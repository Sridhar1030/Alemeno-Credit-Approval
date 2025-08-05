# credit_approval/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta, datetime # Import datetime for date parsing if needed
from decimal import Decimal # Import Decimal for precise calculations


from .models import Customer, Loan
from .serializers import (
    RegisterCustomerSerializer, RegisterCustomerResponseSerializer,
    CheckEligibilityRequestSerializer, CheckEligibilityResponseSerializer,
    CreateLoanRequestSerializer, CreateLoanResponseSerializer,
    ViewLoanResponseSerializer, ViewCustomerLoansResponseSerializer
)
import math
import pandas as pd # Used for initial data ingestion, not directly in API views

# --- Helper Functions ---

def calculate_approved_limit(monthly_salary):
    """
    Calculates the approved limit based on monthly salary,
    rounded to the nearest lakh (100,000).
    """
    raw_limit = 36 * monthly_salary
    # Round to nearest lakh
    return math.ceil(raw_limit / 100000) * 100000

def calculate_emi(principal, annual_interest_rate, tenure_months):
    """
    Calculates the Equated Monthly Installment (EMI) using the compound interest formula.
    EMI = P * R * (1 + R)^N / ((1 + R)^N - 1)
    Where:
    P = Principal loan amount (Decimal)
    R = Monthly interest rate (Decimal)
    N = Loan tenure in months (int)
    """
    # Ensure principal is a Decimal
    principal = Decimal(str(principal))

    # Convert annual_interest_rate to Decimal for consistent calculations
    annual_interest_rate_decimal = Decimal(str(annual_interest_rate))

    if annual_interest_rate_decimal == 0:
        # Handle zero interest rate case with Decimal division
        return round(principal / Decimal(str(tenure_months)), 2)
    
    # Calculate monthly interest rate as a Decimal
    monthly_interest_rate = (annual_interest_rate_decimal / Decimal('12')) / Decimal('100')
    
    # Perform calculations using Decimal types
    try:
        # (1 + R)^N
        power_term = (Decimal('1') + monthly_interest_rate)**tenure_months
        
        # P * R * (1 + R)^N
        numerator = principal * monthly_interest_rate * power_term
        
        # ((1 + R)^N - 1)
        denominator = power_term - Decimal('1')

        if denominator == 0: # Avoid division by zero for very small rates/large tenures
            return round(principal / Decimal(str(tenure_months)), 2)

        emi = numerator / denominator
    except Exception as e:
        # Fallback for unexpected calculation errors, though less likely with Decimal
        print(f"Error in EMI calculation: {e}")
        return round(principal / Decimal(str(tenure_months)), 2)

    return round(emi, 2)

def calculate_credit_score(customer_id):
    """
    Calculates the credit score for a customer based on historical loan data.
    Score is out of 100.
    """
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return 0 # Customer not found

    score = 0
    customer_loans = Loan.objects.filter(customer=customer)

    # 1. Past Loans paid on time
    total_emis_paid_on_time = customer_loans.aggregate(Sum('emis_paid_on_time'))['emis_paid_on_time__sum'] or 0
    # Sum of tenure for all loans, representing total expected EMIs
    total_expected_emis = customer_loans.aggregate(Sum('tenure'))['tenure__sum'] or 0

    if total_expected_emis > 0:
        on_time_ratio = total_emis_paid_on_time / total_expected_emis
        score += min(50, int(on_time_ratio * 50))

    # 2. No of loans taken in past
    num_past_loans = customer_loans.count()
    score += min(10, num_past_loans * 2)

    # 3. Loan activity in current year
    current_year = timezone.now().year
    loans_current_year = customer_loans.filter(start_date__year=current_year).count()
    score += min(20, loans_current_year * 5)

    # 4. Loan approved volume
    total_loan_volume = customer_loans.aggregate(Sum('loan_amount'))['loan_amount__sum'] or 0
    score += min(10, int(total_loan_volume / 100000))

    # 5. If sum of current loans of customer > approved limit of customer, credit score = 0
    total_current_active_debt = Loan.objects.filter(
        customer=customer,
        status__in=['APPROVED', 'ACTIVE'] # Consider loans that are approved or active
    ).aggregate(Sum('loan_amount'))['loan_amount__sum'] or 0

    if total_current_active_debt > customer.approved_limit:
        return 0

    return max(0, min(100, score))


