# Technician Portal App

## Overview
The Technician Portal app is a Django-based web application that provides technicians with a comprehensive interface for managing windshield repair operations. It enables technicians to process repair requests, update repair statuses, document technical details, and track repair metrics.

## Features

### User Management & Authentication
- Technician registration and profile creation
- Account settings management
- Skill level and certification tracking
- Work schedule and availability management

### Repair Queue Management
- View all assigned and available repairs
- Filter repairs by status, priority, or customer
- Claim repairs from the queue
- Update repair status through workflow stages
- Document repair details and outcomes

### Technical Documentation
- Record repair procedures
- Document damage assessment
- Track repair materials used
- Record environmental conditions (temperature, humidity)
- Upload repair photos and documentation

### Reporting & Analytics
- View personal repair statistics
- Track repair completion times
- Monitor success rates
- Record resin usage and other materials
- Generate performance reports

## Technical Documentation

### Models

#### Technician
Extends the Django User model to store technician-specific information.
- **user**: One-to-one relationship with Django User model
- **phone_number**: Contact phone number
- **certification_level**: Skill/certification level of the technician
- **hire_date**: Date when the technician was hired
- **is_active**: Boolean indicating if the technician is currently active

#### Repair
Central model for tracking windshield repairs.
- **technician**: Foreign key to Technician model
- **customer**: Foreign key to Customer model
- **unit_number**: Identifier for the vehicle/unit
- **repair_date**: Date and time when the repair was performed
- **description**: Text description of the repair needed
- **cost**: Decimal field for the repair cost
- **queue_status**: Status of the repair in the workflow (REQUESTED, PENDING, APPROVED, IN_PROGRESS, COMPLETED, DENIED)
- **damage_type**: Type of damage being repaired
- **drilled_before_repair**: Boolean indicating if drilling was performed
- **windshield_temperature**: Temperature of the windshield during repair
- **resin_viscosity**: Viscosity of the resin used for the repair

#### UnitRepairCount
Tracks the number of repairs performed on a specific unit.
- **customer**: Foreign key to Customer model
- **unit_number**: Identifier for the vehicle/unit
- **repair_count**: Number of repairs performed on this unit

#### RepairMaterial
Tracks materials used during repairs.
- **repair**: Foreign key to Repair model
- **material_type**: Type of material used
- **quantity**: Amount of material used
- **cost**: Cost of the materials used

#### RepairPhoto
Stores photos related to repairs.
- **repair**: Foreign key to Repair model
- **photo**: ImageField for storing the photo
- **upload_date**: Date when the photo was uploaded
- **description**: Text description of the photo

### Views

#### Queue Management
- `repair_queue`: Displays all repairs in the queue
- `claim_repair`: Allows technician to claim a repair
- `technician_repairs`: Lists repairs assigned to the logged-in technician
- `update_repair_status`: Updates the status of a repair
- `repair_detail`: Shows detailed information about a repair

#### Repair Documentation
- `document_repair`: Form for adding technical details to a repair
- `upload_repair_photo`: Uploads photos related to a repair
- `record_materials`: Records materials used in a repair

#### Reporting
- `technician_dashboard`: Shows performance metrics and statistics
- `generate_report`: Generates exportable reports of repair activities

#### Account Management
- `technician_profile`: Displays and updates technician profile
- `update_availability`: Updates technician availability for scheduling

### Templates
- **queue.html**: Repair queue listing page
- **technician_repairs.html**: List of repairs assigned to technician
- **repair_detail.html**: Detailed view of a single repair
- **document_repair.html**: Form for documenting repair details
- **upload_photos.html**: Interface for uploading repair photos
- **materials.html**: Form for recording materials used
- **technician_dashboard.html**: Dashboard with performance metrics
- **profile.html**: Technician profile management
- **availability.html**: Calendar for managing availability

### Workflow Stages
The technician portal manages repairs through the following workflow stages:

1. **REQUESTED**: Initial repair request from customer
2. **PENDING**: Awaiting customer approval
3. **APPROVED**: Approved by customer, ready for work
4. **IN_PROGRESS**: Currently being worked on
5. **COMPLETED**: Repair successfully completed
6. **DENIED**: Repair request denied by customer

Each stage has specific actions available to the technician, and transitions between stages are logged and timestamped.

## Integration with Customer Portal

The Technician Portal interacts with the Customer Portal through several mechanisms:

1. **Shared Repair Data**: Both portals access the same repair records but with different permissions
2. **Approval Workflow**: Customer approvals in the Customer Portal affect repair availability in the Technician Portal
3. **Status Updates**: Status changes made by technicians are reflected in the customer's view
4. **Unit Tracking**: The UnitRepairCount model is updated by repair activities and used by both portals

## API Endpoints

### Repair Status Update API
- **Endpoint**: `/technician/api/update-repair-status/`
- **Method**: POST
- **Parameters**: repair_id, new_status
- **Response**: Success message or error
- **Authentication**: Requires technician login
- **Used by**: Mobile app and web interface

### Materials Tracking API
- **Endpoint**: `/technician/api/record-materials/`
- **Method**: POST
- **Parameters**: repair_id, material_data
- **Response**: Success message or error
- **Authentication**: Requires technician login
- **Used by**: Inventory management system

## Usage Guidelines

### For Administrators
- Set up technician accounts and certification levels
- Monitor repair queue and assignment
- Review technician performance metrics
- Configure workflow stages and rules

### For Technicians
- View and claim repairs from the queue
- Update repair status as work progresses
- Document repair details and upload photos
- Record materials used
- Track personal performance metrics

## Dependencies
- Django web framework
- Bootstrap for UI components
- Chart.js for performance visualizations
- Dropzone.js for drag-and-drop file uploads
- FullCalendar for availability scheduling 