# IndusCMS Project

## Project Overview

IndusCMS is an industry-first CMS and business platform built with Django.

The goal is to create one reusable platform from which different
industry-specific business applications can be built.

Instead of developing completely separate software for every industry,
IndusCMS is designed around reusable engines, dynamic entities,
permissions, workflows, APIs and industry templates.

## Core Idea

One Platform
+
Reusable Business Engines
+
Dynamic Entities
+
Industry Templates
=
Multiple Business Applications

## Product Vision

IndusCMS is designed to go beyond a traditional CMS.

A traditional CMS mainly manages content such as:

- Pages
- Posts
- Media
- Menus
- Themes

IndusCMS is additionally designed to manage:

- Businesses
- Users
- Roles
- Permissions
- Customers
- Products
- Transactions
- Workflows
- Dynamic business data
- Industry-specific applications

## Platform Architecture

IndusCMS consists of reusable platform engines:

- CMS Engine
- Business Engine
- Dynamic Entity Engine
- Workflow Engine
- API Engine
- Plugin Engine
- Industry Template Engine

Long-term architecture:

IndusCMS
|
+-- CMS Engine
|
+-- Business Engine
|
+-- Dynamic Entity Engine
|
+-- Workflow Engine
|
+-- API Engine
|
+-- Plugin Engine
|
+-- Industry Templates

## Technology Stack

### Backend

- Python
- Django 5.x
- Django REST Framework

### Database

Development:

- SQLite

Production:

- PostgreSQL

Dynamic business data:

- Django JSONField
- PostgreSQL JSONB strategy

### Planned Infrastructure

- Redis
- Celery
- S3-compatible storage
- Docker
- GitHub Actions

### Future Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui

## Architecture Strategy

The initial application architecture is a modular monolith.

Microservices are intentionally not being introduced at the beginning.

The priority is to build a stable reusable core first.

# Phase 1 — Core CMS Foundation

Status: COMPLETE

Implemented:

- Django project
- Core application
- Home page
- Django admin
- Health endpoint
- Environment configuration
- SQLite development database
- PostgreSQL-ready configuration
- Django REST Framework
- Gunicorn/WSGI
- WhiteNoise
- ALLOWED_HOSTS configuration
- GitHub repository
- Deployment preparation
- README documentation

# Phase 2 — Business / Tenant Foundation

Status: COMPLETE

Implemented models:

### Business

Represents a business or organization.

### Role

Business-specific roles.

Examples:

- Owner
- Admin
- Manager
- Staff

### Permission

Global permission definitions.

Actions:

- view
- create
- update
- delete
- manage

### RolePermission

Connects permissions to roles.

### Membership

Connects users to businesses and roles.

### BusinessSettings

Business-level configuration including:

- Currency
- Timezone
- Date format
- Logo

### AuditLog

Records important business actions.

Audit information includes:

- Business
- User
- Action
- Resource
- Object ID
- IP address
- Metadata
- Timestamp

## Business Services

Implemented:

- Business onboarding
- Owner role creation
- Permission setup
- Membership checks
- Permission checks
- Audit logging

Service files:

core/services/business.py
core/services/permissions.py
core/services/audit.py

# Phase 3 — Dynamic Entity Engine

Status: IN PROGRESS

The Dynamic Entity Engine is one of the core technologies of IndusCMS.

It allows businesses to define their own data structures without
creating a new Django model for every business object.

Examples:

- Customer
- Product
- Vehicle
- Student
- Patient
- Booking
- Property
- Guard
- Invoice

## EntityDefinition

Status: COMPLETE

Defines a business entity.

Implemented:

- UUID ID
- Business relationship
- Name
- Slug
- Description
- Active status
- Created timestamp
- Updated timestamp
- Business + slug uniqueness

## FieldDefinition

Status: COMPLETE

Defines fields belonging to a dynamic entity.

Supported field types:

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

Fields support:

- Name
- Slug
- Field type
- Required
- Unique
- Default value
- Choices
- Position
- Active status
- System field flag
- Timestamps

## EntityRecord

Status: COMPLETE

Stores actual dynamic entity data.

Example:

{
    "name": "Rahul Kumar",
    "email": "rahul@example.com",
    "phone": "9876543210"
}

Entity records support:

- Dynamic JSON data
- Created by user
- Created timestamp
- Updated timestamp
- Soft delete

## Dynamic Data Validation

Status: COMPLETE

Records are validated against their entity field definitions.

Validation includes:

- Required fields
- Default values
- Unknown field detection
- Text validation
- Number validation
- Decimal validation
- Boolean validation
- Date validation
- Datetime validation
- Email validation
- URL validation
- Choice validation
- JSON validation

## Entity Permissions

Current permissions:

- entity.view
- entity.create
- entity.update
- entity.delete
- entity.manage

Security checks include:

1. Authentication
2. Active business membership
3. Required permission
4. Correct business ownership

# Entity Management APIs

## Entity Creation API

Status: COMPLETE

POST /api/entities/

Capabilities:

- Create entity
- Generate slug
- Validate name
- Check membership
- Check entity.create permission
- Prevent duplicate slugs
- Audit logging

## Entity List API

Status: COMPLETE

GET /api/entities/list/?business_id=<business_id>

Capabilities:

- Business filtering
- Active entity filtering
- Membership validation
- Permission validation
- Entity serialization

## Entity Detail API

Status: COMPLETE

GET /api/entities/<entity_id>/

Capabilities:

