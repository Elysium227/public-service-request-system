# Public Service Request System

A web app where citizens can submit public service requests (broken streetlight, water issue, garbage collection) and admins can track them until they are resolved.

## Features
- Citizen registration and login
- Submit a request (category, location, description, optional image)
- Admin dashboard
- Status tracking (Pending, In Progress, Resolved)
- Basic analytics (open vs resolved cases)

## Tech Stack
- Python
- Django

## Setup
1. Clone the repo
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/Scripts/activate` (Git Bash on Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run the server: `python manage.py runserver`
6. Open http://127.0.0.1:8000