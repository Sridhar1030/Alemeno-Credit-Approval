# credit_approval/management/commands/ingest_data.py
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
import math
import uuid
import re

from credit_approval.models import Customer, Loan
from credit_approval.views import calculate_approved_limit, calculate_emi

def clean_column_names(df):
    """
    Cleans column names by converting them to lowercase and replacing
    any non-alphanumeric characters (except underscores) with an empty string.
    This helps in robustly accessing columns regardless of original casing/spacing.
    """
    df.columns = [re.sub(r'[^a-zA-Z0-9_]', '', col.lower().strip().replace(' ', '_')) for col in df.columns]
    return df

class Command(BaseCommand):
    help = 'Ingests customer and loan data from provided XLSX files.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting data ingestion...'))

        # --- Ingest Customer Data ---
        customer_file_path = 'customer_data.xlsx'
        try:
            customer_df = pd.read_excel(customer_file_path)
            customer_df = clean_column_names(customer_df)
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded and cleaned headers for {customer_file_path}'))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Error: {customer_file_path} not found. Make sure it\'s in the same directory as manage.py.'))
            return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error reading customer data Excel file: {e}'))
            return

        self.stdout.write(self.style.SUCCESS('Ingesting customer data...'))
        customers_created = 0
        customer_id_mapping = {} # To map original integer customer IDs to our new UUIDs
        for index, row in customer_df.iterrows():
            try:
                # Use the exact column names after cleaning
                monthly_salary = row['monthly_salary']
                calculated_approved_limit = calculate_approved_limit(monthly_salary)
                original_customer_id = row['customer_id']
                
                # Check if customer with this original_customer_csv_id already exists
                # This ensures idempotency if you run the script multiple times
                customer_exists = Customer.objects.filter(original_customer_csv_id=original_customer_id).exists()

                if customer_exists:
                    customer = Customer.objects.get(original_customer_csv_id=original_customer_id)
                    created = False # Not newly created
                else:
                    customer = Customer.objects.create(
                        original_customer_csv_id=original_customer_id,
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        age=row['age'], # Now 'age' field exists in model
                        phone_number=str(row['phone_number']),
                        monthly_salary=monthly_salary,
                        approved_limit=calculated_approved_limit,
                        current_debt=row.get('current_debt', 0.00)
                    )
                    created = True

                # Store the mapping from original ID to our new UUID for loan ingestion
                customer_id_mapping[original_customer_id] = customer.customer_id
                if created:
                    customers_created += 1
            except KeyError as ke:
                self.stderr.write(self.style.ERROR(f"Missing column in customer data Excel: {ke} at row {index}. Skipping customer."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error ingesting customer row {index}: {e} - Data: {row.to_dict()}'))
        
        self.stdout.write(self.style.SUCCESS(f'Finished ingesting customer data. Created/Updated {customers_created} customers.'))

        # --- Ingest Loan Data ---
        loan_file_path = 'loan_data.xlsx'
        try:
            loan_df = pd.read_excel(loan_file_path)
            loan_df = clean_column_names(loan_df)
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded and cleaned headers for {loan_file_path}'))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Error: {loan_file_path} not found. Make sure it\'s in the same directory as manage.py.'))
            return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error reading loan data Excel file: {e}'))
            return

        self.stdout.write(self.style.SUCCESS('Ingesting loan data...'))
        loans_created = 0
        for index, row in loan_df.iterrows():
            try:
                original_customer_csv_id = row['customer_id']
                customer_uuid = customer_id_mapping.get(original_customer_csv_id)
                
                if not customer_uuid:
                    self.stderr.write(self.style.ERROR(f"Customer with original ID {original_customer_csv_id} not found for loan {row['loan_id']}. Skipping loan."))
                    continue

                customer_obj = Customer.objects.get(customer_id=customer_uuid)
                
                start_date = pd.to_datetime(row['date_of_approval']).date() # Corrected column name
                end_date = pd.to_datetime(row['end_date']).date()

                loan_amount = row['loan_amount']
                interest_rate = row['interest_rate']
                tenure = row['tenure']
                monthly_installment = row['monthly_payment'] # Corrected column name
                emis_paid_on_time = row['emis_paid_on_time']

                # Now, loan_id is an IntegerField and primary_key=True
                # We use get_or_create to handle potential duplicates if the script is run multiple times
                loan, created = Loan.objects.get_or_create(
                    loan_id=row['loan_id'], # Use the integer loan_id directly
                    defaults={
                        'customer': customer_obj,
                        'loan_amount': loan_amount,
                        'tenure': tenure,
                        'interest_rate': interest_rate,
                        'monthly_installment': monthly_installment,
                        'emis_paid_on_time': emis_paid_on_time,
                        'start_date': start_date,
                        'end_date': end_date,
                        'status': 'ACTIVE'
                    }
                )
                
                if created:
                    loans_created += 1
                    with transaction.atomic():
                        customer_obj.current_debt += loan_amount
                        customer_obj.save(update_fields=['current_debt'])
                else:
                    # If the loan already existed, you might want to update its fields
                    # For this assignment, we'll assume get_or_create is sufficient
                    # and won't update existing loans to avoid complexity.
                    pass 

            except KeyError as ke:
                self.stderr.write(self.style.ERROR(f'Missing column in loan data Excel: {ke} at row {index}. Skipping loan.'))
            except ValueError as ve:
                self.stderr.write(self.style.ERROR(f'Data conversion error in loan row {index}: {ve} - Data: {row.to_dict()}. Skipping loan.'))
            except Customer.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Customer not found for loan row {index} (Customer ID: {row.get("customer_id")}). Skipping loan.'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error ingesting loan row {index}: {e} - Data: {row.to_dict()}'))

        self.stdout.write(self.style.SUCCESS(f'Finished ingesting loan data. Created/Updated {loans_created} loans.'))
        self.stdout.write(self.style.SUCCESS('Data ingestion complete.'))
