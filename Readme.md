Credit Approval System - Backend
This project implements a backend credit approval system as an assignment for Alemeno. It's built using Python with Django and Django REST Framework, dockerized with a PostgreSQL database, and includes unit tests for core functionalities and API endpoints.

Table of Contents
Features

Technologies Used

Project Structure

Setup and Installation

Prerequisites

Cloning the Repository

Running with Docker Compose

Database Migrations

Initial Data Ingestion

API Endpoints

POST /api/register

POST /api/check-eligibility

POST /api/create-loan

GET /api/view-loan/<loan_id>

GET /api/view-loans/<customer_id>

Running Unit Tests

General Guidelines & Notes

Contact

Features
Customer Registration: Register new customers with automatic credit limit calculation.

Loan Eligibility Check: Determine loan eligibility based on a dynamic credit score calculated from historical data and current financial standing.

Loan Creation: Process new loan applications, updating customer debt upon approval.

Loan Details View: Retrieve detailed information for a specific loan.

Customer Loan History: View all current loan details for a given customer.

Data Ingestion: Automated ingestion of initial customer and loan data from provided Excel files.

Dockerized Environment: Easily deployable and scalable using Docker and Docker Compose.

PostgreSQL Database: Robust and reliable data storage.

Unit Tests: Comprehensive test suite for core logic and API endpoints.

Technologies Used
Python: 3.11

Django: 4.x

Django REST Framework: For building robust APIs.

PostgreSQL: Relational database.

Docker & Docker Compose: For containerization and orchestration.

Pandas & Openpyxl: For data ingestion from Excel files.

dj-database-url: For simplified database configuration.

Project Structure
.
├── core/                        # Main Django project settings
├── credit_approval/             # Django app for credit approval logic
│   ├── migrations/              # Database migration files
│   ├── management/              # Custom Django management commands (e.g., ingest_data)
│   ├── models.py                # Database models (Customer, Loan)
│   ├── serializers.py           # Django REST Framework serializers
│   ├── tests.py                 # Unit tests for the application
│   ├── urls.py                  # API endpoint URL routing
│   └── views.py                 # API view logic
├── customer_data.xlsx           # Provided customer data
├── loan_data.xlsx               # Provided loan data
├── Dockerfile                   # Docker build instructions for the Django app
├── docker-compose.yml           # Docker Compose configuration for services
├── manage.py                    # Django management utility
└── requirements.txt             # Python dependencies
└── README.md                    # This file

Setup and Installation
Prerequisites
Docker Desktop: Ensure Docker Desktop (or Docker Engine) is installed and running on your machine.

Download Docker Desktop

Cloning the Repository
First, clone this repository to your local machine:

git clone <your-github-repo-url>
cd credit_approval_system # Or whatever your repo folder is named

Running with Docker Compose
This command will build your Django application image, pull the PostgreSQL image, and start both services.

docker-compose up --build

This process might take a few minutes on the first run as it downloads images and builds your application. Once complete, you should see logs indicating that the PostgreSQL database is ready and the Django development server has started (e.g., "Starting development server at http://0.0.0.0:8000/").

Keep this terminal window open and running.

Database Migrations
After the containers are up, you need to apply the database migrations to your new PostgreSQL database. Open a new terminal window, navigate to your project root, and run:

docker-compose exec web python manage.py makemigrations credit_approval
docker-compose exec web python manage.py migrate

Initial Data Ingestion
Once migrations are applied, ingest the provided customer and loan data into the database. In the same new terminal window:

docker-compose exec web python manage.py ingest_data

API Endpoints
The API endpoints are accessible via http://127.0.0.1:8000/api/. You can use curl (from a new terminal window with Docker Compose running) or a tool like Postman/Insomnia to test them.

How to get sample customer_id and loan_id for testing:

After data ingestion, you can get valid IDs from the database using the Django shell:

# Open a new terminal window and navigate to your project root
docker-compose exec web python manage.py shell

# Inside the Django shell:
from credit_approval.models import Customer, Loan
customer = Customer.objects.first()
print(customer.customer_id) # Copy this UUID for customer_id
loan = Loan.objects.filter(customer=customer).first()
if loan:
    print(loan.loan_id) # Copy this integer for loan_id
else:
    print("No loans found for this customer yet.")
exit()

POST /api/register
Registers a new customer and calculates their approved_limit.

Request Method: POST

Request URL: http://127.0.0.1:8000/api/register

Request Body (JSON):

{
    "first_name": "Alice",
    "last_name": "Johnson",
    "age": 28,
    "monthly_income": 80000.00,
    "phone_number": "9911223344"
}

Response Body (JSON - 201 Created):

{
    "customer_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "name": "Alice Johnson",
    "age": 28,
    "monthly_income": "80000.00",
    "approved_limit": "2900000.00",
    "phone_number": "9911223344"
}

Example curl command:

