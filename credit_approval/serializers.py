# credit_approval/serializers.py
from rest_framework import serializers
from .models import Customer, Loan

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__' # Include all fields for simplicity, can be customized later

class RegisterCustomerSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField(min_value=0)
    monthly_income = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    phone_number = serializers.CharField(max_length=15)

class RegisterCustomerResponseSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    name = serializers.CharField(max_length=200) # Combined first_name and last_name
    age = serializers.IntegerField()
    monthly_income = serializers.DecimalField(max_digits=10, decimal_places=2)
    approved_limit = serializers.DecimalField(max_digits=12, decimal_places=2)
    phone_number = serializers.CharField(max_length=15)

class CheckEligibilityRequestSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0)
    tenure = serializers.IntegerField(min_value=1)

class CheckEligibilityResponseSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    approval = serializers.BooleanField()
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    corrected_interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()
    monthly_installment = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True) # Allow null for rejected loans
    message = serializers.CharField(allow_null=True, required=False) # Added message field

class CreateLoanRequestSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0)
    tenure = serializers.IntegerField(min_value=1)

class CreateLoanResponseSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField(allow_null=True) # Changed to IntegerField
    customer_id = serializers.UUIDField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField(allow_null=True, required=False)
    monthly_installment = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)

class ViewLoanResponseSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField() # Changed to IntegerField
    customer = serializers.JSONField() # Will contain customer details as a JSON object
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    monthly_installment = serializers.DecimalField(max_digits=12, decimal_places=2)
    tenure = serializers.IntegerField()

class ViewCustomerLoansResponseSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField() # Changed to IntegerField
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    monthly_installment = serializers.DecimalField(max_digits=12, decimal_places=2)
    repayments_left = serializers.IntegerField()
