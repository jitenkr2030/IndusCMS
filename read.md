# IndusCMS

### Industry-first CMS & Business Management Platform

IndusCMS is an open-source, industry-first CMS and business platform built with **Django**.

The goal is to provide the flexibility of a traditional CMS like WordPress while adding business management, dynamic entities, workflows, APIs, permissions, and industry-specific templates.

Instead of building a separate application for every industry, IndusCMS provides **one core platform with reusable industry templates**.

---

## 🚀 Vision

> **Build any industry's website, business system, workflow, and API from one CMS.**

IndusCMS is designed to support businesses across many industries through configurable templates rather than separate hard-coded applications.

Examples:

* Retail
* Restaurant
* Security Services
* Construction
* Dairy
* Logistics
* Healthcare
* Education
* Real Estate
* Manufacturing
* Accounting
* Legal
* Hospitality
* Agriculture
* Automotive
* Professional Services
* and many more

---

# 🏗️ Architecture

```text
                         IndusCMS
                            │
                ┌───────────┴───────────┐
                │                       │
            CMS ENGINE            BUSINESS ENGINE
                │                       │
                └───────────┬───────────┘
                            │
                     ENTITY ENGINE
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
       Plugins          Templates            API
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                    Industry Templates
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
     Retail             Restaurant           Security
       │                    │                    │
      ...                  ...                  ...
```

---

# 🎯 Core Concept

IndusCMS separates the **platform** from the **industry configuration**.

For example, a security company does not need a completely different application.

The Security template can configure:

```text
Guards
Sites
Shifts
Attendance
Incidents
Documents
Payroll
Client Billing
Reports
```

A restaurant template can configure:

```text
Menu
Tables
Orders
Kitchen
Inventory
Suppliers
Expenses
Payments
Reports
```

The underlying CMS remains the same.

---

# ⭐ Planned Core Features

## CMS

* Pages
* Menus
* Media management
* Themes
* Widgets
* Website configuration
* Public website
* Admin dashboard

## Business Management

* Customers
* Suppliers
* Products
* Services
* Sales
* Purchases
* Payments
* Expenses
* Invoices
* Inventory
* Reports

## Dynamic Entity Engine

The most important feature of IndusCMS.

Users will be able to create custom business entities without writing application code.

Example:

```text
Entity: Vehicle

Fields:

Registration Number
Owner
Purchase Date
Insurance Expiry
Status
```

IndusCMS will automatically provide:

```text
List
Create
Edit
View
Search
Filters
Permissions
Audit Log
REST API
```

---

# 🔗 Relationships

Entities will support relationships.

Example:

```text
Customer
   │
   └── Orders
          │
          └── Order Items

Customer
   │
   └── Payments
```

Another example:

```text
Security Company
       │
       ├── Guards
       │
       ├── Sites
       │
       └── Shifts
              │
              └── Attendance
```

---

# 🔄 Workflow Engine

IndusCMS will provide configurable workflows.

Example:

### Security Guard

```text
New
 ↓
Documents Uploaded
 ↓
Verification
 ↓
Approved
 ↓
Assigned
 ↓
Active
```

### Restaurant Order

```text
Order
 ↓
Confirmed
 ↓
Kitchen
 ↓
Ready
 ↓
Delivered
 ↓
Paid
```

### Construction Material

```text
Material Request
 ↓
Manager Approval
 ↓
Purchase
 ↓
Received
 ↓
Site Consumption
```

---

# 🔌 Plugin System

IndusCMS is designed with a plugin architecture inspired by modern CMS platforms.

Plugins may provide:

* Models
* Admin pages
* Routes
* Permissions
* Dashboard widgets
* Reports
* Settings
* Events
* Hooks
* APIs
* Automation

Example future plugins:

```text
CRM Plugin
Inventory Plugin
Accounting Plugin
HR Plugin
Fleet Plugin
Booking Plugin
Property Plugin
Manufacturing Plugin
Workflow Plugin
AI Plugin
```

---

# 🧩 Industry Templates

An industry template is more than a database schema.

A template can contain:

```text
Schema
Fields
Relationships
Forms
Views
Menus
Dashboard
Workflows
Reports
Permissions
Automation
Theme
API configuration
```

Example:

```text
Security Template
├── Guards
├── Sites
├── Shifts
├── Attendance
├── Incidents
├── Payroll
├── Billing
└── Reports
```

---

# 🌐 API Platform

IndusCMS will provide APIs for businesses and integrations.

Planned capabilities:

* REST API
* API keys
* Authentication
* Permissions
* Webhooks
* Events
* Rate limiting
* API documentation

Future integrations may include:

```text
WordPress
WooCommerce
Tally
Excel
Mobile Apps
External SaaS
Accounting Software
Payment Systems
AI Applications
```

---

# 🛠️ Technology Stack

## Backend

* Python
* Django 5.x
* Django REST Framework

## Database

Development:

* SQLite

Production:

* PostgreSQL

## Frontend

Planned:

* React
* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui

## Infrastructure

Planned:

* Docker
* Redis
* Celery
* S3-compatible object storage
* GitHub Actions

## Deployment

Current development/deployment targets include:

* Faable Cloud
* Wasmer
* VPS
* Cloud infrastructure

The application is designed to remain portable between deployment platforms.

---

# 📁 Current Project Structure