curl -X POST http://127.0.0.1:8000/api/register \
-H "Content-Type: application/json" \
-d '{
    "first_name": "Alice",
    "last_name": "Johnson",
    "age": 28,
    "monthly_income": 80000,
    "phone_number": "9911223344"
}'

POST /api/check-eligibility
Checks loan eligibility based on credit score and other financial rules.

Request Method: POST

Request URL: http://127.0.0.1:8000/api/check-eligibility

Request Body (JSON):

{
    "customer_id": "PASTE_YOUR_CUSTOMER_UUID_HERE",
    "loan_amount": 500000.00,
    "interest_rate": 10.00,
    "tenure": 24
}

Response Body (JSON - 200 OK):

{
    "customer_id": "PASTE_YOUR_CUSTOMER_UUID_HERE",
    "approval": true,
    "interest_rate": "10.00",
    "corrected_interest_rate": "10.00",
    "tenure": 24,
    "monthly_installment": "23265.46",
    "message": "Loan approved." # Message only present if not approved, or for success on create-loan
}

Example curl command:

curl -X POST http://127.0.0.1:8000/api/check-eligibility \
-H "Content-Type: application/json" \
-d '{
    "customer_id": "PASTE_YOUR_CUSTOMER_UUID_HERE",
    "loan_amount": 500000,
    "interest_rate": 10.00,
    "tenure": 24
}'

POST /api/create-loan
Processes a new loan application based on eligibility.

Request Method: POST

Request URL: http://127.0.0.1:8000/api/create-loan

Request Body (JSON):

{
    "customer_id": "PASTE_YOUR_CUSTOMER_UUID_HERE",
    "loan_amount": 200000.00,
    "interest_rate": 13.00,
    "tenure": 18
}

Response Body (JSON - 200 OK):

{
    "loan_id": 12345, # Auto-generated integer ID
    "customer_id": "PASTE_YOUR_CUSTOMER_UUID_HERE",
    "loan_approved": true,
    "message": "Loan approved successfully.",
    "monthly_installment": "12345.67"
}

Example curl command:

curl -X POST http://127.0.0.1:8000/api/create-loan \
-H "Content-Type: application/json" \
-d '{
    "customer_id": "PASTE_YOUR_CUSTOMER_UUID_HERE",
    "loan_amount": 200000,
    "interest_rate": 13.00,
    "tenure": 18
}'

GET /api/view-loan/<loan_id>
Retrieves detailed information for a specific loan and its associated customer.

Request Method: GET

Request URL: http://127.0.0.1:8000/api/view-loan/PASTE_YOUR_LOAN_ID_HERE

Response Body (JSON - 200 OK):

{
    "loan_id": 12345,
    "customer": {
        "id": "PASTE_YOUR_CUSTOMER_UUID_HERE",
        "first_name": "Alice",
        "last_name": "Johnson",
        "phone_number": "9911223344",
        "age": 28
    },
    "loan_amount": "200000.00",
    "interest_rate": "13.00",
    "monthly_installment": "12345.67",
    "tenure": 18
}

Example curl command:

curl -X GET http://127.0.0.1:8000/api/view-loan/PASTE_YOUR_LOAN_ID_HERE

GET /api/view-loans/<customer_id>
Retrieves all current loan details for a given customer.

Request Method: GET

Request URL: http://127.0.0.1:8000/api/view-loans/PASTE_YOUR_CUSTOMER_UUID_HERE

Response Body (JSON - 200 OK):

[
    {
        "loan_id": 12345,
        "loan_amount": "200000.00",
        "interest_rate": "13.00",
        "monthly_installment": "12345.67",
        "repayments_left": 18
    },
    {
        "loan_id": 67890,
        "loan_amount": "50000.00",
        "interest_rate": "10.00",
        "monthly_installment": "2345.67",
        "repayments_left": 6
    }
]

Example curl command:

curl -X GET http://127.0.0.1:8000/api/view-loans/PASTE_YOUR_CUSTOMER_UUID_HERE

Running Unit Tests
To run the comprehensive suite of unit tests for the application:

Ensure your Docker Compose services are running (docker-compose up).

Open a new terminal window in your project root.

Execute the tests inside the web container:

docker-compose exec web python manage.py test credit_approval

All tests should pass.

General Guidelines & Notes
Code Quality: The codebase emphasizes clear organization, separation of concerns (models, serializers, views), and adherence to Django/DRF best practices.

Error Handling: API endpoints include appropriate error handling and HTTP status codes for various scenarios (e.g., customer not found, invalid input, duplicate phone numbers).

Credit Score Logic: The credit score calculation considers past loan payment history, number of loans, recent loan activity, and total loan volume, with a critical check for current debt exceeding the approved limit.

Financial Precision: Decimal types are used for all financial calculations (monthly_salary, loan_amount, interest_rate, monthly_installment, approved_limit, current_debt) to ensure accuracy and prevent floating-point errors.

Scalability: The Dockerized setup allows for easy scaling of both the web application and the database.

Contact
For any questions or further information, please contact [Sridhar_Pillai/sridharpillai75@gmail.com].