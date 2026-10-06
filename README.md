# IndusCMS

**Industry-first CMS & Business Application Platform built with Django.**

IndusCMS is a reusable business application infrastructure platform for building configurable, industry-specific software without rebuilding the same backend foundation for every product.

The core idea is simple:

```text
Business
   +
Dynamic Entities
   +
Relationships
   +
Workflow
   +
Automation
   +
API
   +
Plugins
   +
Industry Templates
```

Instead of creating a completely separate backend for every CRM, ERP, HR, logistics, school, restaurant, security, service or booking application, IndusCMS provides reusable platform engines that can power many different business applications.

---

## Project Status

### Phase 4 — Workflow & Automation Engine

**COMPLETE locally**

Current verification:

```text
223 / 223 tests passing
```

Validation completed:

* Django system check — PASS
* Migration check — PASS
* `git diff --check` — PASS
* Workflow foundation — PASS
* Workflow management — PASS
* Workflow conditions — PASS
* Workflow triggers — PASS
* Record event dispatcher — PASS
* Workflow actions — PASS
* Webhook execution — PASS
* Webhook security validation — PASS
* Action execution history — PASS
* Retry mechanism — PASS
* DB-backed asynchronous queue — PASS
* Workflow worker — PASS
* Workflow engine transition processing — PASS
* Workflow cancellation/resume — PASS
* Audit logging — PASS

The project is currently being developed as a modular Django monolith.

---

# Vision

IndusCMS aims to become a reusable **business application infrastructure layer**.

The long-term goal is to make it possible to build many industry applications from the same platform foundation.

Examples:

```text
IndusCMS
   |
   +-- Restaurant Management
   +-- School Management
   +-- Security Agency Management
   +-- Logistics Management
   +-- Retail Management
   +-- CRM
   +-- HR
   +-- Inventory
   +-- Accounting
   +-- Booking
   +-- Ticketing
   +-- Field Service
   +-- Fleet Management
   +-- Membership
   +-- Subscription Management
```

Each application can reuse the same:

* Business engine
* User system
* Permission system
* Dynamic data engine
* Relationship engine
* Workflow engine
* Automation engine
* API layer
* Audit system

Only the industry-specific configuration needs to change.

---

# The Problem

Traditional business applications often follow this pattern:

```text
New Industry
     |
     v
New Django Project
     |
     +-- Users
     +-- Roles
     +-- Permissions
     +-- Customers
     +-- Products
     +-- Forms
     +-- APIs
     +-- Workflows
     +-- Notifications
     +-- Audit Logs
     +-- Reports
     +-- Automation
```

This results in the same infrastructure being rebuilt repeatedly.

IndusCMS attempts to solve this by moving common business infrastructure into reusable platform engines.

---

# The IndusCMS Model

A future application can be represented as:

```text
Industry
   |
   v
Business
   |
   v
Entities
   |
   v
Fields
   |
   v
Records
   |
   v
Relationships
   |
   v
Workflows
   |
   v
Events
   |
   v
Actions
   |
   v
Reports / APIs / Dashboards
```

This allows the platform to become configuration-driven rather than model-driven for every business object.

---

# Core Architecture

```text
                         IndusCMS
                            |
       +--------------------+--------------------+
       |                    |                    |
       v                    v                    v
 Business Engine     Dynamic Entity Engine    API Engine
       |                    |                    |
       |              Entity / Field / Record   REST APIs
       |                    |
       +------------- Relationships ------------+
                            |
                            v
                     Workflow Engine
                            |
             +--------------+--------------+
             |                             |
             v                             v
        Conditions                   Transitions
             |                             |
             +--------------+--------------+
                            |
                            v
                       Event Engine
                            |
                            v
                    Workflow Triggers
                            |
                            v
                       Action Engine
                            |
             +--------------+--------------+
             |                             |
             v                             v
         Webhooks                    Async Queue
                                           |
                                           v
                                   DB-backed Worker
                                           |
                                           v
                                  Execution History
                                           |
                                           v
                                      Audit Log
```

---

# Platform Engines

## 1. Business Engine

The Business Engine provides the tenant/business foundation.

Current capabilities include:

* Business creation
* Business configuration
* Business membership
* Roles
* Permissions
* Permission checks
* Role seeding
* Business-level access control
* Audit logging
* Business onboarding foundation

A business can therefore become the tenant boundary for industry applications.

---

# 2. Dynamic Entity Engine

The Dynamic Entity Engine allows businesses to define configurable business objects without creating a separate Django model for every object type.

