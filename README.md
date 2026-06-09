# Course Enrollment System

> Django + DRF + PostgreSQL + JWT
> Backend API with a single browser UI for city selection

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Phase 1 — Project Setup & Infrastructure](#3-phase-1--project-setup--infrastructure)
4. [Phase 2 — Location API Integration](#4-phase-2--location-api-integration)
5. [Phase 3 — Course Management](#5-phase-3--course-management)
6. [Phase 4 — Enrollment System](#6-phase-4--enrollment-system)
7. [Phase 5 — Polish, Testing & Docs](#7-phase-5--polish-testing--docs)
8. [Production File Structure](#8-production-file-structure)
9. [Data Models](#9-data-models)
10. [API Reference](#10-api-reference)
11. [Enrollment Validation Rules](#11-enrollment-validation-rules)
12. [Audit Logging](#12-audit-logging)
13. [Access Control Matrix](#13-access-control-matrix)
14. [Key Packages](#14-key-packages)
15. [Environment Variables](#15-environment-variables)

---

## 1. Project Overview

A backend system where **instructors** create and manage courses, and **students** browse and enroll in them. All features exposed via REST APIs (testable through Swagger), except for a single browser-based city selector UI.

### Functional Summary

| Actor | Can Do |
|---|---|
| Student | Register, view all courses, enroll, cancel enrollment, view own enrollments |
| Instructor | Register, create/update own courses, view own courses only, view enrollments for own courses |

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 5.x + Django REST Framework |
| Database | PostgreSQL 15+ |
| Authentication | JWT via `djangorestframework-simplejwt` |
| API Docs | Swagger UI via `drf-spectacular` |
| Filtering | `django-filter` |
| Testing | `pytest-django` + `factory-boy` |
| Config Management | `python-decouple` (.env files) |

---

## 3. Phase 1 — Project Setup & Infrastructure

> **Status:** `[x] Done`
> **Estimated time: ~2 days**

### Goals
Stand up a runnable Django project with auth, database, and Swagger working end-to-end.

### Tasks

#### Environment
- [x] Django project init with DRF installed
- [x] PostgreSQL connection configured
- [x] `.env` management with `python-decouple`
- [x] Separate `dev.py` / `prod.py` settings files inheriting from `base.py`

#### Custom User Model
- [x] `User` model with `role` field (`student` / `instructor`)
- [x] Custom `UserManager`
- [x] UUID primary keys
- [x] Email as username field

#### Authentication
- [x] `POST /api/auth/register/` — create account (role specified at registration)
- [x] `POST /api/auth/login/` — returns access + refresh tokens
- [x] `POST /api/auth/token/refresh/` — refresh access token
- [x] `POST /api/auth/logout/` — blacklist refresh token
- [x] `IsStudent` and `IsInstructor` custom permission classes

#### API Docs
- [x] `drf-spectacular` installed and configured
- [x] Swagger UI available at `/api/docs/`
- [x] OpenAPI schema at `/api/schema/`

### Deliverable
Runnable Django project with JWT auth, Postgres connected, Swagger UI accessible, and logout working.

### Quick Start (Phase 1)

See [Full Setup & Run](#full-setup--run) below for the complete guide.

```powershell
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements\dev.txt

# 3. Copy and edit environment (set your PostgreSQL password)
copy .env.example .env

# 4. Create the database in PostgreSQL, then run migrations
python manage.py migrate

# 5. Start the dev server
python manage.py runserver
```

Swagger UI: http://127.0.0.1:8000/api/docs/

---

## Full Setup & Run

### Prerequisites

- Python 3.12+
- PostgreSQL 15+
- [Country State City API](https://countrystatecity.in/) key (for location endpoints)

### 1. Clone and create virtual environment

```powershell
cd D:\COURSE-TASK
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements\dev.txt
```

### 2. Configure environment

```powershell
copy .env.example .env
```

Edit `.env` — set at minimum:

| Variable | Example |
|---|---|
| `SECRET_KEY` | random secret string |
| `DB_PASSWORD` | your PostgreSQL password |
| `LOCATION_API_KEY` | your CSC API key |

### 3. Create database and migrate

```sql
-- in psql or pgAdmin
CREATE DATABASE course_enrollment;
```

```powershell
python manage.py migrate
python manage.py createsuperuser   # optional — for /api/audit/ and Django Admin
```

### 4. Run the server

```powershell
python manage.py runserver
```

| URL | Purpose |
|---|---|
| http://127.0.0.1:8000/api/docs/ | Swagger UI |
| http://127.0.0.1:8000/location/select/ | City selector UI |
| http://127.0.0.1:8000/api/audit/ | Audit log (admin JWT required) |

### 5. Run tests

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.test"
pytest
```

Tests use SQLite (`config/settings/test.py`) — no PostgreSQL required for the test suite.

### Typical API flow

1. `POST /api/auth/register/` — register as `student` or `instructor`
2. `POST /api/auth/login/` — copy the `access` token
3. In Swagger, click **Authorize** → `Bearer <access-token>`
4. **Instructor:** `POST /api/courses/` with location fields
5. **Student:** `GET /api/courses/` → `POST /api/enrollments/`
6. **Admin:** `GET /api/audit/` to review audit trail

---

## 4. Phase 2 — Location API Integration

> **Status:** `[x] Done`
> **Estimated time: ~1 day**

### Goals
Integrate an external location API and expose proxy endpoints. Build the required city-selector browser UI.

### Tasks

#### Backend
- [x] `location/services.py` — wraps external location API calls (Country / State / City)
- [x] `GET /api/location/countries/` — proxy endpoint
- [x] `GET /api/location/states/?country=IN` — filtered by country code
- [x] `GET /api/location/cities/?country=IN&state=GJ` — filtered by country + state code
- [x] Response caching (Django's cache framework or Redis) to avoid hammering the upstream API
- [x] Validate that `country`, `state`, `city` values submitted on course creation actually exist in the Location API

#### Browser UI (City Selector)
- [x] Single `city_selector.html` page served via Django `TemplateView`
- [x] Accessible at `GET /location/select/`
- [x] Three cascading `<select>` dropdowns: Country → State → City
- [x] Vanilla JS fetches from the proxy endpoints above
- [x] On city selection, the selected location values are displayed/stored

### Deliverable
Working cascading dropdown UI + all three location proxy endpoints + location validation on course write.

---

## 5. Phase 3 — Course Management

> **Status:** `[x] Done`
> **Estimated time: ~2 days**

### Goals
Instructors can create and manage courses. Students can browse and filter courses. Access is role-scoped.

### Tasks

#### Models
- [x] `Course` model with all required fields (see [Data Models](#9-data-models))
- [x] `is_active` BooleanField on `Course` (default: True) for soft-close
- [x] Location fields embedded directly on `Course` (country, state, city stored as strings)
- [x] Migrations

#### Instructor APIs
- [x] `POST /api/courses/` — create course (instructor only); validates location values against Location API
- [x] `PATCH /api/courses/{id}/` — update own course only
- [x] `GET /api/courses/mine/` — list instructor's own courses
- [x] `GET /api/courses/{id}/` — retrieve own course by ID (returns 404 for other instructors' courses)
- [x] `GET /api/courses/{id}/enrollments/` — view enrollments for own course
- [x] Object-level `get_queryset` scoping: instructors only see their own courses in all course endpoints

#### Student APIs
- [x] `GET /api/courses/` — list all available courses
- [x] `GET /api/courses/{id}/` — retrieve any single course by ID
- [x] Filter by `country`, `state`, `city`, `start_datetime` query params via `django-filter`

#### Audit Hooks
- [x] Django signal `post_save` on `Course` (created=True) → log `"course_created"`
- [x] Django signal `post_save` on `Course` (created=False) → log `"course_updated"`

### Deliverable
Full course CRUD with role-based access control, location validation, and audit logging wired up.

---

## 6. Phase 4 — Enrollment System

> **Status:** `[x] Done`
> **Estimated time: ~2 days**

### Goals
Students can enroll in courses. All three enrollment rules enforced atomically.

### Tasks

#### Model
- [x] `Enrollment` model with `student`, `course`, `status`, `enrolled_at`, `cancelled_at`
- [x] Partial unique index instead of `unique_together`: `UniqueConstraint(fields=['student','course'], condition=Q(status='active'), name='unique_active_enrollment')` — allows re-enrollment after cancellation

#### Validation (`enrollments/validators.py`)
- [x] **Duplicate check** — student already has an active enrollment in this course
- [x] **Capacity check** — count active enrollments vs `course.max_capacity`
- [x] **Schedule conflict** — query student's active enrollments, check time overlap using: `existing.start_datetime < new.end_datetime AND existing.end_datetime > new.start_datetime`
- [x] All checks run inside `select_for_update()` atomic transaction to prevent race conditions

#### APIs
- [x] `POST /api/enrollments/` — enroll (student only, validates all 3 rules)
- [x] `GET /api/enrollments/mine/` — student's own enrollments only; supports `?status=active|cancelled` filter
- [x] `DELETE /api/enrollments/{id}/` — cancel own enrollment (sets `status='cancelled'`, sets `cancelled_at=now()`)

#### Access Control
- [x] Students can only see and cancel their own enrollments
- [x] Instructors access enrollments only via `/api/courses/{id}/enrollments/` for their own courses

#### Audit Hooks
- [x] On `POST /api/enrollments/` success → log `"student_enrolled"` (triggered from view/serializer, not signal)
- [x] On `DELETE /api/enrollments/{id}/` → log `"enrollment_cancelled"` (triggered from view directly, not `post_save` signal — signal cannot reliably detect status transitions)

### Deliverable
Full enrollment lifecycle with all three validation rules enforced and correct access restrictions.

---

## 7. Phase 5 — Polish, Testing & Docs

> **Status:** `[x] Done`
> **Estimated time: ~2 days**

### Goals
Production-ready code: tested, documented, hardened.

### Tasks

#### Testing
- [x] `pytest-django` + `factory-boy` for fixtures
- [x] Unit tests for all three enrollment validation rules in isolation
- [x] Integration tests for full enrollment flow (enroll → conflict → cancel → re-enroll)
- [x] Permission boundary tests:
  - Student cannot access another student's enrollments
  - Instructor cannot retrieve another instructor's course by ID (expects 404)
  - Instructor cannot see enrollments for another instructor's course
- [x] Target: >80% coverage on `enrollments/` and `courses/` apps

#### Production Hardening
- [x] Custom DRF exception handler in `core/exceptions.py` — all errors return `{"error": "...", "detail": "..."}`
- [x] `StandardResultsPagination` on all list endpoints (page_size=20)
- [x] Throttle classes: `UserRateThrottle` on enrollment endpoints
- [x] Swagger schema annotations with `@extend_schema` on all viewsets, including role-split behaviour on `GET /api/courses/{id}/`
- [x] Read-only `GET /api/audit/` endpoint (admin-only) so audit trails can be verified without Django Admin

#### Documentation
- [x] Swagger examples for all endpoints
- [x] `README.md` finalised with setup instructions

### Deliverable
Production-ready, tested, fully documented API.

---

## 8. Production File Structure

```
course_enrollment/
│
├── config/                         # Django settings package
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                 # shared settings (installed apps, middleware, etc.)
│   │   ├── dev.py                  # DEBUG=True, console email, relaxed CORS
│   │   └── prod.py                 # ALLOWED_HOSTS, SSL, secure cookies
│   ├── urls.py                     # root URL conf
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   │
│   ├── accounts/                   # Custom user model + JWT auth
│   │   ├── migrations/
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── factories.py        # UserFactory (student/instructor)
│   │   │   └── test_auth.py
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── managers.py             # UserManager (email as username)
│   │   ├── models.py               # User model with role field
│   │   ├── permissions.py          # IsStudent, IsInstructor
│   │   ├── serializers.py          # RegisterSerializer, LoginSerializer
│   │   ├── urls.py
│   │   └── views.py                # RegisterView, TokenObtainView, LogoutView
│   │
│   ├── location/                   # Location API proxy
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   └── test_location.py
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── serializers.py          # CountrySerializer, StateSerializer, CitySerializer
│   │   ├── services.py             # calls external location API, caches responses, validates values
│   │   ├── urls.py
│   │   └── views.py                # CountryListView, StateListView, CityListView
│   │
│   ├── courses/                    # Course management
│   │   ├── migrations/
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── factories.py        # CourseFactory
│   │   │   └── test_courses.py
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── filters.py              # CourseFilter (country, state, city, start_datetime)
│   │   ├── models.py               # Course model (with is_active field)
│   │   ├── serializers.py          # CourseSerializer, CourseCreateSerializer
│   │   ├── signals.py              # post_save → audit log (course_created / course_updated)
│   │   ├── urls.py
│   │   └── views.py                # CourseViewSet (get_queryset scoped by role)
│   │
│   ├── enrollments/                # Enrollment lifecycle
│   │   ├── migrations/
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── factories.py        # EnrollmentFactory
│   │   │   ├── test_enrollment_rules.py   # duplicate / capacity / schedule
│   │   │   └── test_permissions.py
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py               # Enrollment model (with cancelled_at field)
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── validators.py           # check_duplicate, check_capacity, check_schedule_conflict
│   │   └── views.py                # EnrollmentViewSet (audit logged here, not via signal)
│   │
│   └── audit/                      # Audit logging
│       ├── migrations/
│       ├── __init__.py
│       ├── admin.py                # Read-only AuditLog admin
│       ├── apps.py
│       ├── models.py               # AuditLog model
│       ├── serializers.py
│       ├── urls.py                 # GET /api/audit/ (admin-only read endpoint)
│       ├── views.py                # AuditLogListView (IsAdminUser)
│       └── utils.py                # log_event(actor, action, target) helper
│
├── core/                           # Shared utilities (no models)
│   ├── __init__.py
│   ├── exceptions.py               # custom_exception_handler → {error, detail}
│   ├── mixins.py                   # TimestampMixin, UUIDMixin
│   └── pagination.py               # StandardResultsPagination (page_size=20)
│
├── templates/
│   └── city_selector.html          # The required browser UI (cascading dropdowns)
│
├── static/
│   └── city_selector.js            # Vanilla JS for the dropdown logic
│
├── requirements/
│   ├── base.txt                    # production dependencies
│   ├── dev.txt                     # base + pytest, factory-boy, faker
│   └── prod.txt                    # base + gunicorn, sentry-sdk
│
├── manage.py
├── pytest.ini
├── .env.example
├── .gitignore
└── README.md
```

---

## 9. Data Models

### User

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDField | Primary key |
| `email` | EmailField | Unique, used as username |
| `password` | CharField | Hashed by Django |
| `role` | CharField | Choices: `student`, `instructor` |
| `first_name` | CharField | |
| `last_name` | CharField | |
| `is_active` | BooleanField | Default: True |
| `created_at` | DateTimeField | auto_now_add |

### Course

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDField | Primary key |
| `instructor` | ForeignKey → User | `on_delete=PROTECT` |
| `title` | CharField | max_length=255 |
| `description` | TextField | |
| `max_capacity` | PositiveIntegerField | |
| `start_datetime` | DateTimeField | |
| `end_datetime` | DateTimeField | |
| `country` | CharField | Validated against Location API |
| `state` | CharField | Validated against Location API |
| `city` | CharField | Validated against Location API |
| `is_active` | BooleanField | Default: True; soft-close flag |
| `created_at` | DateTimeField | auto_now_add |
| `updated_at` | DateTimeField | auto_now |

### Enrollment

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDField | Primary key |
| `student` | ForeignKey → User | `on_delete=CASCADE` |
| `course` | ForeignKey → Course | `on_delete=CASCADE` |
| `status` | CharField | Choices: `active`, `cancelled` |
| `enrolled_at` | DateTimeField | auto_now_add |
| `cancelled_at` | DateTimeField | nullable; set on cancellation |

> **No `unique_together`** — use a partial `UniqueConstraint` instead:
> `UniqueConstraint(fields=['student','course'], condition=Q(status='active'), name='unique_active_enrollment')`
> This allows a student to re-enroll in a course after cancelling.

### AuditLog

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDField | Primary key |
| `actor` | ForeignKey → User | nullable, `on_delete=SET_NULL` |
| `action` | CharField | Choices: `course_created`, `course_updated`, `student_enrolled`, `enrollment_cancelled` |
| `target_type` | CharField | `"Course"` or `"Enrollment"` |
| `target_id` | UUIDField | ID of the affected object |
| `metadata` | JSONField | Extra context (e.g. changed fields, course title) |
| `timestamp` | DateTimeField | auto_now_add |

---

## 10. API Reference

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Public | Create student or instructor account |
| `POST` | `/api/auth/login/` | Public | Returns access + refresh JWT tokens |
| `POST` | `/api/auth/token/refresh/` | Public | Refresh access token |
| `POST` | `/api/auth/logout/` | Required | Blacklist refresh token |

### Location

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/location/countries/` | Required | List all countries |
| `GET` | `/api/location/states/?country=IN` | Required | States for a country |
| `GET` | `/api/location/cities/?country=IN&state=GJ` | Required | Cities for a state |
| `GET` | `/location/select/` | Public | Browser city selector UI (HTML page) |

### Courses

| Method | Endpoint | Role | Description |
|---|---|---|---|
| `GET` | `/api/courses/` | Student | List all courses; filter by `country`, `state`, `city`, `start_datetime` |
| `POST` | `/api/courses/` | Instructor | Create a new course (location values validated against Location API) |
| `GET` | `/api/courses/{id}/` | Student / Instructor (owner) | Students can retrieve any course; instructors only their own (404 otherwise) |
| `PATCH` | `/api/courses/{id}/` | Instructor (owner) | Update own course only |
| `GET` | `/api/courses/mine/` | Instructor | List instructor's own courses |
| `GET` | `/api/courses/{id}/enrollments/` | Instructor (owner) | View enrollments for own course |

### Enrollments

| Method | Endpoint | Role | Description |
|---|---|---|---|
| `POST` | `/api/enrollments/` | Student | Enroll in a course (validates all 3 rules atomically) |
| `GET` | `/api/enrollments/mine/` | Student | View own enrollments; supports `?status=active\|cancelled` |
| `DELETE` | `/api/enrollments/{id}/` | Student (owner) | Cancel own enrollment; sets `cancelled_at` |

### Audit

| Method | Endpoint | Role | Description |
|---|---|---|---|
| `GET` | `/api/audit/` | Admin only | Read-only list of all audit log entries |

### Docs

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/docs/` | Public | Swagger UI |
| `GET` | `/api/schema/` | Public | Download OpenAPI schema |

---

## 11. Enrollment Validation Rules

All three rules are implemented in `apps/enrollments/validators.py` and called from the serializer's `validate()` method inside a `select_for_update()` atomic block.

### Rule 1 — No Duplicate Active Enrollment

```python
def check_duplicate(student, course):
    if Enrollment.objects.filter(student=student, course=course, status='active').exists():
        raise ValidationError("You are already enrolled in this course.")
```

> Note: uses `status='active'` so a student can re-enroll after cancellation.

### Rule 2 — Capacity Limit

```python
def check_capacity(course):
    active_count = Enrollment.objects.filter(course=course, status='active').count()
    if active_count >= course.max_capacity:
        raise ValidationError("This course has reached its maximum capacity.")
```

### Rule 3 — Schedule Conflict

```python
def check_schedule_conflict(student, new_course):
    """
    Overlap exists if:  existing.start < new.end  AND  existing.end > new.start
    """
    enrolled_courses = Course.objects.filter(
        enrollment__student=student,
        enrollment__status='active'
    )
    conflict = enrolled_courses.filter(
        start_datetime__lt=new_course.end_datetime,
        end_datetime__gt=new_course.start_datetime
    ).first()
    if conflict:
        raise ValidationError(
            f"Schedule conflict with '{conflict.title}' "
            f"({conflict.start_datetime} – {conflict.end_datetime})."
        )
```

### Atomic Execution

```python
# In EnrollmentSerializer.create():
with transaction.atomic():
    course = Course.objects.select_for_update().get(pk=course_id)
    check_duplicate(student, course)
    check_capacity(course)
    check_schedule_conflict(student, course)
    enrollment = Enrollment.objects.create(student=student, course=course)
return enrollment
```

---

## 12. Audit Logging

All audit events are written via `apps/audit/utils.py`:

```python
def log_event(actor, action, target):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target.__class__.__name__,
        target_id=target.pk,
        metadata={"title": str(target)},
    )
```

| Event | Trigger | Location |
|---|---|---|
| `course_created` | `post_save` on Course (`created=True`) | `apps/courses/signals.py` |
| `course_updated` | `post_save` on Course (`created=False`) | `apps/courses/signals.py` |
| `student_enrolled` | After `Enrollment.objects.create()` succeeds | `apps/enrollments/views.py` |
| `enrollment_cancelled` | After `enrollment.status = 'cancelled'` save | `apps/enrollments/views.py` |

> **Why views, not signals, for enrollment events?**
> A `post_save` signal cannot reliably detect a `status` transition from `active → cancelled`
> without comparing to the pre-save state. Triggering from the view is explicit and avoids that complexity.

---

## 13. Access Control Matrix

| Action | Student | Instructor (owner) | Instructor (other) |
|---|---|---|---|
| Register / Login / Logout | ✅ | ✅ | ✅ |
| View all courses (list) | ✅ | ❌ | ❌ |
| View own courses (list) | ❌ | ✅ | — |
| View single course by ID | ✅ (any) | ✅ (own only) | ❌ → 404 |
| Create course | ❌ | ✅ | ✅ |
| Update course | ❌ | ✅ | ❌ |
| Enroll in a course | ✅ | ❌ | ❌ |
| View own enrollments | ✅ | — | — |
| View other student's enrollments | ❌ | ❌ | ❌ |
| Cancel own enrollment | ✅ | — | — |
| View enrollments for own course | — | ✅ | ❌ |
| View enrollments for other's course | — | ❌ | ❌ |
| View audit log | ❌ | ❌ | ❌ (admin only) |

---

## 14. Key Packages

### `requirements/base.txt`

```
django>=5.0
djangorestframework>=3.15
psycopg2-binary>=2.9
djangorestframework-simplejwt>=5.3
drf-spectacular>=0.27
django-filter>=24.0
python-decouple>=3.8
requests>=2.31
```

### `requirements/dev.txt`

```
-r base.txt
pytest-django>=4.8
factory-boy>=3.3
faker>=24.0
pytest-cov>=5.0
```

### `requirements/prod.txt`

```
-r base.txt
gunicorn>=21.2
sentry-sdk[django]>=1.45
```

---

## 15. Environment Variables

`.env.example`:

```dotenv
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=config.settings.dev

# Database
DB_NAME=course_enrollment
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Location API
LOCATION_API_BASE_URL=https://api.countrystatecity.in/v1
LOCATION_API_KEY=your-location-api-key

# Cache (optional Redis)
CACHE_URL=redis://redis:6379/1
```

---

*Total estimated development time: ~9–10 working days for a single developer.*
