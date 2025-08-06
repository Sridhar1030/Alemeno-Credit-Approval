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

Got it! Here’s the **corrected "Alternative Setup (Manual Docker Run Method)"** section integrated into your documentation in a polished, submission-ready format:

---

## Alternative Setup: Running with `docker run` (Manual Pull & Network Mode)

> **Note:** I have pushed my docker image on docker hub https://hub.docker.com/r/sridhar1030/alemenocreditapproval-web/tags.

This setup involves **manually pulling images**, **creating a custom Docker network**, and **running PostgreSQL and Django containers separately** using `docker run`. You'll also need to manually execute migrations and data ingestion inside the Django container.

---

### Steps:

### 1. **Pull Docker Images**

```bash
docker pull postgres:13-alpine
docker pull sridhar1030/alemenocreditapproval-web:latest
```

---

### 2. **Create a Custom Docker Network**

This allows the Django and PostgreSQL containers to communicate by container name.

```bash
docker network create my-credit-app-network
```

---

### 3. **Run PostgreSQL Container**

```bash
docker run -d \
  --name my-credit-app-db \
  --network my-credit-app-network \
  -e POSTGRES_DB=credit_approval_db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:13-alpine
```

* `--name my-credit-app-db`: Container name (used in Django's DATABASE\_URL).
* `--network my-credit-app-network`: Connects container to custom network.
* `-v postgres_data`: Persists PostgreSQL data locally.

---

### 4. **Run Django App Container**

```bash
docker run -d \
  --name my-credit-app-web \
  --network my-credit-app-network \
  -p 8000:8000 \
  -e DATABASE_URL="postgres://user:password@my-credit-app-db:5432/credit_approval_db" \
  sridhar1030/alemenocreditapproval-web:latest \
  python manage.py runserver 0.0.0.0:8000
```

* `-p 8000:8000`: Exposes port 8000 for API access.
* `-e DATABASE_URL`: Points Django to PostgreSQL using the **PostgreSQL container name (my-credit-app-db)**.
* `--network my-credit-app-network`: Ensures both containers can communicate.
* The command `python manage.py runserver` starts the Django development server.

---

### 5. **Run Database Migrations**

Execute inside the running **Django app container**:

```bash
docker exec my-credit-app-web python manage.py migrate
```

---

### 6. **Ingest Initial Data (Excel Files)**

Ensure `customer_data.xlsx` and `loan_data.xlsx` are present inside the app container. If they are not baked into the Docker image, you need to mount them using `-v` during `docker run` (or copy them using `docker cp`).

To ingest data:

```bash
docker exec my-credit-app-web python manage.py ingest_data
```

---

### 7. **Access the API**

Once the above steps are completed, your backend is running at:

```
http://localhost:8000/api/
```

---

### Important Notes

* **DATABASE\_URL syntax must exactly match:**
  `postgres://<DB_USER>:<DB_PASSWORD>@<POSTGRES_CONTAINER_NAME>:5432/<DB_NAME>`
* Ensure that **PostgreSQL is fully up and running** before launching Django.
* This method skips Docker Compose orchestration and mimics a production-like container setup workflow.
* For persistent storage, Docker Volume `postgres_data` is mounted.

---
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