Example:

```text
Customer
Product
Employee
Vehicle
Student
Invoice
Booking
Project
Asset
Ticket
```

Instead of creating:

```text
Customer model
Product model
Employee model
Vehicle model
...
```

the platform can represent these as configurable entities.

### Entity structure

```text
Entity Definition
       |
       +-- Field Definition
       |      |
       |      +-- text
       |      +-- number
       |      +-- decimal
       |      +-- boolean
       |      +-- date
       |      +-- datetime
       |      +-- email
       |      +-- url
       |      +-- choice
       |      +-- json
       |
       +-- Entity Records
```

Current dynamic entity capabilities include:

* Entity creation
* Entity listing
* Entity detail
* Entity update
* Entity deactivation
* Entity deletion protection
* Field creation
* Field listing
* Field detail
* Field update
* Field deactivation
* Dynamic record creation
* Dynamic record update
* Dynamic record deletion
* Type validation
* Required field validation
* Default values
* Choice validation
* Soft deletion
* Pagination
* Search
* Sorting
* Dynamic forms
* Dynamic tables
* Relationship support
* Permission checks
* Audit logging

---

# 3. Relationship Engine

Business applications rarely contain isolated records.

Examples:

```text
Customer
   |
   +-- Orders
   +-- Invoices
   +-- Payments
   +-- Tickets
```

Or:

```text
Employee
   |
   +-- Department
   +-- Projects
   +-- Attendance
```

The Relationship Engine provides the foundation for connecting dynamic business records.

Planned relationship patterns include:

* One-to-one
* One-to-many
* Many-to-many
* Related record lookup
* Relationship validation
* Relationship-aware APIs

---

# 4. Workflow Engine

The Workflow Engine is the main automation foundation of Phase 4.

A workflow consists of:

```text
Workflow
   |
   +-- Steps
   |
   +-- Transitions
   |
   +-- Conditions
   |
   +-- Actions
   |
   +-- Instances
   |
   +-- History
```

Example:

```text
Invoice Created
       |
       v
Check Amount
       |
       +---- Amount <= ₹50,000
       |             |
       |             v
       |        Manager Approval
       |
       +---- Amount > ₹50,000
                     |
                     v
               Finance Approval
                     |
                     v
                 Completed
```

---

# 5. Workflow Conditions

Transitions can evaluate conditions against dynamic record data.

Supported condition concepts include:

```text
equals
not_equals
greater_than
greater_than_or_equal
less_than
less_than_or_equal
contains
is_true
is_false
```

Example:

```text
invoice_amount > 50000
```

can determine whether a workflow transition is allowed.

Conditions are evaluated against the current `EntityRecord`.

---

# 6. Workflow Triggers

Workflow triggers connect business events to workflow execution.

Supported record events:

```text
record_created
record_updated
record_deleted
```

The event flow is:

```text
EntityRecord
     |
     v
Record Service
     |
     v
Record Event
     |
     v
Workflow Dispatcher
     |
     v
Matching Workflow Trigger
     |
     v
Workflow Instance
```

Trigger processing is designed to be isolated so that one broken workflow does not stop unrelated business operations.

---

# 7. Event Dispatcher

The event dispatcher:

1. Receives a record event.
2. Finds active workflow triggers.
3. Filters by event type.
4. Filters by entity.
5. Evaluates trigger configuration.
6. Starts the matching workflow.
7. Creates workflow history.
8. Writes audit information.
9. Isolates individual trigger failures.

This creates the foundation for event-driven business automation.

---

# 8. Workflow Actions

Transitions can execute actions.

Action execution supports:

```text
Workflow Transition
       |
       v
Action
       |
       +-- Synchronous execution
       |
       +-- Asynchronous execution
       |
       +-- Webhook
       |
       +-- Retry
       |
       +-- Execution History
```

Actions have persistent execution records.

Each execution can track:

* Status
* Started time
* Completed time
* Error
* Result
* Retry count
* Maximum retries
* Next retry time
* Last retry time
* Queue time
* Claim time
* Worker ID

---

# 9. Webhook Engine

Workflow actions can send HTTP webhooks.

Supported methods include:

```text
POST
PUT
PATCH
```

Webhook execution includes:

* Timeout protection
* Response capture
* HTTP error handling
* URL validation
* Host validation
* Private/local network protection
* Redirect protection
* Payload size protection
* Idempotency key
* Persistent execution history

Webhook payload size is limited to:

