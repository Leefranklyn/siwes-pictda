# Student Management System

A Django CRUD capstone project: staff manage student records and students sign in to see their own record. It is built as a portfolio piece, so the interface is polished, the code is tested, and the README documents how everything fits together.

## Screenshots

| Dashboard | Student list |
|---|---|
| ![Dashboard](static/img/shots/dashboard.webp) | ![Student list](static/img/shots/students.webp) |

| Student detail |
|---|
| ![Student detail](static/img/shots/student-detail.webp) |

## Features

- Home page, login page, and dashboard with stat cards, charts, and recent activity
- Add, edit, delete, and detail views for students, with guardians managed inline
- Live search, filters, sorting, and pagination on the student list, powered by HTMX
- Course enrollments with grades and an automatically computed CGPA
- Role-based access for admin, staff, and student accounts
- Audit log of every create, update, and delete, with the actor recorded
- Student self-service record page at `/me/`
- Admin panel, custom 403 and 404 pages, seeded demo data, and a styled component set

## Tech stack

Python 3.12+, Django 6, SQLite (PostgreSQL via `DATABASE_URL`), Tailwind CSS through `django-tailwind`, HTMX, Chart.js, WhiteNoise, Pillow, django-environ, coverage.

Why Tailwind instead of Bootstrap: the design is a dark, token-driven interface with a custom palette, and Tailwind expresses it directly in the markup without fighting a Bootstrap theme. The palette, fonts, and component classes are defined once in `theme/static_src/src/styles.css` and reused everywhere.

## Setup

Requires Python 3.12 or newer and Node 20 or newer.

```bash
git clone <repository-url>
cd student-management-system
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py tailwind install
```

Inside the SIWES workspace this project shares the parent `siwes-pictda/.venv` environment instead of keeping its own `.venv` — run commands as `../.venv/bin/python manage.py …`.

## Run

In one terminal build and watch the CSS:

```bash
python manage.py tailwind start
```

In another terminal run the app:

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000.

## Demo accounts

Run `python manage.py seed_demo` first. Passwords come from environment variables; the documented defaults below are for local use only.

| Role | Username | Password (local default) |
|---|---|---|
| Admin | `demo_admin` | `LocalAdmin20!` |
| Staff | `demo_staff` | `LocalStaff20!` |
| Lecturer | `demo_lecturer` | `LocalLecturer20!` |
| Student | `demo_student` | `LocalStudent20!` |

Set `DEMO_MODE=True` to show the demo account autofill buttons on the login page (four buttons, one per role). Sample import files live in `docs/samples/` — `students_sample.csv` passes validation and `students_sample_errors.csv` shows row-level errors.

## Deployment

Deployed on Render with a Neon PostgreSQL database and Cloudflare R2 object storage. On the free web tier the service sleeps after 15 idle minutes, so the first request after a pause is slow while it wakes up.

| Piece | Service | Notes |
|---|---|---|
| Web app | Render `student-records` (Python, free tier) | Build installs dependencies, runs `collectstatic`, `migrate` and `seed_demo`; Gunicorn serves the app |
| Database | Neon PostgreSQL | Linked through the pooled `DATABASE_URL` environment variable produced by Neon's connection modal |
| Uploads | Cloudflare R2 | S3-compatible bucket through `django-storages`; the bucket's public `r2.dev` domain serves the files |

### Deploying your own copy

1. Push the repository to GitHub.
2. In Render, create a **Web Service** from that repo. Set the **Root Directory** to this project's folder (skip it in a standalone clone), and keep the build and start commands from `render.yaml` (`pip install -r requirements.txt` + `collectstatic` + `migrate` + `seed_demo`, and `gunicorn --bind 0.0.0.0:$PORT config.wsgi:application`).
3. Add the environment variables from `render.yaml`: `DEBUG=False`, `ALLOWED_HOSTS=.onrender.com`, `CSRF_TRUSTED_ORIGINS=https://*.onrender.com`, `TRUST_PROXY_HEADERS=True` (Render terminates TLS, and without it the HTTPS redirect loops), `DEMO_MODE=True` plus the demo passwords, `USE_S3=True`, `PHOTO_UPLOADS=True`, and the R2 bucket variables (`AWS_*`).
4. Create the R2 bucket values in the Cloudflare dashboard: an API token scoped to the bucket gives `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`, the controller endpoint is `AWS_S3_ENDPOINT_URL`, the bucket name is `AWS_STORAGE_BUCKET_NAME`, and turning on its public access domain gives `AWS_S3_CUSTOM_DOMAIN` (`pub-....r2.dev`).
5. Paste the Neon pooled `DATABASE_URL` (it must name the app database, not a Prisma shadow database) and deploy; the build migrates and seeds automatically.

Sign in as `demo_admin`, create your own administrator account through the accounts page, and then either delete the demo accounts or set `DEMO_MODE` off so the autofill buttons disappear from the login page.

## Database

Local development, tests, and the assignment submission run on SQLite, and nothing about the project requires PostgreSQL to be installed. The live demo runs on PostgreSQL, selected only by setting the `DATABASE_URL` environment variable, because hosts like Render have ephemeral disks: a SQLite file on the service disk would be wiped on every redeploy, so the demo would lose every change a visitor made. Uploaded photos follow the same rule: send them to S3-compatible object storage with `USE_S3=True`, or switch uploads off with `PHOTO_UPLOADS=False`. Run `python manage.py clearsessions` now and then to prune expired sessions.

## Architecture

Four roles (admin, staff, lecturer, student) across three Django apps under a `config` project:

