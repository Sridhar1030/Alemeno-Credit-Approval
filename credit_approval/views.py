# credit_approval/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
# Removed NaN and Infinity from direct import, as they are not importable names
from decimal import Decimal, getcontext, ROUND_CEILING, InvalidOperation 
import math
import pandas as pd

from .models import Customer, Loan
from .serializers import (
    RegisterCustomerSerializer,
    RegisterCustomerResponseSerializer,
    CheckEligibilityRequestSerializer,
    CheckEligibilityResponseSerializer,
    CreateLoanRequestSerializer,
    CreateLoanResponseSerializer,
    ViewLoanResponseSerializer,
    ViewCustomerLoansResponseSerializer
)

getcontext().prec = 50 # Set high precision for intermediate Decimal calculations

def calculate_approved_limit(monthly_salary):
    monthly_salary = Decimal(str(monthly_salary))
    raw_limit = Decimal('36') * monthly_salary
    if raw_limit > 0:
        lakhs = (raw_limit / Decimal('100000')).to_integral_value(rounding=ROUND_CEILING)
        return lakhs * Decimal('100000')
    return Decimal('0')

def calculate_emi(principal, annual_interest_rate, tenure_months):
    principal = Decimal(str(principal))
    
    try:
        # Convert annual_interest_rate to Decimal, handling potential non-numeric input
        annual_interest_rate_decimal = Decimal(str(annual_interest_rate))
    except (TypeError, ValueError, InvalidOperation):
        # If conversion fails, treat as 0 interest for calculation purposes
        annual_interest_rate_decimal = Decimal('0') 

    # Defensive check for NaN or Infinity values after conversion
    # These methods are called on the Decimal object, not imported names
    if annual_interest_rate_decimal.is_nan() or annual_interest_rate_decimal.is_infinite():
        # If interest rate is invalid, fall back to simple principal / tenure
        return (principal / Decimal(str(tenure_months))).quantize(Decimal('0.01'))

    if annual_interest_rate_decimal == 0:
        return (principal / Decimal(str(tenure_months))).quantize(Decimal('0.01'))
    
    # Calculate monthly interest rate without immediate quantize on this line
    # Let the global getcontext().prec handle the intermediate precision
    monthly_interest_rate = annual_interest_rate_decimal / Decimal('1200')
    
    try:
        power_term = (Decimal('1') + monthly_interest_rate)**tenure_months
        numerator = principal * monthly_interest_rate * power_term
        denominator = power_term - Decimal('1')
        
        if denominator == 0: # Avoid division by zero
            return (principal / Decimal(str(tenure_months))).quantize(Decimal('0.01'))
        
        emi = numerator / denominator
    except InvalidOperation as e: # Catch InvalidOperation specifically for Decimal arithmetic
        print(f"Decimal InvalidOperation in EMI calculation: {e} for principal={principal}, rate={annual_interest_rate_decimal}, tenure={tenure_months}")
        return (principal / Decimal(str(tenure_months))).quantize(Decimal('0.01'))
    except Exception as e: # Catch any other unexpected errors
        print(f"General error in EMI calculation: {e} for principal={principal}, rate={annual_interest_rate_decimal}, tenure={tenure_months}")
        return (principal / Decimal(str(tenure_months))).quantize(Decimal('0.01'))

    return emi.quantize(Decimal('0.01')) # Quantize the final result to 2 decimal places

def calculate_credit_score(customer_id):
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return 0

    score = 0
    customer_loans = Loan.objects.filter(customer=customer)

    total_emis_paid_on_time = customer_loans.aggregate(Sum('emis_paid_on_time'))['emis_paid_on_time__sum'] or 0
    total_expected_emis = customer_loans.aggregate(Sum('tenure'))['tenure__sum'] or 0
    if total_expected_emis > 0:
        on_time_ratio = Decimal(str(total_emis_paid_on_time)) / Decimal(str(total_expected_emis))
        score += min(50, int(on_time_ratio * 50))

    num_past_loans = customer_loans.count()
    score += min(10, num_past_loans * 2)

    current_year = timezone.now().year
    loans_current_year = customer_loans.filter(start_date__year=current_year).count()
    score += min(20, loans_current_year * 5)

    total_loan_volume = customer_loans.aggregate(Sum('loan_amount'))['loan_amount__sum'] or Decimal('0')
    score += min(10, int(total_loan_volume / Decimal('100000')))

    total_current_active_debt = Loan.objects.filter(
        customer=customer, status__in=['APPROVED', 'ACTIVE']
    ).aggregate(Sum('loan_amount'))['loan_amount__sum'] or Decimal('0')

    if total_current_active_debt > customer.approved_limit:
        return 0

    return max(0, min(100, score))