```text
256 KB
```

The platform also prevents webhook requests from targeting private/local network addresses.

---

# 10. Retry Engine

Failed workflow actions can be retried.

The execution system tracks:

```text
retry_count
max_retries
next_retry_at
last_retry_at
```

Retry scheduling uses exponential backoff.

The same execution record is reused so the complete execution lifecycle remains traceable.

---

# 11. DB-backed Async Queue

IndusCMS currently uses a database-backed queue instead of requiring Celery for workflow action processing.

An asynchronous action follows:

```text
Workflow Transition
        |
        v
Create Execution
        |
        v
pending
        |
        v
DB Queue
        |
        v
Workflow Worker
        |
        v
running
        |
        +------ success
        |
        +------ failed
        |
        +------ retry
```

This gives the project a simple local-first worker architecture while keeping the option of replacing the queue infrastructure later.

---

# 12. Workflow Worker

A Django management command is available for workflow processing.

Conceptually:

```bash
python manage.py workflow_worker
```

One-shot processing:

```bash
python manage.py workflow_worker --once
```

The worker supports:

* Pending execution discovery
* Execution claiming
* Worker identification
* Stale execution recovery
* Action processing
* Success handling
* Failure handling
* Retry scheduling
* Configurable limits
* Polling

---

# 13. Workflow Engine Operations

The workflow engine currently provides:

### Transition selection

Selects the first active transition whose conditions match the current record.

### Advance workflow

Moves an active workflow instance to the selected transition's target step.

### Completion

If the target step is final:

```text
active → completed
```

### Waiting state

If no transition currently matches:

```text
active → waiting for matching transition
```

The instance remains active rather than being incorrectly completed.

### Cancellation

```text
active → cancelled
```

### Resume

```text
cancelled → active
```

### History

Workflow state changes create persistent history entries.

### Audit

Important workflow operations are recorded through the audit system.

---

# 14. Workflow History

Every important workflow transition can be represented through history.

Example:

```text
Created
   |
   v
Draft
   |
   v
Submitted
   |
   v
Manager Approval
   |
   v
Finance Approval
   |
   v
Completed
```

History provides the foundation for:

* Timeline views
* Workflow debugging
* Compliance
* Auditing
* Reporting
* Future analytics

---

# 15. Audit System

IndusCMS maintains audit information for important business and workflow operations.

Examples:

```text
business.created
workflow.instance.started
workflow.instance.transitioned
workflow.instance.cancelled
workflow.instance.resumed
workflow.action.failed
workflow.action.retry_failed
```

Audit logs provide traceability across the platform.

---

# Phase History

## Phase 1 — Core CMS Foundation

Completed:

* Django project setup
* Core application
* Homepage
* Django Admin
* Health endpoint
* Environment configuration
* SQLite development database
* PostgreSQL-ready configuration
* Gunicorn/WSGI foundation
* WhiteNoise
* Deployment configuration
* GitHub repository

---

# Phase 2 — Business & Tenant Foundation

Completed:

* Business model
* Business settings
* Memberships
* Roles
* Permissions
* Permission service
* Role seeding
* Audit logging
* Business onboarding
* Django Admin integration

---

# Phase 3 — Dynamic Entity Engine

Completed foundation for:

* Entity definitions
* Field definitions
* Dynamic records
* Validation
* Dynamic CRUD
* Search
* Sorting
* Pagination
* Soft deletion
* Relationships
* Permission checks
* Audit logging
* Dynamic forms
* Dynamic tables

---

# Phase 4 — Workflow & Automation Engine

## Phase 4.1

Completed:

* Workflow definitions
* Workflow steps
* Initial steps
* Final steps
* Workflow transitions
* Workflow instances
* Workflow permissions
* Workflow state changes
* Workflow audit events

## Phase 4.2

Completed:

* Workflow history
* Workflow timeline foundation
* Workflow management APIs
* Workflow update API
* Workflow deactivation
* Workflow deletion protection
* Step listing
* Transition listing
* Instance listing
* Instance history API
* Management services

## Phase 4.3

Completed:

* Workflow conditions
* Transition condition evaluation
* Numeric comparisons
* Boolean conditions
* String conditions
* Conditional transition selection

## Phase 4.4

Completed:

* Record event generation
* Record-created triggers
* Record-updated triggers
* Record-deleted triggers
* Workflow trigger dispatcher
* Trigger filtering
* Trigger configuration
* Failure isolation
* Workflow trigger audit

## Phase 4.4D

