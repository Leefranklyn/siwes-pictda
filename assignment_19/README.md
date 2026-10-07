# Assignment 19 - Student Registration Website

## Description
This assignment builds a student registration website using the Django framework. The project is organized as a Django project (`config`) containing a `pages` app with five pages: Home, About, Students, Contact and Register. The UI uses a custom stylesheet (Sora/Inter fonts, gradient accents, responsive layout) served from the app's `static` directory.

## Objective
- Create a Django project and app
- Define **Views** for each page (function-based views)
- Map **URLs** to the views with `path()` routes
- Render **Templates** for each page using a shared base template
- Handle form submissions (Contact form and Student registration form backed by a `Student` model)
- Display all registered students on a roster page

## Pages
| Page | URL | View | Template |
| --- | --- | --- | --- |
| Home | `/` | `pages.views.home` | `pages/home.html` |
| About | `/about/` | `pages.views.about` | `pages/about.html` |
| Students | `/students/` | `pages.views.students` | `pages/students.html` |
| Contact | `/contact/` | `pages.views.contact` | `pages/contact.html` |
| Register | `/register/` | `pages.views.register` | `pages/register.html` |

## Running the Project
From the repository root (using the existing virtual environment):

```bash
.venv/bin/python assignment_19/manage.py runserver
```

Then open http://127.0.0.1:8000/ in a browser.

> Note: The repository uses `pip` and a shared `.venv` (see `requirements.txt`), so the project sticks with that setup instead of `uv`.

## Features
- **Register** — validated form saving to the `pages_student` table in `db.sqlite3`
- **Students** — live roster of every registered student (newest first) with avatars and course badges
- **Home** — hero section with live stats (student count, course count, latest signup)
- **Contact** — validated contact form
- Shared responsive base template with sticky header and active-page nav highlighting
