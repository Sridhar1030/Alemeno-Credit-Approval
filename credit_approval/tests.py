# credit_approval/tests.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid

from credit_approval.models import Customer, Loan
from credit_approval.views import calculate_approved_limit, calculate_emi, calculate_credit_score

class HelperFunctionTests(TestCase):
    def test_calculate_approved_limit(self):
        # Test cases for calculate_approved_limit
        self.assertEqual(calculate_approved_limit(10000), 400000) # 36*10000 = 360000, rounded to 400000
        self.assertEqual(calculate_approved_limit(50000), 1800000) # 36*50000 = 1800000
        self.assertEqual(calculate_approved_limit(1), 100000) # Smallest salary, rounds up to 1 lakh
        self.assertEqual(calculate_approved_limit(99999), 3600000) # 36*99999 = 3599964, rounds to 3600000

    def test_calculate_emi(self):
        # Test cases for calculate_emi
        # Principal, Annual Interest Rate, Tenure (months)
        self.assertAlmostEqual(calculate_emi(100000, 10, 12), 8791.59, places=2)
        self.assertAlmostEqual(calculate_emi(500000, 12, 60), 11122.22, places=2)
        self.assertAlmostEqual(calculate_emi(200000, 0, 24), 8333.33, places=2) # Zero interest rate
        self.assertAlmostEqual(calculate_emi(1000000, 15, 120), 16133.58, places=2)

class CreditScoreCalculationTests(TestCase):
    def setUp(self):
        # Create a test customer
        self.customer1 = Customer.objects.create(
            first_name="Test",
            last_name="Customer1",
            age=30,
            phone_number="1111111111",
            monthly_salary=Decimal('100000.00'),
            approved_limit=Decimal('3600000.00'),
            current_debt=Decimal('0.00')
        )
        self.customer2 = Customer.objects.create(
            first_name="Test",
            last_name="Customer2",
            age=40,
            phone_number="2222222222",
            monthly_salary=Decimal('50000.00'),
            approved_limit=Decimal('1800000.00'),
            current_debt=Decimal('0.00')
        )

    def test_credit_score_no_loans(self):
        score = calculate_credit_score(self.customer1.customer_id)
        self.assertEqual(score, 0) # Should be 0 initially with no loans

    def test_credit_score_with_paid_loans(self):
        # Create some past loans for customer1
        Loan.objects.create(
            loan_id=1, customer=self.customer1, loan_amount=Decimal('100000'), tenure=12,
            interest_rate=10, monthly_installment=calculate_emi(Decimal('100000'), 10, 12),
            emis_paid_on_time=12, start_date=timezone.now().date() - timedelta(days=365*2),
            end_date=timezone.now().date() - timedelta(days=365) + timedelta(days=30*12), status='PAID'
        )
        Loan.objects.create(
            loan_id=2, customer=self.customer1, loan_amount=Decimal('50000'), tenure=6,
            interest_rate=8, monthly_installment=calculate_emi(Decimal('50000'), 8, 6),
            emis_paid_on_time=6, start_date=timezone.now().date() - timedelta(days=365),
            end_date=timezone.now().date() - timedelta(days=365) + timedelta(days=30*6), status='PAID'
        )
        score = calculate_credit_score(self.customer1.customer_id)
        # Expected score:
        # Past Loans paid on time: (12/12 + 6/6) -> 100% on time, so 50 points
        # No of loans taken: 2 loans -> 4 points (2*2)
        # Loan activity current year: 0 (loans are old)
        # Loan approved volume: (100000+50000)/100000 = 1.5 -> 1 point (int(1.5))
        # Total: 50 + 4 + 0 + 1 = 55
        self.assertGreater(score, 0) # Should be positive now
        self.assertEqual(score, 55) # Based on simplified scoring

    def test_credit_score_exceeds_approved_limit(self):
        # Customer2 has approved_limit of 1800000
        # Create a loan that makes current_debt exceed approved_limit
        self.customer2.current_debt = Decimal('2000000.00') # Manually set debt for testing
        self.customer2.save()
        # Create an active loan to reflect this debt
        Loan.objects.create(
            loan_id=3, customer=self.customer2, loan_amount=Decimal('2000000'), tenure=12,
            interest_rate=10, monthly_installment=calculate_emi(Decimal('2000000'), 10, 12),
            emis_paid_on_time=0, start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30*12), status='ACTIVE'
        )
        score = calculate_credit_score(self.customer2.customer_id)
        self.assertEqual(score, 0) # Should be 0 due to exceeding approved limit

class APIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer_data = {
            "first_name": "Test",
            "last_name": "User",
            "age": 25,
            "monthly_income": 70000.00,
            "phone_number": "9876543210"
        }
        self.customer = Customer.objects.create(
            first_name="Existing",
            last_name="Customer",
            age=35,
            phone_number="1234567890",
            monthly_salary=Decimal('150000.00'),
            approved_limit=Decimal('5400000.00'),
            current_debt=Decimal('0.00')
        )
        # Create a dummy loan for the existing customer to influence credit score
        Loan.objects.create(
            loan_id=100, customer=self.customer, loan_amount=Decimal('100000'), tenure=12,
            interest_rate=10, monthly_installment=calculate_emi(Decimal('100000'), 10, 12),
            emis_paid_on_time=12, start_date=timezone.now().date() - timedelta(days=365),
            end_date=timezone.now().date() - timedelta(days=365) + timedelta(days=30*12), status='PAID'
        )


    def test_register_customer(self):
        response = self.client.post(reverse('register_customer'), self.customer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('customer_id', response.data)
        self.assertEqual(response.data['name'], "Test User")
        self.assertEqual(response.data['approved_limit'], 36 * 70000) # Should be 2520000, rounded to 2500000 or 2600000 based on rounding logic.
        # Check actual rounding logic
        self.assertEqual(response.data['approved_limit'], calculate_approved_limit(self.customer_data['monthly_income']))

        # Test duplicate phone number
        response = self.client.post(reverse('register_customer'), self.customer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


    def test_check_eligibility_approved(self):
        # Assuming existing customer has good credit score
        data = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 100000.00,
            "interest_rate": 10.00,
            "tenure": 12
        }
        response = self.client.post(reverse('check_eligibility'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['approval'])
        self.assertEqual(response.data['corrected_interest_rate'], 10.00)
        self.assertGreater(response.data['monthly_installment'], 0)

    def test_check_eligibility_rejected_low_credit_score(self):
        # Create a customer with a very low credit score (e.g., high debt)
        low_score_customer = Customer.objects.create(
            first_name="Bad",
            last_name="Credit",
            age=30,
            phone_number="3333333333",
            monthly_salary=Decimal('50000.00'),
            approved_limit=Decimal('1000000.00'),
            current_debt=Decimal('1500000.00') # Exceeds approved limit
        )
        Loan.objects.create(
            loan_id=101, customer=low_score_customer, loan_amount=Decimal('1500000'), tenure=12,
            interest_rate=10, monthly_installment=calculate_emi(Decimal('1500000'), 10, 12),
            emis_paid_on_time=0, start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30*12), status='ACTIVE'
        )

        data = {
            "customer_id": low_score_customer.customer_id,
            "loan_amount": 10000.00,
            "interest_rate": 5.00,
            "tenure": 12
        }
        response = self.client.post(reverse('check_eligibility'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['approval'])
        self.assertIn('message', response.data)
        self.assertEqual(response.data['monthly_installment'], 0.0)

    def test_check_eligibility_corrected_interest_rate(self):
        # Customer with moderate credit score (e.g., 30 < score <= 50)
        # Create a customer with a specific credit score range
        moderate_score_customer = Customer.objects.create(
            first_name="Moderate",
            last_name="Credit",
            age=30,
            phone_number="4444444444",
            monthly_salary=Decimal('100000.00'),
            approved_limit=Decimal('3600000.00'),
            current_debt=Decimal('0.00')
        )
        # Add a loan that gives a score in the 30-50 range (e.g., 1 loan, 50% on time)
        Loan.objects.create(
            loan_id=102, customer=moderate_score_customer, loan_amount=Decimal('100000'), tenure=10,
            interest_rate=10, monthly_installment=calculate_emi(Decimal('100000'), 10, 10),
            emis_paid_on_time=5, start_date=timezone.now().date() - timedelta(days=100),
            end_date=timezone.now().date() + timedelta(days=30*10), status='ACTIVE'
        )

        data = {
            "customer_id": moderate_score_customer.customer_id,
            "loan_amount": 50000.00,
            "interest_rate": 8.00, # Requested rate is too low for this slab
            "tenure": 12
        }
        response = self.client.post(reverse('check_eligibility'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['approval'])
        self.assertEqual(response.data['corrected_interest_rate'], 12.00) # Should be corrected to 12%
        self.assertGreater(response.data['monthly_installment'], 0)

    def test_create_loan_approved(self):
        # Use the existing customer with good credit
        data = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 200000.00,
            "interest_rate": 10.00,
            "tenure": 24
        }
        initial_debt = self.customer.current_debt
        response = self.client.post(reverse('create_loan'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['loan_approved'])
        self.assertIsNotNone(response.data['loan_id'])
        self.assertGreater(response.data['monthly_installment'], 0)
        
        # Verify customer debt updated
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_debt, initial_debt + Decimal('200000.00'))
        # Verify loan exists in DB
        self.assertTrue(Loan.objects.filter(loan_id=response.data['loan_id']).exists())


    def test_create_loan_rejected(self):
        # Create a customer who will be rejected (e.g., high current EMIs)
        high_emi_customer = Customer.objects.create(
            first_name="High",
            last_name="EMI",
            age=30,
            phone_number="5555555555",
            monthly_salary=Decimal('10000.00'), # Low salary
            approved_limit=Decimal('360000.00'),
            current_debt=Decimal('0.00')
        )
        # Add an active loan that pushes EMIs over 50%
        Loan.objects.create(
            loan_id=103, customer=high_emi_customer, loan_amount=Decimal('100000'), tenure=10,
            interest_rate=10, monthly_installment=calculate_emi(Decimal('100000'), 10, 10), # EMI approx 10500
            emis_paid_on_time=0, start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30*10), status='ACTIVE'
        )
        # Now try to create another loan
        data = {
            "customer_id": high_emi_customer.customer_id,
            "loan_amount": 50000.00,
            "interest_rate": 10.00,
            "tenure": 6
        }
        response = self.client.post(reverse('create_loan'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['loan_approved'])
        self.assertIn('message', response.data)
        self.assertEqual(response.data['monthly_installment'], None) # No installment if not approved

    def test_view_loan(self):
        # Create a loan to view
        loan_obj = Loan.objects.create(
            loan_id=200, customer=self.customer, loan_amount=Decimal('50000'), tenure=12,
            interest_rate=10, monthly_installment=calculate_emi(Decimal('50000'), 10, 12),
            emis_paid_on_time=0, start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30*12), status='APPROVED'
        )
        response = self.client.get(reverse('view_loan', args=[loan_obj.loan_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['loan_id'], loan_obj.loan_id)
        self.assertEqual(response.data['customer']['id'], str(self.customer.customer_id)) # UUID is stringified
        self.assertEqual(response.data['loan_amount'], float(loan_obj.loan_amount))

    def test_view_loan_not_found(self):
        response = self.client.get(reverse('view_loan', args=[999999])) # Non-existent loan ID
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('message', response.data)

    def test_view_customer_loans(self):
        # Create multiple loans for the customer
        Loan.objects.create(
            loan_id=300, customer=self.customer, loan_amount=Decimal('100000'), tenure=12,
            interest_rate=10, monthly_installment=calculate_emi(Decimal('100000'), 10, 12),
            emis_paid_on_time=6, start_date=timezone.now().date() - timedelta(days=180),
            end_date=timezone.now().date() + timedelta(days=180), status='ACTIVE'
        )
        Loan.objects.create(
            loan_id=301, customer=self.customer, loan_amount=Decimal('50000'), tenure=6,
            interest_rate=8, monthly_installment=calculate_emi(Decimal('50000'), 8, 6),
            emis_paid_on_time=3, start_date=timezone.now().date() - timedelta(days=90),
            end_date=timezone.now().date() + timedelta(days=90), status='ACTIVE'
        )
        response = self.client.get(reverse('view_customer_loans', args=[self.customer.customer_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 2) # At least two active loans, plus any from setup

        # Check structure of one loan item
        first_loan_data = response.data[0]
        self.assertIn('loan_id', first_loan_data)
        self.assertIn('loan_amount', first_loan_data)
        self.assertIn('repayments_left', first_loan_data)

    def test_view_customer_loans_no_loans(self):
        # Create a new customer with no loans
        new_customer = Customer.objects.create(
            first_name="No",
            last_name="Loans",
            age=22,
            phone_number="6666666666",
            monthly_salary=Decimal('40000.00'),
            approved_limit=Decimal('1440000.00'),
            current_debt=Decimal('0.00')
        )
        response = self.client.get(reverse('view_customer_loans', args=[new_customer.customer_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0) # Should return an empty list
