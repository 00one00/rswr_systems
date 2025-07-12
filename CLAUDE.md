# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up database with migrations and create superuser
python manage.py setup_db

# Create default groups and test users
python manage.py setup_groups

# Run development server
python manage.py runserver
```

### Database Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser (using environment variables)
python manage.py createsu
```

### Static Files
```bash
# Collect static files (required for deployment)
python manage.py collectstatic
```

### Testing and Linting
The project doesn't have specific test or lint commands configured. Tests should be run using Django's test runner:
```bash
python manage.py test
```

## High-Level Architecture

### Project Structure
This is a Django-based windshield repair management system with three main applications:

1. **Technician Portal** (`apps/technician_portal/`)
   - Manages repair workflows and technician operations
   - Handles repair status tracking through queue states
   - Provides technician dashboard and repair management

2. **Customer Portal** (`apps/customer_portal/`)
   - Customer-facing interface for repair requests and tracking
   - Includes data visualizations using D3.js
   - Manages customer accounts and approvals

3. **Rewards & Referrals** (`apps/rewards_referrals/`)
   - Handles customer referral codes and reward points
   - Manages reward redemption and fulfillment
   - Integrates with repair system for discount application

### Core Models and Relationships

#### Core Models (`core/models.py`)
- **Customer**: Central customer entity with company information

#### Technician Portal Models
- **Technician**: Extends User model with technician-specific data
- **Repair**: Central repair tracking with queue status workflow
- **UnitRepairCount**: Tracks repair frequency per customer unit

#### Customer Portal Models
- **CustomerUser**: Links Django User to Customer accounts
- **RepairApproval**: Tracks customer approvals for repairs
- **CustomerPreference**: Stores customer portal preferences

#### Rewards Models
- **ReferralCode**: Unique codes for customer referrals
- **Reward**: Point balances for customers
- **RewardOption**: Available redemption options
- **RewardRedemption**: Tracks redemption requests and fulfillment

### Key Business Logic

#### Repair Workflow
Repairs progress through these statuses:
- `REQUESTED`: Customer-initiated repair requests
- `PENDING`: Awaiting customer approval
- `APPROVED`: Approved by customer, ready for work
- `IN_PROGRESS`: Currently being worked on
- `COMPLETED`: Repair finished
- `DENIED`: Rejected by customer

#### Cost Calculation
Repair costs are calculated based on repair frequency per unit:
- 1st repair: $50
- 2nd repair: $40
- 3rd repair: $35
- 4th repair: $30
- 5th+ repairs: $25

#### Reward System Integration
- Customers earn points through referrals (500 points per referral)
- New customers get 100 welcome points
- Rewards can be automatically applied to repairs when completed
- Discount types: percentage, fixed amount, or free (100% off)

### Configuration and Deployment

#### Settings Structure
- **Main settings**: `rs_systems/settings.py` - Development configuration
- **AWS settings**: `rs_systems/settings_aws.py` - Production configuration
- **WSGI**: `rs_systems/wsgi.py` - Web server interface

#### Environment Variables
The system uses these key environment variables:
- `ENVIRONMENT`: Sets deployment environment (development/production)
- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode toggle
- `DATABASE_URL`: Database connection string
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `USE_HTTPS`: Enable HTTPS security settings

#### Database Configuration
Supports both local (SQLite) and production (PostgreSQL) databases via environment variables:
- `USE_RAILWAY_DB`: Toggle between Railway and local database
- `RAILWAY_DATABASE_URL`: Production database URL
- `LOCAL_DATABASE_URL`: Local development database URL

### API and Integration

#### REST Framework
- Uses Django REST Framework with token authentication
- API documentation available via drf-spectacular
- Main API endpoints under `/api/` prefix

#### Key API Endpoints
- Technician Portal API: `/api/` (technician operations)
- Customer Portal visualizations: `/customer/api/` (chart data)
- Rewards system: `/referrals/` (referral and reward management)

### Template and Frontend

#### Template Structure
- Base templates in `templates/` directory
- App-specific templates in each app's `templates/` folder
- Uses Django template inheritance

#### Static Files
- CSS: `static/css/` with component-based organization
- JavaScript: `static/js/` with D3.js visualizations
- Images: `static/images/` for assets

#### Frontend Technologies
- **Bootstrap**: UI framework for responsive design
- **D3.js v7**: Data visualization library for charts
- **Font Awesome**: Icon library
- **Custom CSS**: Component-based styling approach

### Development Workflow

#### User Management
The system includes management commands for setting up users:
- `setup_groups`: Creates default technician groups and test users
- Default users: `admin` (superuser), `johndoe` (tech manager), `jdoe` (technician)

#### Testing Data
Default test users have simple passwords (`123`) for development.
In production, use environment variables for secure user creation.

### Security Considerations

#### Authentication
- Uses Django's built-in authentication system
- Token-based authentication for API endpoints
- Session-based authentication for web interface

#### HTTPS Configuration
- Configurable HTTPS settings based on environment
- Railway deployment detection with appropriate security headers
- CSRF and session security settings

#### Permission System
- Role-based access via Django groups
- Technician-specific permissions
- Customer-specific data access controls

### Common Development Patterns

#### Service Layer
Apps use service classes to encapsulate business logic:
- `ReferralService`: Handles referral code generation and processing
- `RewardService`: Manages reward points and redemptions
- `RewardFulfillmentService`: Handles reward fulfillment workflow

#### Model Integration
- Models use Django signals for automatic updates
- Cross-app model references using string paths
- Automatic reward application when repairs are completed

#### Error Handling
- Graceful error handling in reward application
- Logging configuration for debugging
- Database transaction safety