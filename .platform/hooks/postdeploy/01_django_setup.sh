#!/bin/bash

# Django post-deployment setup
echo "Running Django migrations..."
source /var/app/venv/*/bin/activate
cd /var/app/current

# Create media directories if they don't exist
echo "Creating media directories..."
mkdir -p /var/app/current/media/repair_photos/before
mkdir -p /var/app/current/media/repair_photos/after
# Set appropriate permissions for media directories
chmod -R 755 /var/app/current/media
chown -R webapp:webapp /var/app/current/media

python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "Django setup completed"