# Customer Portal App

## Overview
The Customer Portal app is a Django-based web application that provides customers with a complete self-service interface for managing their windshield repair services. It enables customers to view their repair history, request new repairs, approve or deny pending repairs, and visualize repair data through interactive charts.

## Features

### User Management & Authentication
- Customer registration and profile creation
- Account settings management
- Company information management
- Primary contact designation

### Repair Management
- View all repairs and their statuses
- Request new repairs
- Approve/deny pending repairs
- View detailed repair information
- Track repair history

### Analytics & Visualization
- Interactive D3.js visualizations of repair data:
  - Repair Status Distribution (pie chart)
  - Repairs by Unit (bar chart)
  - Repair Frequency Over Time (line chart)
- Statistical summaries of repair activity
- Visual indicators of repair statuses

## Technical Documentation

### Models

#### CustomerUser
Links Django User accounts to Customer entities.
- **user**: One-to-one relationship with Django User model
- **customer**: Foreign key to Customer model
- **is_primary_contact**: Boolean field indicating if user is the primary contact

#### CustomerPreference
Stores customer preferences for the portal.
- **customer**: One-to-one relationship with Customer model
- **receive_email_notifications**: Boolean field
- **receive_sms_notifications**: Boolean field
- **default_view**: Choice field for dashboard view preference

#### RepairApproval
Tracks customer approvals for repairs.
- **repair**: One-to-one relationship with Repair model
- **approved**: Boolean field indicating approval status
- **approved_by**: Foreign key to CustomerUser model
- **approval_date**: DateTime field for when approval was made
- **notes**: Text field for additional information

### Views

#### Dashboard
`customer_dashboard` renders the main dashboard with:
- Company information
- Repair statistics (active, completed, awaiting approval)
- Recent repair history
- Repairs awaiting approval
- Interactive data visualizations

#### Repair Management
- `customer_repairs`: Lists all customer's repairs
- `customer_repair_detail`: Shows detailed repair information
- `customer_repair_approve`: Approves a pending repair
- `customer_repair_deny`: Denies a pending repair
- `request_repair`: Creates a new repair request

#### Account Management
- `customer_register`: Customer registration
- `profile_creation`: Customer profile setup
- `edit_company`: Company information editing
- `account_settings`: User account settings

#### API Endpoints
- `unit_repair_data_api`: Provides repair data aggregated by unit
- `repair_cost_data_api`: Provides repair frequency data over time

### Templates
- **dashboard.html**: Main dashboard with visualizations
- **repairs.html**: Repair listing page
- **repair_detail.html**: Detailed view of a single repair
- **repair_approve.html**: Confirmation page for repair approval
- **repair_deny.html**: Confirmation page for repair denial
- **request_repair.html**: Form for requesting new repairs
- **edit_company.html**: Form for editing company information
- **account_settings.html**: Form for managing account settings
- **profile_creation.html**: Form for creating customer profile
- **register.html**: Customer registration form

### Data Visualization
The customer portal includes three interactive D3.js visualizations:

1. **Repair Status Distribution (Pie Chart)**
   - Shows the distribution of repairs across different statuses
   - Color-coded segments for each status
   - Interactive legend with counts

2. **Repairs by Unit (Bar Chart)**
   - Shows repair counts for each unit number
   - Sorted in descending order by repair count
   - Limited to top 10 units with most repairs

3. **Repair Frequency Over Time (Line Chart)**
   - Shows the number of repairs performed over time
   - Grouped by month
   - Helps identify trends and patterns in repair frequency

### CSS
The `dashboard_visualizations.css` file provides styling for all visualization components, including:
- Container and card layouts
- Chart-specific styling
- Responsive design adjustments
- Tooltip formatting
- Loading state indicators

## Usage Guidelines

### For Administrators
- Set up customer accounts
- Monitor repair approval workflows
- Review customer repair history

### For Customers
- Register an account and create a profile
- Request repairs for windshield damage
- View repair history and status
- Approve or deny pending repairs
- View visual analytics of repair data

## API Documentation

### Unit Repair Data API
- **Endpoint**: `/customer/api/unit-repair-data/`
- **Method**: GET
- **Response**: JSON array of objects with unit_number and repair_count
- **Authentication**: Requires customer login
- **Used by**: Repairs by Unit bar chart

### Repair Frequency Data API
- **Endpoint**: `/customer/api/repair-cost-data/`
- **Method**: GET
- **Response**: JSON array of objects with date and count (grouped by month)
- **Authentication**: Requires customer login
- **Used by**: Repair Frequency Over Time line chart

## Dependencies
- Django web framework
- D3.js (v7) for data visualizations
- Bootstrap for UI components
- Font Awesome for icons 