Completed:

* Persistent action execution model
* Execution status
* Execution result
* Error tracking
* Retry metadata
* Execution APIs

## Phase 4.4E/F/H

Completed:

* Webhook actions
* HTTP execution
* Webhook timeout handling
* Payload limits
* SSRF protection
* Private network protection
* Redirect protection
* Idempotency keys
* Retry scheduling
* Execution retry APIs

## Phase 4.4G

Completed:

* DB-backed async queue
* Execution claiming
* Worker identity
* Stale execution recovery
* Django workflow worker
* Async transition actions

## Phase 4.5

Completed:

* Transition selection
* Conditional advancement
* Workflow completion
* Workflow waiting behavior
* Workflow cancellation
* Workflow resume
* Workflow history
* Workflow audit

---

# Current Test Status

The complete local suite currently reports:

```text
223 tests
223 passed
0 failed
```

Example:

```text
Ran 223 tests in approximately 107 seconds

OK
```

The workflow failure-isolation test intentionally generates an error for a broken workflow configuration. That error is logged as part of the test and does not represent a failed test.

---

# Technology Stack

## Backend

* Python 3
* Django
* Django REST Framework

## Database

Development:

```text
SQLite
```

Production-ready target:

```text
PostgreSQL
```

## Current Architecture

```text
Django Modular Monolith
```

## Future Infrastructure

Potential production components:

```text
PostgreSQL
Redis
Object Storage
Docker
Reverse Proxy
Background Workers
Monitoring
CI/CD
```

---

# Planned Frontend

The backend foundation is being developed first.

Future frontend:

```text
Next.js
React
TypeScript
Tailwind CSS
shadcn/ui
```

The frontend will eventually provide:

* Business dashboard
* Entity builder
* Dynamic forms
* Dynamic tables
* Workflow designer
* Workflow monitoring
* Action execution dashboard
* Audit timeline
* Reports
* Industry dashboards

---

# Planned API Layer

The API Engine will evolve toward:

* REST APIs
* Authentication
* API keys
* Token-based access
* Webhooks
* Import/export
* External integrations
* Rate limiting
* API documentation
* Integration management

---

# Planned Plugin Engine

Future plugins may provide:

```text
Plugin
   |
   +-- Models
   +-- Entities
   +-- APIs
   +-- Permissions
   +-- Workflows
   +-- Actions
   +-- Reports
   +-- UI
```

Possible plugins:

* Payment Gateway
* WhatsApp
* Email
* SMS
* GST
* Tally
* Accounting
* Shipping
* Maps
* AI
* CRM
* HR
* Inventory

---

# Industry Template Engine

The long-term goal is to allow an industry to be represented as a reusable package.

Example:

```text
Restaurant Template
       |
       +-- Customer
       +-- Table
       +-- Menu
       +-- Order
       +-- Payment
       +-- Staff
       +-- Inventory
       +-- Reports
       +-- Workflows
```

Another:

```text
Security Agency Template
       |
       +-- Client
       +-- Guard
       +-- Site
       +-- Shift
       +-- Attendance
       +-- Salary
       +-- Incident
       +-- Compliance
       +-- Reports
```

Another:

```text
School Template
       |
       +-- Student
       +-- Teacher
       +-- Class
       +-- Attendance
       +-- Exam
       +-- Fee
       +-- Result
       +-- Parent
       +-- Reports
```

Templates should eventually combine:

* Entities
* Fields
* Relationships
* Forms
* Views
* Dashboards
* Menus
* Workflows
* Reports
* Permissions
* Automation

---

# Potential Applications

IndusCMS can eventually become the foundation for applications such as:

### CRM

```text
Lead → Qualification → Sales → Customer
```

### HR

```text
Employee → Leave → Approval → Payroll
```

### Inventory

```text
Purchase → Stock → Sale → Reorder
```

### Logistics

```text
Order → Dispatch → Vehicle → Delivery → Proof
```

### Security

```text
Client → Site → Guard → Shift → Attendance → Incident
```

### School

```text
Student → Attendance → Exam → Result → Fee
```

### Service Business

```text
Customer → Ticket → Assignment → Field Visit → Completion
```

### Booking

```text
Customer → Booking → Approval → Payment → Completion
```

---

# Example Workflow

A future invoice approval workflow could look like:

```text
Invoice Created
      |
      v
Check Invoice Amount
      |
      +---- <= ₹50,000
      |          |
      |          v
      |     Manager Approval
      |
      +---- > ₹50,000
                 |
                 v
           Finance Approval
                 |
                 v
              Approved
                 |
                 v
           Send Webhook
                 |
                 v
             Completed
```