class RegisterCustomerView(APIView):
    def post(self, request):
        serializer = RegisterCustomerSerializer(data=request.data)
        if serializer.is_valid():
            first_name = serializer.validated_data['first_name']
            last_name = serializer.validated_data['last_name']
            monthly_income = serializer.validated_data['monthly_income']
            phone_number = serializer.validated_data['phone_number']
            age = serializer.validated_data['age']

            if Customer.objects.filter(phone_number=phone_number).exists():
                return Response({"message": "Customer with this phone number already exists."}, status=status.HTTP_409_CONFLICT)

            approved_limit = calculate_approved_limit(monthly_income)
            customer = Customer.objects.create(
                first_name=first_name, last_name=last_name, age=age,
                monthly_salary=monthly_income, phone_number=phone_number, approved_limit=approved_limit
            )

            response_data = {
                "customer_id": customer.customer_id, "name": f"{customer.first_name} {customer.last_name}",
                "age": customer.age, "monthly_income": customer.monthly_salary,
                "approved_limit": customer.approved_limit, "phone_number": customer.phone_number
            }
            response_serializer = RegisterCustomerResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckEligibilityView(APIView):
    def post(self, request):
        serializer = CheckEligibilityRequestSerializer(data=request.data)
        if serializer.is_valid():
            customer_id = serializer.validated_data['customer_id']
            loan_amount = serializer.validated_data['loan_amount']
            interest_rate = serializer.validated_data['interest_rate']
            tenure = serializer.validated_data['tenure']

            try:
                customer = Customer.objects.get(customer_id=customer_id)
            except Customer.DoesNotExist:
                return Response({"message": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

            credit_score = calculate_credit_score(customer_id)
            approval = False
            corrected_interest_rate = interest_rate
            monthly_installment = Decimal('0.00')
            message = None

            prospective_emi = calculate_emi(loan_amount, interest_rate, tenure)

            total_current_active_emis = Loan.objects.filter(
                customer=customer, status='ACTIVE'
            ).aggregate(Sum('monthly_installment'))['monthly_installment__sum'] or Decimal('0.00')

            if total_current_active_emis + prospective_emi > (customer.monthly_salary / Decimal('2')):
                approval = False
                message = "Sum of all current EMIs exceeds 50% of monthly salary."
            else:
                if credit_score > 50:
                    approval = True
                elif 30 < credit_score <= 50:
                    if interest_rate <= Decimal('12'):
                        corrected_interest_rate = Decimal('12.00')
                    approval = True
                elif 10 < credit_score <= 30:
                    if interest_rate <= Decimal('16'):
                        corrected_interest_rate = Decimal('16.00')
                    approval = True
                else:
                    approval = False
                    message = "Credit score too low for loan approval."
                
                if approval:
                    if loan_amount > customer.approved_limit:
                        approval = False
                        message = "Requested loan amount exceeds customer's approved limit."
                    else:
                        monthly_installment = calculate_emi(loan_amount, corrected_interest_rate, tenure)
                        if total_current_active_emis + monthly_installment > (customer.monthly_salary / Decimal('2')):
                            approval = False
                            message = "Sum of all current EMIs exceeds 50% of monthly salary even with corrected rate."
                else:
                    monthly_installment = Decimal('0.00')
            
            response_data = {
                "customer_id": customer_id, "approval": approval,
                "interest_rate": interest_rate, "corrected_interest_rate": corrected_interest_rate,
                "tenure": tenure, "monthly_installment": monthly_installment,
            }
            if not approval:
                response_data['message'] = message or "Loan not approved due to eligibility criteria."
            
            response_serializer = CheckEligibilityResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateLoanView(APIView):
    def post(self, request):
        serializer = CreateLoanRequestSerializer(data=request.data)
        if serializer.is_valid():
            customer_id = serializer.validated_data['customer_id']
            loan_amount = serializer.validated_data['loan_amount']
            interest_rate = serializer.validated_data['interest_rate']
            tenure = serializer.validated_data['tenure']

            try:
                customer = Customer.objects.get(customer_id=customer_id)
            except Customer.DoesNotExist:
                return Response({"message": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

            credit_score = calculate_credit_score(customer_id)
            loan_approved = False
            corrected_interest_rate = interest_rate
            monthly_installment = Decimal('0.00')
            message = None

            prospective_emi = calculate_emi(loan_amount, interest_rate, tenure)
            total_current_active_emis = Loan.objects.filter(
                customer=customer, status='ACTIVE'
            ).aggregate(Sum('monthly_installment'))['monthly_installment__sum'] or Decimal('0.00')
            
            if total_current_active_emis + prospective_emi > (customer.monthly_salary / Decimal('2')):
                loan_approved = False
                message = "Sum of all current EMIs exceeds 50% of monthly salary."
            else:
                if credit_score > 50:
                    loan_approved = True
                elif 30 < credit_score <= 50:
                    if interest_rate <= Decimal('12'):
                        corrected_interest_rate = Decimal('12.00')
                    loan_approved = True
                elif 10 < credit_score <= 30:
                    if interest_rate <= Decimal('16'):
                        corrected_interest_rate = Decimal('16.00')
                    loan_approved = True
                else:
                    loan_approved = False
                    message = "Credit score too low for loan approval."

                if loan_approved:
                    if loan_amount > customer.approved_limit:
                        loan_approved = False
                        message = "Requested loan amount exceeds customer's approved limit."
                    else:
                        monthly_installment = calculate_emi(loan_amount, corrected_interest_rate, tenure)
                        if total_current_active_emis + monthly_installment > (customer.monthly_salary / Decimal('2')):
                            loan_approved = False
                            message = "Sum of all current EMIs exceeds 50% of monthly salary even with corrected rate."
                else:
                    monthly_installment = Decimal('0.00')
            
            loan_id = None
            if loan_approved:
                with transaction.atomic():
                    start_date = timezone.now().date()
                    end_date = start_date + timedelta(days=30 * tenure)
                    loan = Loan.objects.create(
                        customer=customer, loan_amount=loan_amount, tenure=tenure,
                        interest_rate=corrected_interest_rate, monthly_installment=monthly_installment,
                        emis_paid_on_time=0, start_date=start_date, end_date=end_date, status='APPROVED'
                    )
                    loan_id = loan.loan_id
                    customer.current_debt = F('current_debt') + loan_amount
                    customer.save(update_fields=['current_debt'])
                    customer.refresh_from_db()
                message = "Loan approved successfully."
            else:
                message = message or "Loan not approved due to eligibility criteria."

            response_data = {
                "loan_id": loan_id, "customer_id": customer_id,
                "loan_approved": loan_approved, "message": message,
                "monthly_installment": monthly_installment if loan_approved else None
            }
            response_serializer = CreateLoanResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ViewLoanView(APIView):
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.get(loan_id=loan_id)
        except Loan.DoesNotExist:
            return Response({"message": "Loan not found."}, status=status.HTTP_404_NOT_FOUND)

        customer_data = {
            "id": loan.customer.customer_id, "first_name": loan.customer.first_name,
            "last_name": loan.customer.last_name, "phone_number": loan.customer.phone_number,
            "age": loan.customer.age,
        }
        response_data = {
            "loan_id": loan.loan_id, "customer": customer_data,
            "loan_amount": loan.loan_amount, "interest_rate": loan.interest_rate,
            "monthly_installment": loan.monthly_installment, "tenure": loan.tenure,
        }
        response_serializer = ViewLoanResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

class ViewCustomerLoansView(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response({"message": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

        customer_loans = Loan.objects.filter(customer=customer, status__in=['APPROVED', 'ACTIVE']).order_by('-start_date')

        loan_list_data = []
        for loan in customer_loans:
            repayments_left = max(0, loan.tenure - loan.emis_paid_on_time)
            loan_list_data.append({
                "loan_id": loan.loan_id, "loan_amount": loan.loan_amount, "interest_rate": loan.interest_rate,
                "monthly_installment": loan.monthly_installment, "repayments_left": repayments_left,
            })
        response_serializer = ViewCustomerLoansResponseSerializer(loan_list_data, many=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
