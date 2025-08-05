# credit_approval/models.py
from django.db import models
from django.core.validators import MinValueValidator
import uuid

class Customer(models.Model):
    # Django's internal primary key (UUID for good practice)
    customer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Field to store the original integer Customer ID from the CSV for mapping
    original_customer_csv_id = models.IntegerField(unique=True, null=True, blank=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField()  # Added 'age' field as per CSV structure
    phone_number = models.CharField(max_length=15, unique=True)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    approved_limit = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    current_debt = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (ID: {self.original_customer_csv_id or self.customer_id})"

    class Meta:
        ordering = ['first_name', 'last_name']

class Loan(models.Model):
    # Changed loan_id to IntegerField and primary_key=True to match CSV structure
    loan_id = models.IntegerField(primary_key=True)
    
    # ForeignKey remains linked to our Customer model's UUID primary key
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='loans')
    
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    tenure = models.IntegerField(validators=[MinValueValidator(1)])
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    monthly_installment = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    emis_paid_on_time = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    start_date = models.DateField()
    end_date = models.DateField()
    
    LOAN_STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ACTIVE', 'Active'),
        ('PAID', 'Paid Off'),
    ]
    status = models.CharField(max_length=10, choices=LOAN_STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Loan {self.loan_id} for {self.customer.first_name} {self.customer.last_name}"

    class Meta:
        ordering = ['-start_date']
