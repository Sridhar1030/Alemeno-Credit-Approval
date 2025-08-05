# 🏦 Credit Approval System - Backend

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.x-green?style=flat-square&logo=django)](https://djangoproject.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue?style=flat-square&logo=postgresql)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue?style=flat-square&logo=docker)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen?style=flat-square)](https://github.com)

> A comprehensive backend credit approval system built for Alemeno assignment. This system provides intelligent credit scoring, loan eligibility assessment, and complete loan management capabilities.

## 📚 Table of Contents

- [✨ Features](#-features)
- [🛠️ Technologies Used](#️-technologies-used)
- [📁 Project Structure](#-project-structure)
- [🚀 Setup and Installation](#-setup-and-installation)
  - [📋 Prerequisites](#-prerequisites)
  - [📂 Cloning the Repository](#-cloning-the-repository)
  - [🐳 Running with Docker Compose](#-running-with-docker-compose)
  - [🗃️ Database Migrations](#️-database-migrations)
  - [📊 Initial Data Ingestion](#-initial-data-ingestion)
- [🔗 API Endpoints](#-api-endpoints)
  - [👤 POST /api/register](#-post-apiregister)
  - [✅ POST /api/check-eligibility](#-post-apicheck-eligibility)
  - [💰 POST /api/create-loan](#-post-apicreate-loan)
  - [📄 GET /api/view-loan/<loan_id>](#-get-apiview-loanloan_id)
  - [📋 GET /api/view-loans/<customer_id>](#-get-apiview-loanscustomer_id)
- [🧪 Running Unit Tests](#-running-unit-tests)
- [📘 General Guidelines & Notes](#-general-guidelines--notes)
- [📞 Contact](#-contact)

## ✨ Features

| 🎯 Feature | 📝 Description |
|------------|----------------|
| 👤 **Customer Registration** | Register new customers with automatic credit limit calculation |
| 🎯 **Loan Eligibility Check** | Determine loan eligibility based on dynamic credit score from historical data |
| 💰 **Loan Creation** | Process new loan applications with automatic debt updates |
| 📄 **Loan Details View** | Retrieve comprehensive information for specific loans |
| 📋 **Customer Loan History** | View all current loan details for any customer |
| 📊 **Data Ingestion** | Automated ingestion from Excel files (customer_data.xlsx, loan_data.xlsx) |
| 🐳 **Dockerized Environment** | Easily deployable and scalable with Docker & Docker Compose |
| 🗃️ **PostgreSQL Database** | Robust and reliable data storage with ACID compliance |
| 🧪 **Unit Tests** | Comprehensive test suite for core logic and API endpoints |

## 🛠️ Technologies Used

<div align="center">

| Technology | Version | Purpose |
|------------|---------|---------|
| ![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white) | 3.11 | Core backend language |
| ![Django](https://img.shields.io/badge/Django-4.x-green?style=for-the-badge&logo=django&logoColor=white) | 4.x | Web framework |
| ![DRF](https://img.shields.io/badge/DRF-3.x-red?style=for-the-badge&logo=django&logoColor=white) | 3.x | API framework |
| ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue?style=for-the-badge&logo=postgresql&logoColor=white) | 13+ | Database |
| ![Docker](https://img.shields.io/badge/Docker-Latest-blue?style=for-the-badge&logo=docker&logoColor=white) | Latest | Containerization |
| ![Pandas](https://img.shields.io/badge/Pandas-2.x-purple?style=for-the-badge&logo=pandas&logoColor=white) | 2.x | Data processing |

</div>

**Additional Dependencies:**
- **Django REST Framework** - Building robust and scalable APIs
- **PostgreSQL** - ACID-compliant relational database
- **Docker & Docker Compose** - Containerization and orchestration
- **Pandas & Openpyxl** - Excel file processing and data ingestion
- **dj-database-url** - Simplified database configuration

## 📁 Project Structure

```
📦 Credit Approval System
├── 🏗️  core/                           # Django project configuration
│   ├── __init__.py
│   ├── asgi.py                         # ASGI configuration
│   ├── settings.py                     # Project settings
│   ├── urls.py                         # Main URL routing
│   └── wsgi.py                         # WSGI configuration
├── 💳 credit_approval/                 # Main application
│   ├── 🗄️  migrations/                # Database migrations
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   ├── ⚙️  management/                 # Custom management commands
│   │   └── commands/
│   │       └── ingest_data.py          # Data ingestion command
│   ├── 📊 models.py                    # Database models (Customer, Loan)
│   ├── 🔄 serializers.py               # DRF serializers
│   ├── 🧪 tests.py                     # Comprehensive unit tests
│   ├── 🔗 urls.py                      # API endpoint routing
│   └── 👁️  views.py                    # API business logic
├── 📈 customer_data.xlsx               # Sample customer data
├── 💰 loan_data.xlsx                   # Sample loan data
├── 🐳 Dockerfile                       # Container build instructions
├── 🔧 docker-compose.yml               # Multi-service orchestration
├── ⚡ manage.py                        # Django CLI utility
├── 📋 requirements.txt                 # Python dependencies
└── 📖 README.md                        # Project documentation
```

## 🚀 Setup and Installation

### 📋 Prerequisites

> **Important:** Ensure you have Docker Desktop installed and running on your machine.

<div align="center">

[![Docker Desktop](https://img.shields.io/badge/Download-Docker%20Desktop-blue?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/products/docker-desktop)

</div>

### 📂 Cloning the Repository

```bash
# Clone the repository
git clone <your-github-repo-url>

# Navigate to project directory
cd credit_approval_system
```

### 🐳 Running with Docker Compose

Start all services with a single command:

```bash
docker-compose up --build
```

> **⏱️ First Run:** This process may take 3-5 minutes as Docker downloads images and builds your application.

**✅ Success Indicators:**
- PostgreSQL database ready message
- Django development server starts at `http://0.0.0.0:8000/`

<div align="center">

🎉 **Keep this terminal window open and running!** 🎉

</div>

### 🗃️ Database Migrations

In a **new terminal window**, run the following commands:

```bash
# Create migrations
docker-compose exec web python manage.py makemigrations credit_approval

# Apply migrations
docker-compose exec web python manage.py migrate
```

### 📊 Initial Data Ingestion

Load the provided Excel data into your database:

```bash
docker-compose exec web python manage.py ingest_data
```

<div align="center">

✨ **Your Credit Approval System is now ready!** ✨

</div>

## 🔗 API Endpoints

> **Base URL:** `http://127.0.0.1:8000/api/`

<div align="center">

🛠️ **Testing Tools:** Use `curl`, Postman, or Insomnia to test the endpoints

</div>

### 🔍 Getting Sample IDs for Testing

After data ingestion, get valid IDs using the Django shell:

```bash
# Open Django shell
docker-compose exec web python manage.py shell
```

```python
# Inside the Django shell
from credit_approval.models import Customer, Loan

# Get customer ID
customer = Customer.objects.first()
print(f"Customer ID: {customer.customer_id}")

# Get loan ID
loan = Loan.objects.filter(customer=customer).first()
if loan:
    print(f"Loan ID: {loan.loan_id}")
else:
    print("No loans found for this customer yet.")

exit()
```

### 👤 POST /api/register

> **Purpose:** Register a new customer with automatic credit limit calculation

<details>
<summary><b>📝 Request Details</b></summary>

**Method:** `POST`  
**URL:** `http://127.0.0.1:8000/api/register`  
**Content-Type:** `application/json`

**Request Body:**
```json
{
    "first_name": "Alice",
    "last_name": "Johnson", 
    "age": 28,
    "monthly_income": 80000.00,
    "phone_number": "9911223344"
}
```

</details>

<details>
<summary><b>✅ Response Details</b></summary>

**Status:** `201 Created`

```json
{
    "customer_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "name": "Alice Johnson",
    "age": 28,
    "monthly_income": "80000.00",
    "approved_limit": "2900000.00",
    "phone_number": "9911223344"
}
```

</details>

<details>
<summary><b>🔧 cURL Example</b></summary>

```bash
curl -X POST http://127.0.0.1:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Alice",
    "last_name": "Johnson",
    "age": 28,
    "monthly_income": 80000,
    "phone_number": "9911223344"
  }'
```

</details>

### ✅ POST /api/check-eligibility

> **Purpose:** Check loan eligibility based on dynamic credit score and financial rules

<details>
<summary><b>📝 Request Details</b></summary>

**Method:** `POST`  
**URL:** `http://127.0.0.1:8000/api/check-eligibility`  
**Content-Type:** `application/json`

**Request Body:**
```json
{
    "customer_id": "PASTE_YOUR_CUSTOMER_UUID_HERE",
    "loan_amount": 500000.00,
    "interest_rate": 10.00,
    "tenure": 24
}
```

</details>

<details>
<summary><b>✅ Response Details</b></summary>

**Status:** `200 OK`

```json
{
    "customer_id": "PASTE_YOUR_CUSTOMER_UUID_HERE",
    "approval": true,
    "interest_rate": "10.00",
    "corrected_interest_rate": "10.00",
    "tenure": 24,
    "monthly_installment": "23265.46",
    "message": "Loan approved."
}
```

> **Note:** Message field appears for rejections or successful loan creation

</details>

<details>
<summary><b>🔧 cURL Example</b></summary>

```bash
curl -X POST http://127.0.0.1:8000/api/check-eligibility \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "PASTE_YOUR_CUSTOMER_UUID_HERE",
    "loan_amount": 500000,
    "interest_rate": 10.00,
    "tenure": 24
  }'
```

</details>

### 💰 POST /api/create-loan

> **Purpose:** Process new loan application and update customer debt upon approval

<details>
<summary><b>📝 Request Details</b></summary>

**Method:** `POST`  
**URL:** `http://127.0.0.1:8000/api/create-loan`  
**Content-Type:** `application/json`

**Request Body:**
```json
{
    "customer_id": "PASTE_YOUR_CUSTOMER_UUID_HERE",
    "loan_amount": 200000.00,
    "interest_rate": 13.00,
    "tenure": 18
}
```

</details>

<details>
<summary><b>✅ Response Details</b></summary>

**Status:** `200 OK`

```json
{
    "loan_id": 12345,
    "customer_id": "PASTE_YOUR_CUSTOMER_UUID_HERE", 
    "loan_approved": true,
    "message": "Loan approved successfully.",
    "monthly_installment": "12345.67"
}
```

> **loan_id:** Auto-generated unique integer identifier

</details>

<details>
<summary><b>🔧 cURL Example</b></summary>

```bash
curl -X POST http://127.0.0.1:8000/api/create-loan \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "PASTE_YOUR_CUSTOMER_UUID_HERE",
    "loan_amount": 200000,
    "interest_rate": 13.00,
    "tenure": 18
  }'
```

</details>

### 📄 GET /api/view-loan/\<loan_id\>

> **Purpose:** Retrieve detailed information for a specific loan and associated customer

<details>
<summary><b>📝 Request Details</b></summary>

**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/view-loan/PASTE_YOUR_LOAN_ID_HERE`

> **Parameter:** `loan_id` - Integer ID of the loan to retrieve

</details>

<details>
<summary><b>✅ Response Details</b></summary>

**Status:** `200 OK`

```json
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
```

</details>

<details>
<summary><b>🔧 cURL Example</b></summary>

```bash
curl -X GET http://127.0.0.1:8000/api/view-loan/PASTE_YOUR_LOAN_ID_HERE
```

</details>

### 📋 GET /api/view-loans/\<customer_id\>

> **Purpose:** Retrieve all current loan details for a specific customer

<details>
<summary><b>📝 Request Details</b></summary>

**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/view-loans/PASTE_YOUR_CUSTOMER_UUID_HERE`

> **Parameter:** `customer_id` - UUID of the customer whose loans to retrieve

</details>

<details>
<summary><b>✅ Response Details</b></summary>

**Status:** `200 OK`

```json
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
```

> **Returns:** Array of loan objects for the specified customer

</details>

<details>
<summary><b>🔧 cURL Example</b></summary>

```bash
curl -X GET http://127.0.0.1:8000/api/view-loans/PASTE_YOUR_CUSTOMER_UUID_HERE
```

</details>

## 🧪 Running Unit Tests

> **Comprehensive test suite covering core logic and all API endpoints**

<div align="center">

🔍 **Test Coverage:** Models • Serializers • Views • API Endpoints

</div>

### 🚀 Quick Test Execution

```bash
# Ensure Docker Compose is running
docker-compose up

# In a new terminal, run the test suite
docker-compose exec web python manage.py test credit_approval
```

<div align="center">

✅ **Expected Result:** All tests should pass

</div>

### 📊 Test Categories

| 🧪 Test Type | 📝 Coverage |
|--------------|-------------|
| **Model Tests** | Customer & Loan model validation, constraints |
| **Serializer Tests** | Data validation, field requirements |
| **View Tests** | API endpoint functionality, response formats |
| **Integration Tests** | End-to-end workflows, business logic |

## 📘 General Guidelines & Notes

<div align="center">

💡 **Key Principles:** Quality • Reliability • Scalability • Precision

</div>

### 🏗️ Code Architecture

| 🎯 Aspect | 📝 Implementation |
|-----------|------------------|
| **Code Quality** | Clear organization, separation of concerns (models, serializers, views) |
| **Standards** | Adherence to Django/DRF best practices and conventions |
| **Error Handling** | Comprehensive HTTP status codes and error messages |
| **Validation** | Input validation at multiple layers (serializers, models) |

### 🧮 Credit Score Algorithm

> **Intelligent scoring system considering multiple financial factors**

- 📊 **Payment History** - Past loan repayment behavior analysis
- 🔢 **Loan Portfolio** - Number and variety of existing loans  
- ⏰ **Recent Activity** - Latest loan application patterns
- 💰 **Volume Assessment** - Total loan amounts and utilization
- ⚠️ **Debt Limit Check** - Critical validation against approved limits

### 💰 Financial Precision

> **Decimal-based calculations for accurate financial operations**

**All monetary fields use `Decimal` types:**
- `monthly_salary` - Customer income precision
- `loan_amount` - Exact loan values
- `interest_rate` - Precise rate calculations  
- `monthly_installment` - Accurate payment amounts
- `approved_limit` & `current_debt` - Financial limit tracking

### 🚀 Scalability Features

- 🐳 **Containerized Architecture** - Easy horizontal scaling
- 🗃️ **PostgreSQL Database** - Enterprise-grade data management
- 🔄 **Stateless API Design** - Load balancer friendly
- 📊 **Efficient Data Models** - Optimized query performance

---

## 📞 Contact

<div align="center">

**For questions, support, or collaboration:**

[![Email](https://img.shields.io/badge/Email-sridharpillai75%40gmail.com-red?style=for-the-badge&logo=gmail&logoColor=white)](mailto:sridharpillai75@gmail.com)

**Developer:** Sridhar Pillai

</div>

---

<div align="center">

⭐ **Star this repository if you found it helpful!** ⭐

</div>