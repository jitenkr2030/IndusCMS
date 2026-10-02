# IndusCMS

**Industry-first Business Platform built with Django**

IndusCMS is a modular CMS and business application platform designed
to build industry-specific software on top of reusable business engines.

The goal is to provide a flexible foundation for applications such as:

- CRM
- HR Management
- Inventory
- Sales & Purchase
- Accounting
- Fleet Management
- Logistics
- Booking
- Ticketing
- Compliance
- Field Service
- Manufacturing

Instead of building every business application from scratch,
IndusCMS provides reusable infrastructure for entities, fields,
records, permissions, workflows, APIs and industry templates.

## Project Status

**Current phase: Phase 3 — Dynamic Entity Engine**

Phase 1 and Phase 2 are complete.

Phase 3 is actively under development.


## Platform Architecture

IndusCMS is being developed as a modular monolith initially.

Core platform engines:

1. CMS Engine
2. Business Engine
3. Dynamic Entity Engine
4. Workflow Engine
5. API Engine
6. Plugin Engine
7. Industry Template Engine

The architecture is designed so that these engines can be reused
across multiple industries.

## Technology Stack

### Backend

- Python
- Django 5.x
- Django REST Framework
- PostgreSQL
- SQLite for local development

### Planned Infrastructure

- Redis
- Celery
- S3-compatible storage
- Docker
- GitHub Actions

### Frontend

Planned:

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui


## Completed Phases

### Phase 1 — Core CMS Foundation

Completed:

- Django project setup
- Core application
- Homepage
- Django Admin
- Health endpoint
- Environment configuration
- SQLite development database
- PostgreSQL-ready configuration
- Gunicorn/WSGI configuration
- WhiteNoise support
- GitHub repository
- Deployment configuration
- ALLOWED_HOSTS configuration

### Phase 2 — Business & Tenant Foundation

Completed:

- Business model
- Role model
- Permission model
- RolePermission model
- Membership model
- BusinessSettings model
- AuditLog model
- Business onboarding service
- Permission service
- Audit logging service
- Role/permission seeding
- Django Admin integration


## Phase 3 — Dynamic Entity Engine

The Dynamic Entity Engine allows each business to create
custom business data structures without requiring a new Django model
for every business object.

### EntityDefinition

Defines a business entity.

Examples:

- Customer
- Product
- Employee
- Vehicle
- Student
- Patient
- Invoice

### FieldDefinition

Defines fields belonging to an entity.

Supported field types currently include:

- text
- long_text
- number
- decimal
- boolean
- date
- datetime
- email
- url
- choice
- json

### EntityRecord

Stores actual records using a JSON data structure.

This allows the same platform to support different industries
without creating separate database tables for every custom entity.

## Current Dynamic Entity Features

Completed:

- Entity creation
- Entity listing
- Entity detail
- Entity field creation
- Dynamic field validation
- Required fields
- Default values
- Choice validation
- Type validation
- Dynamic record creation
- Record listing
- Record detail
- Record update
- Soft delete
- Record deletion protection
- Pagination
- Entity permissions
- Audit logging


## Current Development Status

### Phase 3 — Dynamic Entity Engine

Current status:

- Entity model: Complete
- Field definition model: Complete
- Entity record model: Complete
- Entity creation API: Complete
- Entity list API: Complete
- Entity detail API: Complete
- Field creation API: Complete
- Dynamic record CRUD API: Complete
- Dynamic validation: Complete
- Permission checks: Complete
- Audit logging: Complete
- Entity update API: In progress
- Entity update tests: Pending

The entity update feature must pass its dedicated tests before
Phase 3.7C is marked complete.

## Roadmap

### Phase 3 — Dynamic Entity Engine

- [x] Entity definitions
- [x] Field definitions
- [x] Dynamic records
- [x] Field validation
- [x] Record CRUD
- [x] Soft deletion
- [x] Entity listing
- [x] Entity detail
- [x] Permission integration
- [x] Audit logging
- [ ] Entity update API
- [ ] Entity update tests
- [ ] Entity deactivation
- [ ] Advanced entity filtering
- [ ] Entity search
- [ ] Entity relationships

### Phase 4 — Business Application Engine

Planned reusable business modules:

- CRM
- Customers
- Products
- Inventory
- Sales
- Purchases
- Employees
- HR
- Accounting
- Assets
- Projects
- Fleet
- Logistics
- Bookings
- Tickets
- Documents
- Compliance
- Field Service
- Subscriptions
- Memberships

### Phase 5 — Workflow Engine

Planned capabilities:

- Approval workflows
- Status transitions
- Conditions
- Actions
- Notifications
- Assignment rules
- Automation
- Scheduled tasks

### Phase 6 — API & Integration Engine

Planned capabilities:

- REST API expansion
- API authentication
- API keys
- Webhooks
- External integrations
- Import/export
- Third-party application integration

### Phase 7 — Plugin Engine

Planned capabilities:

- Installable plugins
- Plugin lifecycle
- Plugin configuration
- Plugin permissions
- Plugin APIs
- Industry-specific extensions

### Phase 8 — Industry Templates

Planned templates include:

- Restaurant
- School
- Security Agency
- Logistics
- Retail
- Service Business
- Accounting Firm
- Healthcare
- Manufacturing
- Real Estate

Industry templates will provide reusable:

- Entities
- Fields
- Relationships
- Forms
- Views
- Dashboards
- Menus
- Workflows
- Reports
- Permissions
- Automation

