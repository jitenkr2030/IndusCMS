# IndusCMS

**Industry-first CMS & Business Application Platform built with Django**

IndusCMS is a modular, industry-first platform for building configurable business applications on top of reusable engines for businesses, dynamic entities, relationships, workflows, APIs and future industry templates.

The goal is to avoid rebuilding the same business infrastructure for every industry.

## Project Status

**Phase 4.2 — Workflow History & Management APIs: COMPLETE**

Current full test status:

**110 tests passed**

Completed phases:

- Phase 1 — Core CMS Foundation
- Phase 2 — Business & Tenant Foundation
- Phase 3 — Dynamic Entity Engine
- Phase 4.1 — Workflow Foundation
- Phase 4.2 — Workflow History & Management APIs

## Platform Architecture

IndusCMS is being developed as a modular monolith initially.

Core engines:

1. CMS Engine
2. Business Engine
3. Dynamic Entity Engine
4. Workflow Engine
5. API Engine
6. Plugin Engine
7. Industry Template Engine

Reusable business engines planned on top of this foundation include CRM, HR, Inventory, Sales, Purchase, Accounting, Assets, Projects, Fleet, Logistics, Booking, Ticketing, Compliance, Field Service, Subscriptions and Memberships.

## Technology Stack

### Backend

- Python
- Django 5.x
- Django REST Framework
- PostgreSQL for production
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

## Phase 1 — Core CMS Foundation

Completed:

- Django project setup
- Core application
- Homepage
- Django Admin
- Health endpoint
- Environment configuration
- SQLite development database
- PostgreSQL-ready configuration
- Gunicorn/WSGI
- WhiteNoise
- Deployment configuration
- GitHub repository

## Phase 2 — Business & Tenant Foundation

Completed:

- Business model
- Roles and permissions
- Memberships
- Business settings
- Audit logging
- Business onboarding service
- Permission service
- Role/permission seeding
- Django Admin integration

## Phase 3 — Dynamic Entity Engine

The Dynamic Entity Engine allows each business to define configurable business data without creating a new Django model for every business object.

### Entities

Examples:

- Customer
- Product
- Employee
- Vehicle
- Student
- Invoice
- Booking

### Supported field types

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

### Dynamic Entity Features

- Entity creation/list/detail
- Entity update/deactivation
- Entity deletion protection
- Field creation/list/detail/update/deactivation
- Dynamic record CRUD
- Type validation
- Required fields
- Default values
- Choice validation
- Soft deletion
- Pagination
- Search
- Sorting
- Dynamic forms
- Dynamic tables
- Entity relationships
- Relationship validation
- Relationship options
- Role-based permissions
- Audit logging

## Phase 4 — Workflow Engine

### Phase 4.1 — Workflow Foundation

Completed:

- Workflow definitions
- Workflow steps
- Initial/final steps
- Workflow transitions
- Workflow instances
- Instance state transitions
- Workflow permissions
- Workflow audit events

### Phase 4.2 — Workflow History & Management

Completed:

- Workflow history timeline
- Start/transition history entries
- Completed workflow history
- Workflow update API
- Workflow deactivation API
- Workflow deletion protection
- Workflow step listing API
- Workflow transition listing API
- Workflow instance listing API
- Workflow instance history API
- Workflow management services
- Dedicated workflow API test suite

Current verification:

**110/110 tests passing**

## Phase 4.3 — Next

Planned:

- Workflow conditions
- Transition rules
- Transition permissions
- Workflow actions
- Notifications
- Webhooks
- Record-based automation
- Scheduled automation

Example:

`Invoice amount > ₹50,000 → Manager Approval → Finance Approval → Completed`

The long-term workflow model is:

`Record → Condition → Transition → Action`

## Phase 5 — API & Integration Engine

Planned:

- Expanded REST APIs
- API authentication
- API keys
- Webhooks
- Import/export
- External integrations
- Third-party application integration

## Phase 6 — Plugin Engine

Planned:

- Installable plugins
- Plugin lifecycle
- Plugin configuration
- Plugin permissions
- Plugin APIs
- Industry-specific extensions

## Phase 7 — Industry Templates

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

Industry templates will combine:

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

## Vision

IndusCMS aims to become a reusable **business application infrastructure layer** where one platform can power many industry-specific SaaS products.

Instead of building a separate backend foundation for every application:

`Business + Dynamic Entities + Workflow + API + Plugins + Industry Template`

becomes the reusable core.

## License

Project is under active development.
