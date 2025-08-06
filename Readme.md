Here’s a polished and professional version of your **Alemeno Credit Approval System - Backend Documentation**:

---

# Alemeno Credit Approval System - Backend

This project implements a backend Credit Approval System as an assignment for **Alemeno**. It is built using **Python (Django + Django REST Framework)**, **Dockerized with PostgreSQL**, and includes **unit tests** for core functionalities and API endpoints.

---

## Table of Contents

1. [Features](#features)
2. [Technologies Used](#technologies-used)
3. [Project Structure](#project-structure)
4. [Setup and Installation](#setup-and-installation)

   * Prerequisites
   * Cloning the Repository
   * Running with Docker Compose
   * Database Migrations
   * Initial Data Ingestion
5. [API Endpoints](#api-endpoints)

   * Register Customer
   * Check Loan Eligibility
   * Create Loan
   * View Loan Details
   * View Customer Loans
6. [Running Unit Tests](#running-unit-tests)
7. [Alternative Setup (Docker Pull Method)](#alternative-setup-docker-pull-method)
8. [General Guidelines & Notes](#general-guidelines--notes)
9. [Contact](#contact)

---

## Features

* **Customer Registration** with automatic approved credit limit calculation.
* **Loan Eligibility Check** based on dynamic credit scoring logic.
* **Loan Creation** workflow with real-time debt updates.
* **Detailed Loan View** for individual loans.
* **Customer Loan History** retrieval.
* **Excel Data Ingestion** for initial customer & loan data.
* **Dockerized Environment** for easy setup and deployment.
* **PostgreSQL Database** for reliable storage.
* **Unit Tests** covering business logic and API endpoints.

---

## Technologies Used

* **Python 3.11**
* **Django 4.x**
* **Django REST Framework**
* **PostgreSQL**
* **Docker & Docker Compose**
* **Pandas & Openpyxl** (for Excel ingestion)
* **dj-database-url** (for database URL parsing)

---

## Project Structure

```
.
├── core/                        # Django project settings
├── credit_approval/             # Django app for credit logic
│   ├── migrations/              # Database migration files
│   ├── management/              # Custom management commands (ingest_data)
│   ├── models.py                # Database models (Customer, Loan)
│   ├── serializers.py           # DRF serializers
│   ├── tests.py                 # Unit tests
│   ├── urls.py                  # API routing
│   └── views.py                 # API view logic
├── customer_data.xlsx           # Sample customer data
├── loan_data.xlsx               # Sample loan data
├── Dockerfile                   # Docker build instructions
├── docker-compose.yml           # Docker Compose orchestration file
├── manage.py                    # Django management utility
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

## Setup and Installation

### Prerequisites

* **Docker Desktop** installed and running.

  * [Download Docker Desktop](https://www.docker.com/products/docker-desktop)

### Cloning the Repository

```bash
git clone <your-github-repo-url>
cd credit_approval_system
```

### Running with Docker Compose

```bash
docker-compose up --build
```

* This builds the Django image, pulls PostgreSQL, and starts both services.
* Once successful, the Django server will be running at: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

### Database Migrations

In a **new terminal window**:

```bash
docker-compose exec web python manage.py makemigrations credit_approval
docker-compose exec web python manage.py migrate
```

### Initial Data Ingestion

```bash
docker-compose exec web python manage.py ingest_data
```

---

## API Endpoints

Base URL: **[http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)**

### 1. **POST /register** – Customer Registration

* **Request Body:**

```json
{
    "first_name": "Alice",
    "last_name": "Johnson",
    "age": 28,
    "monthly_income": 80000.00,
    "phone_number": "9911223344"
}
```

* **Response:**

```json
{
    "customer_id": "<UUID>",
    "name": "Alice Johnson",
    "approved_limit": "2900000.00",
    ...
}
```

### 2. **POST /check-eligibility** – Loan Eligibility Check

* **Request Body:**

```json
{
    "customer_id": "<UUID>",
    "loan_amount": 500000.00,
    "interest_rate": 10.00,
    "tenure": 24
}
```

* **Response:**

```json
{
    "approval": true,
    "monthly_installment": "23265.46",
    "message": "Loan approved."
}
```

### 3. **POST /create-loan** – Create Loan

* **Request Body:**

```json
{
    "customer_id": "<UUID>",
    "loan_amount": 200000.00,
    "interest_rate": 13.00,
    "tenure": 18
}
```

* **Response:**

```json
{
    "loan_id": 12345,
    "loan_approved": true,
    "monthly_installment": "12345.67"
}
```

### 4. **GET /view-loan/\<loan\_id>** – View Loan Details

* **Response:**

```json
{
    "loan_id": 12345,
    "customer": {
        "id": "<UUID>",
        "first_name": "Alice",
        ...
    },
    "loan_amount": "200000.00",
    ...
}
```

### 5. **GET /view-loans/\<customer\_id>** – View Customer's Loans

* **Response:**

```json
[
    {
        "loan_id": 12345,
        "loan_amount": "200000.00",
        "repayments_left": 18
    },
    ...
]
```

---

## Running Unit Tests

```bash
docker-compose exec web python manage.py test credit_approval
```

All tests should pass successfully.

---

## Alternative Setup: Docker Pull Method (Advanced)

> **Note:** This is NOT the recommended approach for assignment submissions.

### Steps:

1. Ensure `customer_data.xlsx` and `loan_data.xlsx` are in the working directory.
2. Create a **docker-compose.yml** with the following:

```yaml
version: '3.8'
services:
  db:
    image: postgres:13-alpine
    environment:
      POSTGRES_DB: credit_approval_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"

  web:
    image: sridhar1030/alemenocreditapproval-web:latest
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgres://user:password@db:5432/credit_approval_db
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
```

3. Run:

```bash
docker-compose up
```

4. Run migrations:

```bash
docker-compose exec web python manage.py migrate
```

5. Ingest data:

```bash
docker-compose exec web python manage.py ingest_data
```

---

## General Guidelines & Notes

* **Code Quality:** Organized with Django/DRF best practices.
* **Error Handling:** Proper HTTP status codes & error messages.
* **Financial Precision:** All financial fields use Decimal for accuracy.
* **Credit Scoring Logic:** Dynamic scoring based on payment history, debt limits, and loan activity.
* **Security Note:** For demo purposes, credentials are hardcoded. In production, use environment variables or Docker secrets.

---

## Contact

For queries or collaboration, feel free to reach out:

* **Name:** Sridhar Pillai
* **Email:** [sridharpillai1030@gmail.com](mailto:sridharpillai1030@gmail.com)
* **LinkedIn:** [linkedin.com/in/sridhar-pillai](https://linkedin.com/in/sridhar-pillai)