The platform therefore moves toward:

```text
Record
   ↓
Event
   ↓
Trigger
   ↓
Condition
   ↓
Transition
   ↓
Action
   ↓
Async Worker
   ↓
External System
   ↓
Audit
```

---

# Development Philosophy

IndusCMS is being developed around several principles.

## Reusable infrastructure

Do not rebuild the same business backend for every industry.

## Configuration over duplication

Prefer configurable entities, fields and workflows where practical.

## Modular architecture

Keep platform engines separated by clear service boundaries.

## Local-first development

The system should remain usable and testable locally before introducing production infrastructure.

## Safe automation

Workflow failures should be isolated and observable.

## Persistent execution history

Important asynchronous operations should not disappear into logs only.

## Production-oriented design

Security, retries, idempotency, auditability and failure handling are considered during foundation development rather than added only at the end.

---

# Development

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Run Django checks:

```bash
python manage.py check
```

Run the development server:

```bash
python manage.py runserver
```

Run all tests:

```bash
python manage.py test --verbosity 1
```

Run workflow engine tests:

```bash
python manage.py test core.tests.test_workflow_engine --verbosity 1
```

Run workflow worker once:

```bash
python manage.py workflow_worker --once
```

Run the worker continuously:

```bash
python manage.py workflow_worker
```

---

# Project Structure

The project is evolving toward the following structure:

```text
IndusCMS/
|
├── core/
│   ├── api/
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── workflow_action_execution_views.py
│   │
│   ├── management/
│   │   └── commands/
│   │       └── workflow_worker.py
│   │
│   ├── migrations/
│   │
│   ├── services/
│   │   ├── audit.py
│   │   ├── entity.py
│   │   ├── record.py
│   │   ├── workflow.py
│   │   ├── workflow_action.py
│   │   ├── workflow_condition.py
│   │   ├── workflow_engine.py
│   │   ├── workflow_event.py
│   │   └── workflow_worker.py
│   │
│   ├── tests/
│   │   ├── test_workflow_actions.py
│   │   ├── test_workflow_api.py
│   │   ├── test_workflow_conditions.py
│   │   ├── test_workflow_engine.py
│   │   ├── test_workflow_management_43c.py
│   │   └── test_workflow_triggers.py
│   │
│   └── models.py
│
├── templates/
│   └── core/
│       └── home.html
│
├── manage.py
├── requirements.txt
└── README.md
```

---

# Roadmap

## Completed

```text
✓ Core CMS Foundation
✓ Business/Tenant Foundation
✓ Dynamic Entity Engine
✓ Relationships Foundation
✓ Workflow Foundation
✓ Workflow Management
✓ Workflow Conditions
✓ Workflow Triggers
✓ Event Dispatcher
✓ Workflow Actions
✓ Webhooks
✓ Retry Engine
✓ Execution History
✓ DB-backed Async Queue
✓ Workflow Worker
✓ Workflow Engine
✓ Cancellation / Resume
✓ Audit Foundation
```

## Next

Planned areas include:

```text
→ Advanced API Engine
→ Authentication / API Keys
→ Import / Export
→ Advanced Relationship APIs
→ Workflow designer
→ Notification actions
→ Scheduled workflows
→ More action types
→ Plugin Engine
→ Industry Template Engine
→ Dashboard Engine
→ Reporting Engine
→ Frontend Application
```

---

# Long-Term Platform

The intended architecture is:

```text
                     INDUSTRY APPLICATIONS
                              |
          +-------------------+-------------------+
          |                   |                   |
        CRM                 ERP               Industry Apps
          |                   |                   |
          +-------------------+-------------------+
                              |
                         IndusCMS Core
                              |
       +----------+-----------+-----------+----------+
       |          |           |           |          |
   Business   Entities   Workflow      API       Plugins
       |          |           |           |          |
       +----------+-----------+-----------+----------+
                              |
                         Infrastructure
                              |
                   PostgreSQL / Redis / Storage
```

The goal is not simply to build another CMS.

The goal is to build a reusable **business application operating layer**.

---

# License

IndusCMS is currently under active development.

Licensing and distribution terms will be finalized as the platform matures.

---

# Project

**IndusCMS**

Industry-first CMS & Business Application Platform.

Built with Django.

```text
Build once.
Configure for industries.
Reuse everywhere.
```