# --- API Views ---

class RegisterCustomerView(APIView):
    def post(self, request):
        serializer = RegisterCustomerSerializer(data=request.data)
        if serializer.is_valid():
            first_name = serializer.validated_data['first_name']
            last_name = serializer.validated_data['last_name']
            monthly_income = serializer.validated_data['monthly_income']
            phone_number = serializer.validated_data['phone_number']
            age = serializer.validated_data['age']

            # Check if customer with this phone number already exists
            if Customer.objects.filter(phone_number=phone_number).exists():
                return Response(
                    {"message": "Customer with this phone number already exists."},
                    status=status.HTTP_409_CONFLICT
                )

            approved_limit = calculate_approved_limit(monthly_income)

            customer = Customer.objects.create(
                first_name=first_name,
                last_name=last_name,
                age=age,
                monthly_salary=monthly_income,
                phone_number=phone_number,
                approved_limit=approved_limit
            )

            response_data = {
                "customer_id": customer.customer_id,
                "name": f"{customer.first_name} {customer.last_name}",
                "age": customer.age,
                "monthly_income": customer.monthly_salary,
                "approved_limit": customer.approved_limit,
                "phone_number": customer.phone_number
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
                return Response(
                    {"message": "Customer not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            credit_score = calculate_credit_score(customer_id)
            approval = False
            corrected_interest_rate = interest_rate
            monthly_installment = 0.0
            message = None

            # Calculate EMI for the *new* loan to check against monthly salary limit
            prospective_emi = calculate_emi(loan_amount, interest_rate, tenure)

            # Check if sum of all current EMIs + prospective EMI > 50% of monthly salary
            total_current_active_emis = Loan.objects.filter(
                customer=customer,
                status='ACTIVE' # Only consider active loans for EMI check
            ).aggregate(Sum('monthly_installment'))['monthly_installment__sum'] or 0

            if total_current_active_emis + prospective_emi > (customer.monthly_salary / 2):
                approval = False
                message = "Sum of all current EMIs exceeds 50% of monthly salary."
            else:
                # Determine approval and correct interest rate based on credit score
                if credit_score > 50:
                    approval = True
                elif 30 < credit_score <= 50:
                    if interest_rate <= 12:
                        corrected_interest_rate = 12.0
                    approval = True
                elif 10 < credit_score <= 30:
                    if interest_rate <= 16:
                        corrected_interest_rate = 16.0
                    approval = True
                else: # credit_score <= 10
                    approval = False
                    message = "Credit score too low for loan approval."

                if approval:
                    # If loan amount exceeds approved limit, it cannot be approved
                    if loan_amount > customer.approved_limit:
                        approval = False
                        message = "Requested loan amount exceeds customer's approved limit."
                    else:
                        # Calculate monthly installment with the potentially corrected interest rate
                        monthly_installment = calculate_emi(loan_amount, corrected_interest_rate, tenure)
                        # Re-check EMI condition with corrected interest rate (important!)
                        if total_current_active_emis + monthly_installment > (customer.monthly_salary / 2):
                            approval = False
                            message = "Sum of all current EMIs exceeds 50% of monthly salary even with corrected rate."
                else:
                    monthly_installment = 0.0 # No installment if not approved

            response_data = {
                "customer_id": customer_id,
                "approval": approval,
                "interest_rate": interest_rate, # Requested interest rate
                "corrected_interest_rate": corrected_interest_rate, # Potentially corrected rate
                "tenure": tenure,
                "monthly_installment": monthly_installment,
            }
            if not approval and message: # Only add message if loan is not approved and message exists
                response_data['message'] = message

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
                return Response(
                    {"message": "Customer not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # --- Directly perform eligibility check logic here ---
            credit_score = calculate_credit_score(customer_id)
            loan_approved = False
            corrected_interest_rate = interest_rate
            monthly_installment = 0.0
            message = None

            # Calculate EMI for the *new* loan to check against monthly salary limit
            prospective_emi = calculate_emi(loan_amount, interest_rate, tenure)

            total_current_active_emis = Loan.objects.filter(
                customer=customer,
                status='ACTIVE'
            ).aggregate(Sum('monthly_installment'))['monthly_installment__sum'] or 0

            if total_current_active_emis + prospective_emi > (customer.monthly_salary / 2):
                loan_approved = False
                message = "Sum of all current EMIs exceeds 50% of monthly salary."
            else:
                if credit_score > 50:
                    loan_approved = True
                elif 30 < credit_score <= 50:
                    if interest_rate <= 12:
                        corrected_interest_rate = 12.0
                    loan_approved = True
                elif 10 < credit_score <= 30:
                    if interest_rate <= 16:
                        corrected_interest_rate = 16.0
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
                        if total_current_active_emis + monthly_installment > (customer.monthly_salary / 2):
                            loan_approved = False
                            message = "Sum of all current EMIs exceeds 50% of monthly salary even with corrected rate."
                else:
                    monthly_installment = 0.0 # No installment if not approved


            loan_id = None
            if loan_approved:
                with transaction.atomic():
                    start_date = timezone.now().date()
                    # Approximate end date based on tenure
                    end_date = start_date + timedelta(days=30 * tenure) 

                    loan = Loan.objects.create(
                        customer=customer,
                        loan_amount=loan_amount,
                        tenure=tenure,
                        interest_rate=corrected_interest_rate,
                        monthly_installment=monthly_installment,
                        emis_paid_on_time=0, # New loans start with 0 EMIs paid on time
                        start_date=start_date,
                        end_date=end_date,
                        status='APPROVED'
                    )
                    loan_id = loan.loan_id

                    # Update customer's current_debt
                    customer.current_debt = F('current_debt') + loan_amount
                    customer.save(update_fields=['current_debt'])
                    customer.refresh_from_db() # Reload customer instance with updated debt

                message = "Loan approved successfully."
            else:
                message = message or "Loan not approved due to eligibility criteria."


            response_data = {
                "loan_id": loan_id,
                "customer_id": customer_id,
                "loan_approved": loan_approved,
                "message": message,
                "monthly_installment": monthly_installment if loan_approved else None
            }
            response_serializer = CreateLoanResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ViewLoanView(APIView):
    def get(self, request, loan_id): # loan_id is now an int
        try:
            loan = Loan.objects.get(loan_id=loan_id)
        except Loan.DoesNotExist:
            return Response(
                {"message": "Loan not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        customer_data = {
            "id": loan.customer.customer_id, # This is the UUID
            "first_name": loan.customer.first_name,
            "last_name": loan.customer.last_name,
            "phone_number": loan.customer.phone_number,
            "age": loan.customer.age,
        }

        response_data = {
            "loan_id": loan.loan_id,
            "customer": customer_data,
            "loan_amount": loan.loan_amount,
            "interest_rate": loan.interest_rate,
            "monthly_installment": loan.monthly_installment,
            "tenure": loan.tenure,
        }
        response_serializer = ViewLoanResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ViewCustomerLoansView(APIView):
    def get(self, request, customer_id): # customer_id is still a UUID
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {"message": "Customer not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        customer_loans = Loan.objects.filter(
            customer=customer,
            status__in=['APPROVED', 'ACTIVE']
        ).order_by('-start_date')

        loan_list_data = []
        for loan in customer_loans:
            repayments_left = max(0, loan.tenure - loan.emis_paid_on_time)

            loan_list_data.append({
                "loan_id": loan.loan_id,
                "loan_amount": loan.loan_amount,
                "interest_rate": loan.interest_rate,
                "monthly_installment": loan.monthly_installment,
                "repayments_left": repayments_left,
            })

        response_serializer = ViewCustomerLoansResponseSerializer(loan_list_data, many=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
