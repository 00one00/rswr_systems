# RS Systems - Windshield Repair Management Platform

A comprehensive Django-based windshield repair management system that streamlines operations for repair technicians and provides an intuitive customer portal for service tracking and rewards management.

## 🎯 Overview

RS Systems is a full-stack web application designed to modernize windshield repair operations through digital workflow management. The platform connects technicians, customers, and administrative staff through specialized portals that handle everything from repair requests to customer rewards and referral programs.

### Key Benefits

- **Streamlined Operations**: Digital repair workflow with queue management and status tracking
- **Customer Engagement**: Self-service portal with real-time repair tracking and approvals
- **Revenue Growth**: Integrated referral system with rewards program to drive customer retention
- **Cost Efficiency**: Automated pricing based on repair frequency with built-in discount application
- **Data Insights**: Comprehensive analytics and visualizations for business intelligence

## 🏗️ System Architecture

### Core Applications

The system is built with a modular architecture featuring three main applications:

#### 1. **Technician Portal** (`apps/technician_portal/`)
- Repair workflow management with queue-based status tracking
- Customer and unit management with repair history
- Cost calculation based on repair frequency
- Reward fulfillment and discount application
- Real-time notifications for pending tasks

#### 2. **Customer Portal** (`apps/customer_portal/`)
- Self-service repair request submission
- Real-time repair status tracking and approvals
- Interactive data visualizations using D3.js
- Account management and preferences
- Repair history and documentation access

#### 3. **Rewards & Referrals** (`apps/rewards_referrals/`)
- Referral code generation and tracking
- Point-based reward system with automatic earning
- Flexible redemption options with discount types
- Automated reward application to repairs
- Comprehensive redemption management

### Supporting Infrastructure

- **Security Module**: Authentication, authorization, and security middleware
- **Photo Storage**: Repair documentation and image management
- **Queue Management**: Advanced repair workflow orchestration
- **Scheduling**: Appointment and maintenance scheduling

## 🚀 Features

### For Technicians
- **Digital Repair Queue**: Manage repairs through status-based workflow (Requested → Pending → Approved → In Progress → Completed)
- **Smart Pricing**: Automatic cost calculation based on unit repair frequency ($50 first repair, decreasing to $25 for 5+ repairs)
- **Customer Management**: Complete customer profiles with repair history and contact information
- **Reward Integration**: Apply customer rewards and discounts directly to repairs
- **Real-time Notifications**: Stay informed about pending redemptions and approvals

### For Customers
- **Self-Service Portal**: Submit repair requests and track status in real-time
- **Approval Workflow**: Review and approve/deny repair estimates with detailed information
- **Visual Analytics**: Interactive charts showing repair patterns and costs
- **Referral Program**: Generate unique referral codes and earn 500 points per successful referral
- **Reward Redemption**: Browse and redeem points for discounts, free services, and merchandise

### For Administrators
- **User Management**: Control access and permissions for technicians and customers
- **Reward Configuration**: Set up reward types, options, and redemption rules
- **System Analytics**: Monitor performance, costs, and customer engagement
- **Flexible Pricing**: Configure repair costs and discount structures

## 🛠️ Technology Stack

### Backend
- **Django 5.1.2**: Web framework with ORM and admin interface
- **Django REST Framework 3.15.2**: API development and documentation
- **PostgreSQL**: Production database with robust data integrity
- **SQLite**: Development database for local testing

### Frontend
- **Bootstrap**: Responsive UI framework
- **D3.js v7**: Advanced data visualization library
- **Font Awesome**: Comprehensive icon library
- **Custom CSS**: Component-based styling approach

### Infrastructure
- **Gunicorn**: Production WSGI server
- **WhiteNoise**: Static file serving
- **AWS S3**: File storage and media management
- **Railway/AWS**: Cloud deployment platforms

### Development Tools
- **Python 3.x**: Primary programming language
- **pip**: Package management
- **Django Management Commands**: Custom database setup and user management

## ⚡ Quick Start