```text
induscms/
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── core/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── templates/
│   └── core/
│       └── home.html
│
├── static/
│
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# ⚙️ Local Development

## 1. Clone Repository

```bash
git clone https://github.com/jitenkr2030/IndusCMS.git
cd IndusCMS
```

## 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure Environment

Create `.env`:

```env
DEBUG=1
DJANGO_SECRET_KEY=change-this-secret
```

For PostgreSQL:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
```

## 5. Run Migrations

```bash
python manage.py migrate
```

## 6. Create Admin User

```bash
python manage.py createsuperuser
```

## 7. Run Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

Open:

```text
http://127.0.0.1:8000/
```

Admin:

```text
http://127.0.0.1:8000/admin/
```

Health check:

```text
http://127.0.0.1:8000/health/
```

---

# ❤️ Health API

Endpoint:

```text
GET /health/
```

Example response:

```json
{
    "name": "IndusCMS",
    "status": "healthy",
    "version": "0.1.0"
}
```

This endpoint can be used by deployment platforms and monitoring systems to verify that the application is running.

---

# ☁️ Deployment

IndusCMS can run behind Gunicorn.

Example:

```bash
gunicorn config.wsgi:app
```

The WSGI module exposes both:

```python
application
```

and:

```python
app
```

This keeps the project compatible with standard Django deployment as well as platforms that expect a WSGI variable named `app`.

Production hosts must be added to Django's `ALLOWED_HOSTS`.

Example:

```python
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    ".wasmer.app",
    ".faable.link",
]
```

---

# 🗺️ Development Roadmap

## Phase 1 — Foundation

* [x] Django project
* [x] Core application
* [x] Home page
* [x] Admin
* [x] Health API
* [x] Environment configuration
* [x] SQLite development database
* [x] PostgreSQL-ready configuration
* [x] Gunicorn/WSGI support
* [x] Faable deployment

---

## Phase 2 — Identity & Business

* [ ] User system
* [ ] Organizations
* [ ] Businesses
* [ ] Multi-tenancy
* [ ] Roles
* [ ] Permissions
* [ ] Business settings
* [ ] Audit logs

---

## Phase 3 — Dynamic Entity Engine

* [ ] Entity builder
* [ ] Dynamic fields
* [ ] Field types
* [ ] Entity relationships
* [ ] Dynamic forms
* [ ] Dynamic lists
* [ ] Search
* [ ] Filters
* [ ] Sorting
* [ ] Pagination
* [ ] Dynamic CRUD

---

## Phase 4 — Business Engine

* [ ] Customers
* [ ] Suppliers
* [ ] Products
* [ ] Services
* [ ] Sales
* [ ] Purchases
* [ ] Payments
* [ ] Expenses
* [ ] Invoices
* [ ] Inventory
* [ ] Reports

---

## Phase 5 — Workflow Engine

* [ ] Workflow builder
* [ ] Statuses
* [ ] Transitions
* [ ] Approval system
* [ ] Conditions
* [ ] Actions
* [ ] Notifications
* [ ] Automation

---

## Phase 6 — API Engine

* [ ] REST API
* [ ] API keys
* [ ] API permissions
* [ ] Webhooks
* [ ] Events
* [ ] Rate limiting
* [ ] API documentation

---

## Phase 7 — Plugin System

* [ ] Plugin manifest
* [ ] Plugin installation
* [ ] Plugin activation/deactivation
* [ ] Plugin settings
* [ ] Plugin permissions
* [ ] Plugin routes
* [ ] Plugin events
* [ ] Plugin marketplace

---

## Phase 8 — Industry Templates

Initial templates:

```text
Retail
Restaurant
Security
Construction
Dairy
Logistics
Healthcare
Education
Real Estate
Manufacturing
Accounting
Legal
Hospitality
Agriculture
Automotive
```

The template system should eventually support **100+ industries**.

---

# 💡 Example: From CMS to Industry System

A user could create:

```text
New Business
     ↓
Select Industry
     ↓
Security Services
     ↓
Install Security Template
     ↓
IndusCMS configures:
     ├── Guards
     ├── Sites
     ├── Shifts
     ├── Attendance
     ├── Incidents
     ├── Payroll
     ├── Billing
     └── Reports
```

The same platform could then create:

```text
New Business
     ↓
Restaurant
     ↓
Restaurant Template
```

with:

```text
Menu
Tables
Orders
Kitchen
Inventory
Suppliers
Expenses
Payments
Reports
```

---

# 💰 Future Business Model

IndusCMS is designed to support a low-cost SaaS model.

Potential plans:

| Plan         |       Price |
| ------------ | ----------: |
| Starter      |   ₹999/year |
| Professional | ₹2,999/year |
| Business     | ₹9,999/year |
| Enterprise   |      Custom |

Additional revenue opportunities:

* Premium industry templates
* Premium plugins
* API usage
* AI features
* White-label deployments
* Custom integrations
* Hosting
* Enterprise support
* Template marketplace
* Developer marketplace

---

# 🔭 Long-Term Vision

IndusCMS aims to become an **industry operating platform** where a business can start with a template and progressively customize its entire digital operation.

```text
Website
   +
CRM
   +
Business Management
   +
Workflow
   +
Reports
   +
API
   +
Automation
   +
AI
   +
Industry Template
```

The long-term objective is:

> **One CMS. Hundreds of industries. Thousands of business configurations.**

---

# 📜 License

License to be determined.

---

# 👨‍💻 Project

**IndusCMS**

Developed by **Jitender Kumar**

GitHub:

`https://github.com/jitenkr2030/IndusCMS`
