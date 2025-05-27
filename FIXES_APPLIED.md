# RS Systems - Fixes Applied

## Issues Identified and Fixed

### 1. Django Settings Module Configuration
**Problem**: The Django settings module was changed from `rs_systems.settings` to `django_settings`, breaking the application structure.

**Fix Applied**:
- Restored `manage.py` to use `rs_systems.settings`
- Updated `application.py` to use `rs_systems.settings_aws` for AWS deployment
- Updated `.ebextensions/01_wsgi.config` to use `rs_systems.settings_aws`
- Removed duplicate `django_settings.py` file

### 2. AWS WSGI Application Errors
**Problem**: The `application.py` file had a bug causing `KeyError: 'CONTENT_LENGTH'` errors on AWS.

**Fix Applied**:
- Added proper WSGI wrapper function that handles missing `CONTENT_LENGTH` header
- Added logging for debugging requests
- Fixed the Django application initialization

### 3. Missing User Groups
**Problem**: The Technicians group was missing, preventing proper user role assignment.

**Fix Applied**:
- Ran the existing `setup_groups` management command
- Created the "Technicians" group
- Created default admin and technician users

### 4. Static Files Configuration
**Problem**: Conflicting static files configuration between development and production.

**Fix Applied**:
- Maintained proper separation between `static/` (source) and `staticfiles/` (collected)
- Updated AWS settings to use standard static files storage (not compressed)
- Ensured proper static files collection

### 5. Directory Structure Cleanup
**Problem**: Multiple duplicate files and folders from failed deployment attempts.

**Fix Applied**:
- Removed duplicate files: `django_settings.py`, `django_wsgi.py`, `django_urls.py`, `test_application.py`
- Kept proper Django project structure intact

## Current Configuration

### Local Development
- Uses `rs_systems.settings`
- SQLite database (fallback when no DATABASE_URL configured)
- Debug mode enabled
- Static files served by Django development server

### AWS Production
- Uses `rs_systems.settings_aws`
- PostgreSQL database (when RDS_HOSTNAME is set)
- Debug mode disabled
- Static files served by whitenoise
- Proper security headers enabled

## Deployment Instructions

### For Local Development
1. Ensure virtual environment is activated
2. Run migrations: `python manage.py migrate`
3. Create superuser: `python manage.py createsuperuser`
4. Run setup command: `python manage.py setup_groups`
5. Collect static files: `python manage.py collectstatic`
6. Start server: `python manage.py runserver`

### For AWS Elastic Beanstalk
1. Ensure all changes are committed to git
2. Deploy using: `eb deploy`
3. The application will use `rs_systems.settings_aws` automatically
4. Set environment variables in EB console:
   - `SECRET_KEY`: Your production secret key
   - `RDS_HOSTNAME`: Your RDS endpoint
   - `RDS_DB_NAME`: Your database name
   - `RDS_USERNAME`: Your database username
   - `RDS_PASSWORD`: Your database password

## User Management

### Default Users Created
- **admin**: Superuser with full access
- **johndoe**: Technician manager
- **jdoe**: Regular technician

### Groups Available
- **Technicians**: For technician portal access

### Creating New Users
1. Go to Django Admin → Users
2. Create new user
3. Use the admin actions to assign roles:
   - "Convert selected users to technicians"
   - "Convert selected users to customers"
   - "Give selected users both technician and customer roles"

## Testing Checklist

### Local Testing
- [ ] Homepage loads with proper styling
- [ ] Admin interface accessible
- [ ] Technician portal accessible for technician users
- [ ] Customer portal accessible for customer users
- [ ] Static files (CSS/JS) loading properly
- [ ] Navigation between pages works

### AWS Testing
- [ ] Application deploys without errors
- [ ] Homepage loads with proper styling
- [ ] Database connections work
- [ ] Static files serve correctly
- [ ] User authentication works
- [ ] All portal features functional

## Notes
- The `staticfiles/` directory contains collected static files and should not be manually edited
- The `static/` directory contains source static files for development
- AWS deployment uses a separate settings file for production-specific configurations
- The WSGI application wrapper handles AWS load balancer quirks 