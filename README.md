# Rock Star Windshield Repair Systems

## Overview
The RS Wind Repair Systems is a comprehensive Django-based web application designed to streamline the management of windshield repairs for wind power companies. The system consists of two main components: a Technician Portal for repair staff and a Customer Portal for client companies. The application enables efficient tracking of repairs, customer approvals, invoicing, and provides data visualizations for business intelligence.

## System Architecture

### Core Components
- **Technician Portal**: Internal system for technicians to manage repairs, schedules, and customer interactions
- **Customer Portal**: External interface for customers to request repairs, approve work, and view repair history
- **Admin Interface**: Customized Django admin for system management and user administration
- **REST API**: Backend services supporting both portals and potential mobile applications
- **Data Visualization**: Interactive D3.js charts providing insights into repair statistics

### Technology Stack
- **Backend**: Django 5.1, Python
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript, D3.js
- **API**: Django REST Framework
- **Authentication**: Django's authentication system with token-based API authentication
- **Documentation**: DRF Spectacular for API documentation

## Features

### Technician Portal
- **Dashboard**: Overview of assigned repairs, status metrics, and daily schedule
- **Repair Management**: Create, view, update, and track repair requests through the entire workflow
- **Customer Records**: Access and manage customer information and repair history
- **Material Tracking**: Record materials used for repair work
- **Photo Documentation**: Upload and manage repair photos
- **Scheduling**: Manage technician availability and work assignments
- **Repair Logs**: Detailed tracking of all changes to repair status

### Customer Portal
- **Dashboard**: Visualizations of repair statistics and status using D3.js
- **Repair Requests**: Submit new repair requests
- **Repair Approval**: Review and approve/deny proposed repairs
- **Unit Management**: Track repair history by unit/vehicle
- **Account Settings**: Manage notification preferences and user access
- **User Management**: Primary contacts can manage additional users for their company

### Admin Features
- **User Management**: Create and manage technician and customer accounts
- **System Configuration**: Manage system settings and lookup values
- **Data Export**: Generate reports and export data for analysis
- **Technician Registration**: Specialized interface for adding new technicians

### Data Visualization
- **Repair Status Distribution**: Pie chart showing the distribution of repairs across different statuses
- **Repairs by Unit**: Bar chart displaying the number of repairs for each unit
- **Repair Frequency Over Time**: Line chart tracking repair volume over time

## Data Model

The system is built around a central Repair model with relationships to Customers, Technicians, and supporting entities:

### Core Models
- **Customer**: Companies that request repairs
- **Repair**: Central entity tracking repair details, status, and costs
- **UnitRepairCount**: Tracks repair frequency by customer unit
- **Technician**: Staff members who perform repairs
- **Invoice**: Financial records for completed repairs

### Supporting Models
- **RepairMaterial**: Materials used during repairs
- **RepairPhoto**: Photos documenting repairs
- **RepairLog**: Audit trail of repair status changes
- **TechnicianSchedule**: Work schedules for technicians
- **CustomerPreference**: Customer-specific settings
- **RepairApproval**: Records of customer approval decisions

## Authentication & Access Control

### User Types
- **Administrators**: Full system access via Django admin
- **Technicians**: Access to Technician Portal features based on assignments
- **Customer Users**: Access to Customer Portal for their company only
- **Primary Contacts**: Special customer users who can manage other users for their company

### Authentication Methods
- **Web Interface**: Form-based authentication with session management
- **API**: Token-based authentication for programmatic access
- **Password Policy**: Enforced security requirements for all passwords

### Authorization
- Role-based access control for different user types
- Object-level permissions ensure users only access their own data
- Fine-grained permission controls in the Django admin

## API Documentation
The system provides a RESTful API documented using Swagger/OpenAPI via DRF Spectacular:
- Access API documentation at `/api/schema/swagger-ui/`
- Token-based authentication for all API endpoints
- Comprehensive endpoints for both portals

## Development & Deployment

### Local Development
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure database settings in `settings.py`
4. Run migrations: `python manage.py migrate`
5. Create a superuser: `python manage.py createsuperuser`
6. Start the development server: `python manage.py runserver`

### Static Files
- CSS files are located in `/static/css/`
- JavaScript files are in `/static/js/`
- Run `python manage.py collectstatic` to gather static files for production

### Database Setup
- The system is configured to use PostgreSQL
- Database schema is documented in `docs/DATABASE_SCHEMA.md`

## Future Enhancements
- Mobile applications for technicians
- Advanced reporting and analytics
- Integration with financial systems
- Customer self-service portal enhancements
- AI-assisted damage assessment
- Scheduling optimization algorithms
- Inventory management system integration

## License
Proprietary software developed for RS Wind Repair Systems. All rights reserved. 