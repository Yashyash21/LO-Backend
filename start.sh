#!/bin/bash

# Apply database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start the Django app
gunicorn backend.wsgi