### Prerequisites
- Python 3.8+
- pip package manager
- Git
- Virtual environment support

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd rs_systems_branch2
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Create .env file with required variables
   SECRET_KEY=your-secret-key
   DEBUG=True
   ADMIN_PASSWORD=secure-admin-password
   ```

5. **Initialize database**
   ```bash
   python manage.py setup_db
   python manage.py setup_groups
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Main application: http://localhost:8000
   - Admin interface: http://localhost:8000/admin
   - API documentation: http://localhost:8000/api/schema/swagger-ui/

## 📋 Usage Guide

### Default Users
The system creates default test users for immediate access:

- **Admin**: `admin` / `[ADMIN_PASSWORD]` - Full system access
- **Tech Manager**: `johndoe` / `[secure password]` - Technician management
- **Technician**: `jdoe` / `[secure password]` - Repair operations

### Customer Registration
Customers can register through the customer portal with optional referral codes to automatically earn welcome points and referral bonuses.

### Repair Workflow
1. **Customer Request**: Submit repair request with unit and damage details
2. **Technician Review**: Assess request and provide cost estimate
3. **Customer Approval**: Review and approve/deny repair estimate
4. **Work Performance**: Technician completes repair work
5. **Completion**: Automatic cost calculation and reward application

### Reward System
- **Earning Points**: 500 points per successful referral, 100 welcome points
- **Redemption Options**: Percentage discounts, fixed amounts, free services
- **Automatic Application**: Rewards applied to repairs when completed

## 🔧 Development

### Database Management
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsu
```

### Testing
```bash
# Run all tests
python manage.py test

# Test specific app
python manage.py test apps.technician_portal
```

### Static Files
```bash
# Collect static files for production
python manage.py collectstatic
```

## 🌐 API Documentation

The system provides comprehensive REST API documentation:

- **Interactive Documentation**: `/api/schema/swagger-ui/`
- **OpenAPI Schema**: `/api/schema/`
- **ReDoc Documentation**: `/api/schema/redoc/`

### Key Endpoints
- **Repairs**: `/api/repairs/` - Repair CRUD operations
- **Customers**: `/api/customers/` - Customer management
- **Rewards**: `/referrals/api/` - Reward and referral operations
- **Analytics**: `/customer/api/` - Data visualization endpoints

## 🚀 Deployment

### Environment Configuration
The system supports multiple deployment environments with environment-specific settings:

- **Development**: `rs_systems/settings.py`
- **Production**: `rs_systems/settings_aws.py`

### Required Environment Variables
```bash
# Core Configuration
SECRET_KEY=your-secret-key
DEBUG=False
ENVIRONMENT=production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Security
USE_HTTPS=True

# User Management
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=secure-password
```

### Deployment Platforms
- **Railway**: Automatic deployment with PostgreSQL
- **AWS**: EC2 with RDS and S3 integration
- **Docker**: Containerized deployment support

## 📊 Data Models

### Core Entities
- **Customer**: Company information and contact details
- **Technician**: User profile with expertise and contact info
- **Repair**: Central repair tracking with status workflow
- **Reward**: Point balances and redemption tracking

### Business Logic
- **Repair Frequency Pricing**: Automatic cost reduction for repeat repairs
- **Reward Integration**: Seamless point earning and redemption
- **Status Workflow**: Structured repair process management

## 🔒 Security

### Authentication & Authorization
- Django's built-in authentication system
- Token-based API authentication
- Role-based permissions with groups
- Session security with CSRF protection

### Data Protection
- Secure password handling
- HTTPS enforcement in production
- Environment variable configuration
- SQL injection prevention through ORM

## 📈 Analytics & Reporting

### Customer Portal Visualizations
- Repair frequency trends over time
- Cost analysis by unit and repair type
- Status distribution charts
- Customer-specific metrics

### Business Intelligence
- Technician performance tracking
- Revenue analysis with discount impact
- Customer engagement metrics
- Referral program effectiveness

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow Django best practices
- Write comprehensive tests
- Update documentation for new features
- Use environment variables for configuration
- Maintain security standards

## 📝 License

This project is proprietary software. All rights reserved.

## 📞 Support

For technical support or questions about the RS Systems platform:

- **Documentation**: Refer to the `/docs` directory for detailed guides
- **Issues**: Report bugs and feature requests through the project repository
---

*Built with Django, designed for efficiency, and optimized for growth.*