# Business & Inventory Management System

A multi-tenant Django REST API for managing business inventory, customer relationships, order invoicing, and financial reporting with Role-Based Access Control (RBAC), atomic inventory tracking, and Redis caching.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture & Multi-Tenancy](#architecture--multi-tenancy)
- [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Configuration](#environment-configuration)
  - [Database Migrations](#database-migrations)
  - [Creating a Superuser](#creating-a-superuser)
  - [Running the Server](#running-the-server)
- [API Reference](#api-reference)
  - [Authentication](#authentication)
  - [Accounts & Companies](#accounts--companies)
  - [Inventory & Catalog](#inventory--catalog)
  - [Billing & Invoicing](#billing--invoicing)
  - [Analytics & Reports](#analytics--reports)
- [Printable Invoices](#printable-invoices)
- [Running Tests](#running-tests)
- [License](#license)

---

## Features

- **Multi-Tenant Architecture**: Strict company-level data isolation across customers, categories, products, and invoices.
- **Role-Based Access Control (RBAC)**: Fine-grained permissions separating **Admin**, **Manager**, and **Staff** capabilities.
- **JWT Authentication**: Secure stateless token authentication via SimpleJWT, with support for query-param authentication for printable views.
- **Inventory & Catalog Management**:
  - Hierarchical categories with parent-child support.
  - SKU uniqueness enforced per company (different companies can reuse SKU identifiers).
  - Search and category filtering.
  - High-performance Redis caching with automated cache versioning and invalidation.
- **Transactional Billing Engine**:
  - Atomic invoice generation with database-level row locking (`select_for_update`) to prevent race conditions.
  - Automatic stock deduction upon invoice creation.
  - Stock auto-replenishment and recalculation when updating or deleting invoice items.
  - Automated unique invoice numbers (`INV-XXXXXXXX`).
- **Printable Invoices**:
  - Browser-native print & PDF export template with query parameter authentication (`?token=...`).
- **Dashboard & Sales Analytics**:
  - Aggregated revenue metrics and invoice status counts.
  - Automated low-stock alerts (`stock_quantity <= 5`).
  - Top-selling products ranking.
  - Date-filtered sales reports.

---

## Tech Stack

- **Backend Framework**: [Django 6.1](https://www.djangoproject.com/)
- **API Engine**: [Django REST Framework (DRF) 3.18](https://www.django-rest-framework.org/)
- **Authentication**: [Django REST Framework SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- **Database**: [PostgreSQL](https://www.postgresql.org/) (via `psycopg` 3)
- **Caching**: [Redis](https://redis.io/) (`django.core.cache.backends.redis.RedisCache`)
- **Document Rendering**: HTML/CSS print template with optional PDF styling

---

## Architecture & Multi-Tenancy

Every entity belongs to a `Company`. Data access across all inventory, billing, and user management views is automatically filtered by the requesting user's tenant:

```
[Company]
   ├── [Users] (Admin, Manager, Staff)
   ├── [Customers]
   ├── [Categories] (Hierarchical subcategories)
   ├── [Products] (Unique SKU per Company)
   └── [Invoices]
         └── [InvoiceItems] (Deducts Product Stock)
```

---

## Role-Based Access Control (RBAC)

| Capability | Admin | Manager | Staff |
|---|:---:|:---:|:---:|
| Manage all companies |  |  |  |
| Manage own company profile |  |  |  |
| Create users for own company |  (any role) |  (Staff only) |  |
| Update own company users |  |  (Staff only) |  (Self only) |
| Manage customers & products |  |  |  |
| Create & view invoices |  |  |  |
| View dashboard & sales reports |  |  |  |
| Delete users/companies |  |  (Staff only) |  |

---

## Project Structure

```
Buisness_Inventory/
├── manage.py
├── requirements.txt
├── core/                        # Project configuration
│   ├── settings.py              # App, DB, Cache & JWT configuration
│   ├── urls.py                  # Root URL router
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                    # Users & Companies
│   ├── models.py                # Company & custom User models
│   ├── permissions.py           # IsAdmin, IsAdminManager RBAC permissions
│   ├── authentication.py        # JWTQueryParamAuthentication for browser URLs
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── inventory/                   # Product, Category & Customer management
│   ├── models.py                # Customer, Category, Product
│   ├── cache_services.py        # Redis cache versioning and key generation
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
└── billing/                     # Invoicing, Reporting & Dashboard
    ├── models.py                # Invoice, InvoiceItem
    ├── serializers.py           # Atomic stock handling during invoicing
    ├── views.py                 # Invoice CRUD, Dashboard Summary, Sales Report
    ├── urls.py
    └── templates/
        └── billing/
            └── invoice_pdf.html # Clean print & PDF layout
```

---

## Getting Started

### Prerequisites

- **Python**: 3.12+ (tested up to 3.14)
- **PostgreSQL**: 14+ running locally or remotely
- **Redis**: 6.0+ running locally or remotely

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Buisness_Inventory
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate       # On Linux/macOS
   # or venv\Scripts\activate   # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Environment Configuration

The application uses standard environment variables with sensible development defaults:

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DEBUG` | Enable debug mode (`True` or `False`) | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `*` |
| `DB_NAME` | PostgreSQL database name | `inventory` |
| `DB_USER` | PostgreSQL user | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | `password` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `REDIS_URL` | Redis connection URL | `redis://127.0.0.1:6379/0` |

You can export these in your shell or set up a `.env` file:
```bash
export DB_NAME="inventory"
export DB_USER="postgres"
export DB_PASSWORD="your_password"
export DB_HOST="localhost"
export DB_PORT="5432"
export REDIS_URL="redis://127.0.0.1:6379/0"
```

### Database Migrations

Apply database migrations:
```bash
python manage.py migrate
```

### Creating a Superuser

Create the initial administrator account:
```bash
python manage.py createsuperuser
```

### Running the Server

Start the Django development server:
```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

---

## API Reference

All protected endpoints require an `Authorization: Bearer <access_token>` header, unless otherwise specified.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/token/` | Obtain JWT access and refresh token pair |
| `POST` | `/api/token/refresh/` | Refresh expired access token |

#### Example Login Request
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

---

### Accounts & Companies

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/accounts/companies/` | Admin | List all companies |
| `POST` | `/api/accounts/companies/` | Admin | Create a new company |
| `GET` | `/api/accounts/companies/<id>/` | Admin, Manager | Retrieve company details |
| `PUT/PATCH` | `/api/accounts/companies/<id>/` | Admin, Manager | Update company |
| `DELETE` | `/api/accounts/companies/<id>/` | Admin | Delete company |
| `GET` | `/api/accounts/users/` | Admin, Manager | List users (filtered by company for managers) |
| `POST` | `/api/accounts/users/` | Admin, Manager | Create a user |
| `GET/PUT/PATCH` | `/api/accounts/users/<id>/` | Authenticated | Retrieve or update user details |
| `DELETE` | `/api/accounts/users/<id>/` | Admin, Manager | Delete user account |

---

### Inventory & Catalog

| Method | Endpoint | Query Parameters | Description |
|---|---|---|---|
| `GET` | `/api/inventory/customers/` | `?search=<name>` | List company customers |
| `POST` | `/api/inventory/customers/` | - | Create a customer |
| `GET/PUT/PATCH/DELETE` | `/api/inventory/customers/<id>/` | - | Customer detail operations |
| `GET` | `/api/inventory/categories/` | - | List product categories |
| `POST` | `/api/inventory/categories/` | - | Create a category (supports nested parents) |
| `GET/PUT/PATCH/DELETE` | `/api/inventory/categories/<id>/` | - | Category detail operations |
| `GET` | `/api/inventory/products/` | `?category=<id>&search=<name>` | List products with Redis caching |
| `POST` | `/api/inventory/products/` | - | Create a product |
| `GET/PUT/PATCH/DELETE` | `/api/inventory/products/<id>/` | - | Product detail operations |

---

### Billing & Invoicing

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/billing/invoices/` | List company invoices |
| `POST` | `/api/billing/invoices/` | Create an invoice & atomically deduct stock |
| `GET` | `/api/billing/invoices/<id>/` | Retrieve invoice details with line items |
| `PUT/PATCH` | `/api/billing/invoices/<id>/` | Update invoice (re-syncs stock quantities) |
| `DELETE` | `/api/billing/invoices/<id>/` | Delete invoice |

#### Example: Create an Invoice
```bash
curl -X POST http://127.0.0.1:8000/api/billing/invoices/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer": 1,
    "status": "paid",
    "items": [
      {
        "product": 5,
        "quantity": 2,
        "unit_price": "49.99"
      }
    ]
  }'
```

> **Note on Stock Validation**: The API uses PostgreSQL row-level locks (`select_for_update`) within an atomic transaction. If stock for any item is insufficient, the entire invoice creation fails with HTTP 400 and stock remains intact.

---

### Analytics & Reports

| Method | Endpoint | Query Parameters | Description |
|---|---|---|---|
| `GET` | `/api/billing/dashboard/summary/` | - | Summary metrics: revenue, invoice status breakdown, low-stock warnings, top products |
| `GET` | `/api/billing/reports/sales/` | `?from=YYYY-MM-DD&to=YYYY-MM-DD` | Sales report with date filtering |

#### Dashboard Summary Response Example
```json
{
  "total_invoices": 42,
  "total_revenue": 15420.50,
  "invoices_by_status": [
    {"status": "paid", "count": 35},
    {"status": "draft", "count": 7}
  ],
  "low_stock_products": [
    {"id": 12, "name": "Wireless Mouse", "stock_quantity": 2}
  ],
  "top_products": [
    {"id": 5, "name": "Mechanical Keyboard", "stock_quantity": 18, "total_sold": 45}
  ]
}
```

---

## Printable Invoices

Invoices can be opened directly in any browser for immediate printing or saving as PDF via the browser's native print dialog:

```
GET /api/billing/invoices/<id>/print/?token=<access_token>&auto=1
```

- **`token`**: JWT access token passed via query parameter (bypasses browser authorization header restrictions).
- **`auto`**: Set `auto=1` (default) to trigger the browser's print dialog automatically on load, or `auto=0` for view-only.

---

## Running Tests

Run the full test suite covering all applications (Accounts, Inventory, and Billing):

```bash
python manage.py test accounts inventory billing
```

Test coverage includes:
- Cross-tenant data isolation and security checks
- Role-based privilege elevation restrictions
- Atomic stock deduction and restoration on invoice updates
- SKU uniqueness isolation across companies
- Dashboard aggregations and sales reporting
- Printable invoice authentication via query param tokens

---

## License

This project is open-source and available under the [MIT License](LICENSE).