- Entity lookup
- Active entity validation
- Active business validation
- Membership validation
- Permission validation

## Entity Update API

Status: IN PROGRESS

Endpoint:

PATCH /api/entities/<entity_id>/

Allowed fields:

- name
- slug
- description

The service layer has been implemented.

The service provides:

- Authentication check
- Business membership check
- entity.manage permission
- Name validation
- Slug generation
- Duplicate slug protection
- Description update
- Audit logging
- Transaction support

Remaining work:

- Successful update test
- Partial update test
- Permission failure test
- Non-member test
- Other business test
- Inactive entity test
- Nonexistent entity test
- Duplicate slug test
- Invalid name test
- Invalid slug test
- Unsupported field test
- Audit log test

The feature will be marked COMPLETE only after the tests pass.

## Entity Field Creation API

Status: COMPLETE

POST /api/entity-fields/

Capabilities:

- Create dynamic field
- Validate entity
- Validate field name
- Validate field slug
- Validate field type
- Check membership
- Check entity.manage permission
- Audit logging

# Entity Record APIs

## Record Creation

Status: COMPLETE

POST /api/entity-records/

Records are validated against the entity's active field definitions.

## Record List

Status: COMPLETE

GET /api/entity-records/?entity_id=<entity_id>

Pagination includes:

- count
- page
- page_size
- total_pages
- next_page
- previous_page
- results

Maximum page size:

100

Soft-deleted records are excluded.

## Record Detail

Status: COMPLETE

GET /api/entity-records/<record_id>/

Supports:

- Record lookup
- Active entity validation
- Active business validation
- Soft-delete filtering
- Permission checks

## Record Update

Status: COMPLETE

PATCH /api/entity-records/<record_id>/

Updated records are validated against the current field definitions.

## Record Delete

Status: COMPLETE

DELETE /api/entity-records/<record_id>/

Deletion uses soft delete.

Fields:

- is_deleted
- deleted_at
- deleted_by

Deleted records are hidden from normal list and detail APIs.

Audit logging is performed.

# Testing

Django's built-in test framework is currently being used.

Pytest is not required at this stage.

Entity API tests currently cover:

- Entity creation
- Entity listing
- Entity detail

Current result:

15 tests
15 passed

Command:

python manage.py test core.tests.test_entity_api -v 2

The broader project test suite previously reached:

53 tests
53 passed

## System Check

Current Django system check:

System check identified no issues (0 silenced).

Command:

python manage.py check

# Current Project Status

Phase 1
Core CMS Foundation
COMPLETE

Phase 2
Business / Tenant Foundation
COMPLETE

Phase 3
Dynamic Entity Engine
IN PROGRESS

Current active feature:

Entity Update API

## Current Milestone

Dynamic Entity Management API

Entity Model                 COMPLETE
Field Model                  COMPLETE
Record Model                 COMPLETE

Entity Creation API          COMPLETE
Entity List API              COMPLETE
Entity Detail API            COMPLETE
Entity Update API            IN PROGRESS

Field Creation API           COMPLETE

Record Create API            COMPLETE
Record List API              COMPLETE
Record Detail API            COMPLETE
Record Update API            COMPLETE
Record Delete API            COMPLETE

# Planned Dynamic Entity Features

After Entity Update API:

- Entity deactivation
- Entity deletion
- Field list API
- Field detail API
- Field update API
- Field deletion API
- Dynamic forms
- Dynamic table views
- Dynamic search
- Dynamic filtering
- Dynamic sorting
- Entity relationships

# Future Business Engines

Potential reusable engines:

- CRM
- HR
- Inventory
- Sales
- Purchase
- Accounting
- Asset Management
- Project Management
- Fleet
- Booking
- Ticketing
- Workflow
- Document Management
- Compliance
- Field Service
- Subscription
- Membership
- Property
- Manufacturing
- Logistics

# Industry Templates

Potential industry templates:

- Restaurant
- School
- Retail
- Logistics
- Security Company
- Service Business
- Hospital
- Property Management
- Manufacturing
- Professional Services

A template may eventually contain:

- Entities
- Fields
- Relationships
- Forms
- Views
- Menus
- Dashboard
- Workflows
- Reports
- Permissions
- Automation
- Theme configuration
- API configuration

# Deployment Strategy

IndusCMS should remain portable.

Potential deployment environments:

- VPS
- Cloud servers
- Wasmer
- Faable
- Docker
- PostgreSQL hosting

The platform should not depend on a single hosting provider.

# Repository

GitHub:

https://github.com/jitenkr2030/IndusCMS

# Development Rule

One feature at a time.

START FEATURE
    ↓
IMPLEMENT
    ↓
TEST
    ↓
FIX
    ↓
REGRESSION TEST
    ↓
MARK COMPLETE
    ↓
START NEXT FEATURE

The objective is to build a stable reusable platform rather than
rapidly accumulate unfinished features.

# Long-Term Product Architecture

IndusCMS
|
+-- CMS Engine
|
+-- Business Engines
|
+-- Dynamic Entity Engine
|
+-- Workflow Engine
|
+-- API Engine
|
+-- Plugin Engine
|
+-- Industry Templates
|
+-- Industry-specific Applications

# Project Principle

IndusCMS should grow as a platform.

The priority is to establish a strong reusable foundation:

Stable Core
    ↓
Business Foundation
    ↓
Dynamic Data
    ↓
Permissions
    ↓
Audit
    ↓
APIs
    ↓
Workflows
    ↓
Plugins
    ↓
Industry Templates
