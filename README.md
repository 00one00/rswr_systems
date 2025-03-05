# Rock Star Windshield Repair Systems (RSWR)

## Overview
The Rock Star Windshield Repair System is a Django-based web application designed to streamline windshield repair operations. The system consists of two main components: a Technician Portal for repair staff and a Customer Portal for client companies. The application enables efficient tracking of repairs, customer approvals, invoicing, and provides interactive data visualizations for business intelligence.

## Current System Architecture

### Core Components
- **Technician Portal**: Web interface for technicians to manage repairs, track queues, and document work
- **Customer Portal**: Interface for customers to request repairs, approve/deny work, and view repair history
- **Admin Interface**: Customized Django admin for system management and user administration
- **Database Layer**: PostgreSQL database storing repair, customer, and technician data

### Technology Stack
- **Backend**: Python, Django 5.1
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript
- **Data Visualization**: D3.js
- **Authentication**: Django's built-in authentication system

## Implemented Features

### Technician Portal
- **Dashboard**: Overview of assigned repairs and customer-requested repairs
- **Repair Queue Management**: View, filter, and update repair statuses
- **Repair Documentation**: Record technical details about repairs
- **Customer Management**: Create and manage customer records
- **Admin Controls**: Additional controls for administrators to manage all repairs

### Customer Portal
- **Dashboard**: Interactive visualizations of repair data using D3.js
- **Repair Request Submission**: Submit new repair requests
- **Repair Tracking**: Monitor repair status in real-time
- **Approval System**: Review and approve/deny proposed repairs
- **Unit/Vehicle Tracking**: View repair history by unit number
- **Account Settings**: Manage profile and company information

### Data Visualizations
- **Repair Status Distribution**: Pie chart showing repairs by status
- **Repairs by Unit**: Bar chart displaying repair counts for each unit
- **Repair Frequency Over Time**: Line chart tracking repair volume over time

## Data Model

The current database schema includes these key models:

### Core Models
- **Customer**: Companies that request repairs
- **Repair**: Central entity tracking repair details, status, and costs
- **Technician**: Staff members who perform repairs
- **UnitRepairCount**: Tracks repair frequency by customer unit

### Supporting Models
- **CustomerUser**: Links Django Users to Customer accounts
- **CustomerPreference**: Stores customer portal preferences
- **RepairApproval**: Records of customer approval decisions

## Authentication & Access Control

### User Types
- **Administrators**: Full system access
- **Technicians**: Access to Technician Portal features
- **Customer Users**: Access to Customer Portal for their company only
- **Primary Contacts**: Special customer users who can manage company settings

## In-Progress Development

Currently implemented and working:
- Complete user authentication and role-based access control
- Repair workflow from creation to completion
- Customer approval process
- Interactive data visualizations
- Admin interfaces for user management

## Getting Started

### Local Development
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure database settings in `settings.py`
4. Run migrations: `python manage.py migrate`
5. Create a superuser: `python manage.py createsuperuser`
6. Start the development server: `python manage.py runserver`

## License
Proprietary software developed for Rock Star Windshield Repair. All rights reserved.
