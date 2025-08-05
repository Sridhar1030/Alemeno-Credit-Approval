# credit_approval/urls.py
from django.urls import path
from .views import (
    RegisterCustomerView, CheckEligibilityView, CreateLoanView,
    ViewLoanView, ViewCustomerLoansView
)

urlpatterns = [
    path('register', RegisterCustomerView.as_view(), name='register_customer'),
    path('check-eligibility', CheckEligibilityView.as_view(), name='check_eligibility'),
    path('create-loan', CreateLoanView.as_view(), name='create_loan'),
    path('view-loan/<int:loan_id>', ViewLoanView.as_view(), name='view_loan'),
    path('view-loans/<uuid:customer_id>', ViewCustomerLoansView.as_view(), name='view_customer_loans'),
]