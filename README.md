# Public Service Request System

A mini eCitizen-style web app where citizens report public service problems (broken streetlight, water issue, garbage collection) and admins track them until they are resolved.

## Features

**Citizens**
- Register, log in and log out
- Submit a request with category, location, description and an optional image
- View their own requests and see the current status of each

**Admins**
- Dashboard listing all requests from all citizens
- Update a request's status: Pending, In Progress or Resolved
- Analytics: total, open (pending plus in progress) and resolved counts, with a progress bar
- Filter requests by status and category

**Access control**
- Citizen pages require login
- The dashboard and status updates are for staff users only. Other users see an "Access denied" page.

## Tech Stack

- Python and Django
- SQLite database (Django default)
- Pillow for image uploads
- Plain HTML and CSS templates

## Setup

1. Clone the repo:
```
   git clone https://github.com/Elysium227/public-service-request-system.git
   cd public-service-request-system
```
2. Create and activate a virtual environment:
```
   python -m venv venv
   source venv/Scripts/activate      # Windows (Git Bash)
   source venv/bin/activate          # Mac/Linux
```
3. Install dependencies:
```
   pip install -r requirements.txt
```
4. Create the database tables:
```
   python manage.py migrate
```
5. Create an admin account:
```
   python manage.py createsuperuser
```
6. Start the server:
```
   python manage.py runserver
```
7. Open http://127.0.0.1:8000

## Usage

1. Click **Register** to create a citizen account.
2. Click **Submit request**, fill in the form and submit.
3. Open **My requests** to see your requests and their status.
4. Log in with the admin account and open **Dashboard** to view all requests, filter them and change their status.
5. Log back in as the citizen to see the updated status.

To make an existing user an admin, log in at `/admin/` with the superuser account, open Users, and tick **Staff status** for that user.

## Project Structure

```
config/                 Project settings and main URLs
requests_app/
    models.py           ServiceRequest model
    forms.py            Request submission form
    views.py            Page logic (citizen and admin views)
    urls.py             App URLs
    templates/          HTML pages
manage.py
requirements.txt
```

## Request Status Flow

Pending, then In Progress, then Resolved. Only admins can change the status.

## Possible Future Improvements

- Email or SMS notifications when a status changes
- Comments on requests
- Charts for analytics