- `accounts`: roles (groups plus the `user_role()` and `can_grade()` helpers in `accounts/roles.py`), permission mixins and the `roles_required` decorator in `accounts/mixins.py`, login/password views in `accounts/views.py`, admin-only account management in `accounts/manage_views.py`, the `UserProfile` model (`must_change_password`) and its signal in `accounts/models.py`, and `MustChangePasswordMiddleware` in `accounts/middleware.py`
- `students`: models (`Department`, `Lecturer`, `Student`, `Guardian`, `Course`, `Enrollment`) in `students/models.py`, forms in `students/forms.py`, student views (list, CRUD, tabs, bulk actions, transcripts, imports) in `students/views.py`, course views (list, detail, rosters, grade sheet, grade/course CSV, lecturer home) in `students/courses.py`, CSV parsing and validation in `students/imports.py`, session and GPA helpers in `students/utils.py`, the `seed_demo` command, and the `ui` template tags
- `core`: home, dashboard, global search, audit log list, and error pages in `core/views.py`; the `AuditLog` and `ImportBatch` models in `core/models.py`; audit signal receivers in `core/signals.py`; streaming CSV exports in `core/exports.py`; and the middleware that remembers the current request user in `core/middleware.py`

The frontend is server-rendered Django templates: `templates/base.html` is the shell, shared UI partials live in `templates/ui/`, and each app keeps its pages in `<app>/templates/<app>/`. HTMX (loaded in `base.html`) powers the student and course live search, the global top-bar search, and the account-form student picker — each asks the same URL (or an `/accounts/manage/link-students/` endpoint) for a partial. The dashboard charts fetch `/dashboard/charts.json` (built in `core/views.py`) and draw it with Chart.js. The transcript (`students/transcript.html`) is the only light-print page, via print styles in `templates/transcript_base.html`.

Every request stores the current user in thread-local storage; post-save and post-delete signal receivers in `core/signals.py` write audit rows with that user attached, including old-to-new grade changes. Views stay thin; CGPA and semester GPA live in `students/utils.py` and the `Student` model. Multi-row writes (imports, enroll-matching, bulk actions) use `bulk_create`/`bulk_update` inside `transaction.atomic()`.

### How a typical request flows

For example, saving the grade sheet (`students/courses.py:grade_sheet`):

1. `students/urls.py` routes `courses/<int:pk>/grades/` to the view; the decorator allows admin, staff, and lecturers.
2. `can_grade()` (in `accounts/roles.py`) checks the user is admin/staff or a lecturer assigned to this course; anyone else gets a 403.
3. The view loads the roster for the selected session — for lecturers, `only()` restricts the query to name, matric number, department, and level, so contact details never leave the database.
4. Each posted grade is compared with the stored one; only changed rows are saved, setting `graded_at` and `graded_by`, inside one `transaction.atomic()` block.
5. Each save fires the `post_save` receiver in `core/signals.py`, which writes an `AuditLog` row ("Grade for CSC201 changed from C to B (...)").

### Making a small change

To add a field to the student model, say `nationality`:

1. Add the field in `students/models.py`.
2. Run `python manage.py makemigrations students` and `python manage.py migrate` (see the next section).
3. Add it to the `fields` list in `StudentForm` in `students/forms.py` — the add and edit forms pick it up automatically.
4. Show it where needed in `students/templates/students/student_detail.html` or `students/_table.html`.
5. Add or extend a test in `students/tests/` and run `python manage.py test`.

### Migrations

Create migrations after model changes with `python manage.py makemigrations` and apply them with `python manage.py migrate`. Never delete the migration files in `<app>/migrations/` — they are how Django knows what has already been applied to the database. Check that your models and migrations agree with `python manage.py makemigrations --check --dry-run`.

## Tests

```bash
python manage.py test
```

The suite (104 tests) lives in `students/tests/` (models, permissions, views, V2 features, seeding — shared setup helpers are in `students/tests/helpers.py`), `accounts/tests.py` (roles, account management, password flows), and `core/tests.py` (audit logging, dashboard, public pages). It covers the permission matrix for all four roles, CGPA and semester GPA, form validation, HTMX behaviour, CRUD flows, CSV imports with preview and rollback, exports with formula safety, bulk actions, transcripts, audit logging, and the seeding command. Coverage summary:

```
TOTAL   2168   212   90%
```

## Intentional complexity

Three parts are more involved than a plain CRUD app and why:

- **Audit logging with the actor attached** (`core/middleware.py`, `core/signals.py`): model signal receivers cannot see the request, so `AuditUserMiddleware` stores the request user in thread-local storage for the duration of each request, and the receivers read it back. This is a common Django pattern; the alternative is passing the user through every save call by hand.
- **Role-aware admin site** (`accounts/admin.py`, registered in `config/settings.py` via `RecordsAdminConfig`): a small `AdminSite` subclass keeps non-admin roles out of `/admin/` instead of letting Django's default permissions decide.
- **Lecturer field restrictions** (`students/courses.py:_visible_roster`): instead of hiding columns in the template, the roster query itself uses `only()` so a lecturer's page never selects student contact fields from the database.

Everything else follows plain Django conventions deliberately: function views and class-based views, `ModelForm`s, role mixins, `inlineformset_factory` for guardians, and Django's built-in password change/reset views.

## Known limitations

- Photos are stored locally in development; on ephemeral hosts use object storage or disable uploads
- The enrollment trend chart counts students by `enrolled_on`, not course enrollments
- There is no self-service password reset or user management UI; users are managed in the admin panel
- The student list paginates server-side; the live search re-renders the table partial, not individual cells
- First request after a free-tier host idles can be slow while the service wakes up
