# credit_approval/tests.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid

from credit_approval.models import Customer, Loan
from credit_approval.views import calculate_approved_limit, calculate_emi, calculate_credit_score

class HelperFunctionTests(TestCase):
    def test_calculate_approved_limit(self):
        self.assertEqual(calculate_approved_limit(Decimal('10000')), Decimal('400000'))
        self.assertEqual(calculate_approved_limit(Decimal('50000')), Decimal('1800000'))
        self.assertEqual(calculate_approved_limit(Decimal('1')), Decimal('100000'))
        self.assertEqual(calculate_approved_limit(Decimal('99999')), Decimal('3600000'))
        self.assertEqual(calculate_approved_limit(Decimal('0')), Decimal('0'))

    def test_calculate_emi(self):
        self.assertAlmostEqual(calculate_emi(Decimal('100000'), Decimal('10'), 12), Decimal('8791.59'), places=2)
        self.assertAlmostEqual(calculate_emi(Decimal('500000'), Decimal('12'), 60), Decimal('11122.22'), places=2)
        self.assertAlmostEqual(calculate_emi(Decimal('200000'), Decimal('0'), 24), Decimal('8333.33'), places=2)
        self.assertAlmostEqual(calculate_emi(Decimal('1000000'), Decimal('15'), 120), Decimal('16133.50'), places=2)

class CreditScoreCalculationTests(TestCase):
    def setUp(self):
        self.customer1 = Customer.objects.create(
            first_name="Test", last_name="Customer1", age=30, phone_number="1111111111",
            monthly_salary=Decimal('100000.00'), approved_limit=Decimal('3600000.00'), current_debt=Decimal('0.00')
        )
        self.customer2 = Customer.objects.create(
            first_name="Test", last_name="Customer2", age=40, phone_number="2222222222",
            monthly_salary=Decimal('50000.00'), approved_limit=Decimal('1800000.00'), current_debt=Decimal('0.00')
        )

    def test_credit_score_no_loans(self):
        score = calculate_credit_score(self.customer1.customer_id)
        self.assertEqual(score, 0)

    def test_credit_score_with_paid_loans(self):
        Loan.objects.create(
            customer=self.customer1, loan_amount=Decimal('100000'), tenure=12, interest_rate=Decimal('10'),
            monthly_installment=calculate_emi(Decimal('100000'), Decimal('10'), 12), emis_paid_on_time=12,
            start_date=timezone.now().date() - timedelta(days=365*2), end_date=timezone.now().date() - timedelta(days=365) + timedelta(days=30*12), status='PAID'
        )
        Loan.objects.create(
            customer=self.customer1, loan_amount=Decimal('50000'), tenure=6, interest_rate=Decimal('8'),
            monthly_installment=calculate_emi(Decimal('50000'), Decimal('8'), 6), emis_paid_on_time=6,
            start_date=timezone.now().date() - timedelta(days=365), end_date=timezone.now().date() - timedelta(days=365) + timedelta(days=30*6), status='PAID'
        )
        score = calculate_credit_score(self.customer1.customer_id)
        self.assertGreater(score, 0)
        self.assertEqual(score, 55)

    def test_credit_score_exceeds_approved_limit(self):
        self.customer2.current_debt = Decimal('2000000.00')
        self.customer2.save()
        Loan.objects.create(
            customer=self.customer2, loan_amount=Decimal('2000000'), tenure=12, interest_rate=Decimal('10'),
            monthly_installment=calculate_emi(Decimal('2000000'), Decimal('10'), 12), emis_paid_on_time=0,
            start_date=timezone.now().date(), end_date=timezone.now().date() + timedelta(days=30*12), status='ACTIVE'
        )
        score = calculate_credit_score(self.customer2.customer_id)
        self.assertEqual(score, 0)

class APIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer_data = {
            "first_name": "Test", "last_name": "User", "age": 25,
            "monthly_income": Decimal('70000.00'), "phone_number": "9876543210"
        }
        self.customer = Customer.objects.create(
            first_name="Existing", last_name="Customer", age=35, phone_number="1234567890",
            monthly_salary=Decimal('150000.00'), approved_limit=Decimal('5400000.00'), current_debt=Decimal('0.00')
        )
        Loan.objects.create(
            customer=self.customer, loan_amount=Decimal('100000'), tenure=12, interest_rate=Decimal('10'),
            monthly_installment=calculate_emi(Decimal('100000'), Decimal('10'), 12), emis_paid_on_time=12,
            start_date=timezone.now().date() - timedelta(days=365), end_date=timezone.now().date() - timedelta(days=365) + timedelta(days=30*12), status='PAID'
        )


    def test_register_customer(self):
        response = self.client.post(reverse('register_customer'), self.customer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('customer_id', response.data)
        self.assertEqual(response.data['name'], "Test User")
        self.assertEqual(Decimal(str(response.data['approved_limit'])), calculate_approved_limit(self.customer_data['monthly_income']))
        
        duplicate_data = self.customer_data.copy()
        duplicate_data['phone_number'] = "1234567890"
        response = self.client.post(reverse('register_customer'), duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_check_eligibility_approved(self):
        data = {
            "customer_id": self.customer.customer_id, "loan_amount": Decimal('100000.00'),
            "interest_rate": Decimal('10.00'), "tenure": 12
        }
        response = self.client.post(reverse('check_eligibility'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['approval'])
        self.assertEqual(Decimal(str(response.data['corrected_interest_rate'])), Decimal('10.00'))
        self.assertGreater(Decimal(str(response.data['monthly_installment'])), Decimal('0'))

    def test_check_eligibility_rejected_low_credit_score(self):
        low_score_customer = Customer.objects.create(
            first_name="Bad", last_name="Credit", age=30, phone_number="3333333333",
            monthly_salary=Decimal('50000.00'), approved_limit=Decimal('1000000.00'), current_debt=Decimal('0.00')
        )
        low_score_customer.current_debt = Decimal('1500000.00')
        low_score_customer.save()
        Loan.objects.create(
            customer=low_score_customer, loan_amount=Decimal('1500000'), tenure=12, interest_rate=Decimal('10'),
            monthly_installment=calculate_emi(Decimal('1500000'), Decimal('10'), 12), emis_paid_on_time=0,
            start_date=timezone.now().date(), end_date=timezone.now().date() + timedelta(days=30*12), status='ACTIVE'
        )

        data = {
            "customer_id": low_score_customer.customer_id, "loan_amount": Decimal('10000.00'),
            "interest_rate": Decimal('5.00'), "tenure": 12
        }
        response = self.client.post(reverse('check_eligibility'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['approval'])
        self.assertIn('message', response.data)
        self.assertEqual(Decimal(str(response.data['monthly_installment'])), Decimal('0.00'))

    def test_check_eligibility_corrected_interest_rate(self):
        moderate_score_customer = Customer.objects.create(
            first_name="Moderate", last_name="Credit", age=30, phone_number="4444444444",
            monthly_salary=Decimal('100000.00'), approved_limit=Decimal('3600000.00'), current_debt=Decimal('0.00')
        )
        Loan.objects.create(
            customer=moderate_score_customer, loan_amount=Decimal('100000'), tenure=10, interest_rate=Decimal('10'),
            monthly_installment=calculate_emi(Decimal('100000'), Decimal('10'), 10), emis_paid_on_time=5,
            start_date=timezone.now().date() - timedelta(days=100), end_date=timezone.now().date() + timedelta(days=30*10), status='ACTIVE'
        )

        data = {
            "customer_id": moderate_score_customer.customer_id, "loan_amount": Decimal('50000.00'),
            "interest_rate": Decimal('8.00'), "tenure": 12
        }
        response = self.client.post(reverse('check_eligibility'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['approval'])
        self.assertEqual(Decimal(str(response.data['corrected_interest_rate'])), Decimal('12.00'))
        self.assertGreater(Decimal(str(response.data['monthly_installment'])), Decimal('0'))

    def test_create_loan_approved(self):
        data = {
            "customer_id": self.customer.customer_id, "loan_amount": Decimal('200000.00'),
            "interest_rate": Decimal('10.00'), "tenure": 24
        }
        initial_debt = self.customer.current_debt
        response = self.client.post(reverse('create_loan'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['loan_approved'])
        self.assertIsNotNone(response.data['loan_id'])
        self.assertGreater(Decimal(str(response.data['monthly_installment'])), Decimal('0'))
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_debt, initial_debt + Decimal('200000.00'))
        self.assertTrue(Loan.objects.filter(loan_id=response.data['loan_id']).exists())

    def test_create_loan_rejected(self):
        high_emi_customer = Customer.objects.create(
            first_name="High", last_name="EMI", age=30, phone_number="5555555555",
            monthly_salary=Decimal('10000.00'), approved_limit=Decimal('360000.00'), current_debt=Decimal('0.00')
        )
        Loan.objects.create(
            customer=high_emi_customer, loan_amount=Decimal('100000'), tenure=10, interest_rate=Decimal('10'),
            monthly_installment=calculate_emi(Decimal('100000'), Decimal('10'), 10), emis_paid_on_time=0,
            start_date=timezone.now().date(), end_date=timezone.now().date() + timedelta(days=30*10), status='ACTIVE'
        )
        data = {
            "customer_id": high_emi_customer.customer_id, "loan_amount": Decimal('50000.00'),
            "interest_rate": Decimal('10.00'), "tenure": 6
        }
        response = self.client.post(reverse('create_loan'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['loan_approved'])
        self.assertIn('message', response.data)
        self.assertEqual(response.data['monthly_installment'], None)

    def test_view_loan(self):
        loan_obj = Loan.objects.create(
            customer=self.customer, loan_amount=Decimal('50000'), tenure=12, interest_rate=Decimal('10'),
            monthly_installment=calculate_emi(Decimal('50000'), Decimal('10'), 12), emis_paid_on_time=0,
            start_date=timezone.now().date(), end_date=timezone.now().date() + timedelta(days=30*12), status='APPROVED'
        )
        response = self.client.get(reverse('view_loan', args=[loan_obj.loan_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['loan_id'], loan_obj.loan_id)
        # FIX: Convert both to string for robust comparison
        self.assertEqual(str(response.data['customer']['id']), str(self.customer.customer_id))
        self.assertEqual(Decimal(str(response.data['loan_amount'])), loan_obj.loan_amount)

    def test_view_loan_not_found(self):
        response = self.client.get(reverse('view_loan', args=[999999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('message', response.data)

    def test_view_customer_loans(self):
        Loan.objects.create(
            customer=self.customer, loan_amount=Decimal('100000'), tenure=12, interest_rate=Decimal('10'),
            monthly_installment=calculate_emi(Decimal('100000'), Decimal('10'), 12), emis_paid_on_time=6,
            start_date=timezone.now().date() - timedelta(days=180), end_date=timezone.now().date() + timedelta(days=180), status='ACTIVE'
        )
        Loan.objects.create(
            customer=self.customer, loan_amount=Decimal('50000'), tenure=6, interest_rate=Decimal('8'),
            monthly_installment=calculate_emi(Decimal('50000'), Decimal('8'), 6), emis_paid_on_time=3,
            start_date=timezone.now().date() - timedelta(days=90), end_date=timezone.now().date() + timedelta(days=90), status='ACTIVE'
        )
        response = self.client.get(reverse('view_customer_loans', args=[self.customer.customer_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 2)
        
        first_loan_data = response.data[0]
        self.assertIn('loan_id', first_loan_data)
        self.assertIn('loan_amount', first_loan_data)
        self.assertIn('repayments_left', first_loan_data)
    
    def test_view_customer_loans_no_loans(self):
        new_customer = Customer.objects.create(
            first_name="No", last_name="Loans", age=22, phone_number="6666666666",
            monthly_salary=Decimal('40000.00'), approved_limit=Decimal('1440000.00'), current_debt=Decimal('0.00')
        )
        response = self.client.get(reverse('view_customer_loans', args=[new_customer.customer_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
