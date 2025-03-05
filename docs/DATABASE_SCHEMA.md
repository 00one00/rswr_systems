# Database Schema Documentation

## Overview
This document details the database architecture for the RSWR Systems application. The schema supports both the Customer Portal and Technician Portal with a unified data model that enables seamless workflow between the two interfaces while maintaining appropriate data separation and access controls.

## Core Data Models

### Customer
The `Customer` model represents companies or organizations that request windshield repair services.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Unique identifier | Primary Key, Auto-increment |
| name | CharField | Company name | max_length=255, Not Null |
| address | TextField | Physical address | Nullable |
| phone | CharField | Contact phone number | max_length=20, Nullable |
| email | EmailField | Primary contact email | Unique, Not Null |
| created_at | DateTimeField | Account creation timestamp | Auto Now Add |
| updated_at | DateTimeField | Last update timestamp | Auto Now |
| is_active | BooleanField | Whether account is active | Default=True |

**Key Behaviors:**
- Company names are automatically converted to lowercase during save for consistency
- Email address must be unique to prevent duplicate customer accounts
- Customer record deletion cascades to related repairs and user accounts

### Repair
The `Repair` model is the central entity that tracks all windshield repair operations from request to completion.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Unique identifier | Primary Key, Auto-increment |
| technician | ForeignKey | Assigned technician | FK to Technician, Cascade |
| customer | ForeignKey | Customer requesting repair | FK to Customer, SET_NULL, Nullable |
| unit_number | CharField | Vehicle/unit identifier | max_length=50, Not Null |
| repair_date | DateTimeField | When repair was created/performed | Default=now |
| description | TextField | Detailed repair description | Nullable |
| cost | DecimalField | Calculated repair cost | max_digits=10, decimal_places=2, Default=0 |
| queue_status | CharField | Current workflow status | Choices, max_length=20, Default='PENDING' |
| damage_type | CharField | Type of windshield damage | max_length=50, Not Null |
| drilled_before_repair | BooleanField | If drilling was performed | Default=False |
| windshield_temperature | FloatField | Temperature during repair | Nullable |
| resin_viscosity | CharField | Viscosity of resin used | max_length=50, Nullable |

**Queue Status Options:**
- `REQUESTED`: Initial customer-submitted request
- `PENDING`: Awaiting customer approval
- `APPROVED`: Approved by customer, ready for work
- `IN_PROGRESS`: Currently being worked on
- `COMPLETED`: Repair successfully completed
- `DENIED`: Repair request denied by customer

**Key Behaviors:**
- Cost is automatically calculated based on repair count for the unit
- When marked as completed, the `UnitRepairCount` is automatically updated
- Original status is tracked during changes to enable appropriate workflow actions

### UnitRepairCount
The `UnitRepairCount` model tracks the number of repairs performed on each customer's vehicles/units.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Unique identifier | Primary Key, Auto-increment |
| customer | ForeignKey | Customer owning the unit | FK to Customer, Cascade |
| unit_number | CharField | Vehicle/unit identifier | max_length=50 |
| repair_count | IntegerField | Number of repairs performed | Default=0 |

**Unique Constraint:** (customer, unit_number) - Ensures one record per unit per customer

**Key Behaviors:**
- Auto-increments the repair count when a repair is completed
- Used for cost calculation based on repair frequency
- Can be reset when a unit is replaced

## User-Related Models

### Technician
The `Technician` model extends Django's User model with technician-specific information.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Unique identifier | Primary Key, Auto-increment |
| user | OneToOneField | Django user account | FK to User, Cascade |
| phone_number | CharField | Contact phone number | max_length=20, Nullable |
| expertise | CharField | Specialization/skill level | max_length=100, Nullable |

**Key Behaviors:**
- Links standard Django authentication to technician-specific data
- Enables role-based access control for the Technician Portal
- Associates repairs with specific technicians

### CustomerUser
The `CustomerUser` model links Django User accounts to Customer entities.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Unique identifier | Primary Key, Auto-increment |
| user | OneToOneField | Django user account | FK to User, Cascade |
| customer | ForeignKey | Associated customer | FK to Customer, Cascade |
| is_primary_contact | BooleanField | Primary contact designation | Default=False |

**Key Behaviors:**
- Enables multiple users per customer account
- Designates primary contacts who have additional permissions
- Controls access to the Customer Portal and customer-specific data

### CustomerPreference
The `CustomerPreference` model stores customization options for the Customer Portal.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Unique identifier | Primary Key, Auto-increment |
| customer | OneToOneField | Associated customer | FK to Customer, Cascade |
| receive_email_notifications | BooleanField | Email notification preference | Default=True |
| receive_sms_notifications | BooleanField | SMS notification preference | Default=False |
| default_view | CharField | Default dashboard view | Choices, max_length=20, Default='pending' |

**Key Behaviors:**
- Customizes customer experience in the portal
- Controls notification settings
- Persists user interface preferences

## Workflow-Related Models

### RepairApproval
The `RepairApproval` model tracks customer approvals for repairs.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Unique identifier | Primary Key, Auto-increment |
| repair | OneToOneField | Associated repair | FK to Repair, Cascade |
| approved | BooleanField | Approval status | Nullable |
| approved_by | ForeignKey | User who approved/denied | FK to CustomerUser, SET_NULL, Nullable |
| approval_date | DateTimeField | When approval was made | Nullable |
| notes | TextField | Approval/denial notes | Nullable |

**Key Behaviors:**
- Records who approved or denied a repair and when
- Stores reasoning behind approval decisions
- Contains special handling for customer-initiated repairs

## Planned Future Models

### RepairMaterial
Tracks materials used during repairs (planned implementation).

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Unique identifier | Primary Key, Auto-increment |
| repair | ForeignKey | Associated repair | FK to Repair, Cascade |
| material_type | CharField | Type of material | max_length=100 |
| quantity | DecimalField | Amount used | max_digits=8, decimal_places=2 |
| cost | DecimalField | Material cost | max_digits=10, decimal_places=2 |
| recorded_at | DateTimeField | When recorded | Auto Now Add |

### RepairPhoto
Stores photos related to repairs (planned implementation).

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Unique identifier | Primary Key, Auto-increment |
| repair | ForeignKey | Associated repair | FK to Repair, Cascade |
| photo | ImageField | Photo file | upload_to='repair_photos/' |
| upload_date | DateTimeField | Upload timestamp | Auto Now Add |
| description | TextField | Photo description | Nullable |

### TechnicianSchedule
Manages technician availability and work schedule (planned implementation).

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Unique identifier | Primary Key, Auto-increment |
| technician | ForeignKey | Associated technician | FK to Technician, Cascade |
| date | DateField | Schedule date | Not Null |
| start_time | TimeField | Shift start time | Not Null |
| end_time | TimeField | Shift end time | Not Null |
| is_available | BooleanField | Availability flag | Default=True |
| notes | TextField | Schedule notes | Nullable |

**Unique Constraint:** (technician, date, start_time) - Prevents scheduling conflicts

## Entity Relationship Diagram

```
+------------+       +---------------+       +------------+
| Customer   |<------| CustomerUser  |------>| User       |
+------------+       +---------------+       +------------+
      ^               (1:N)                        ^
      |                                           |
      |                                           |
      |               +---------------+           |
      |<--------------| CustomerPref  |           |
      |               +---------------+           |
      |                                           |
      |                                           |
      |               +-------------+             |
      |               | Technician  |------------>|
      |               +-------------+             |
      |                     ^                     |
      |                     |                     |
      |               +----------------+          |
      |               | TechSchedule   |          |
      |               +----------------+          |
      |                                           |
      |                                           |
      |                                           |
      |               +------------+              |
      |<--------------| Repair     |<------------>|
      |               +------------+              |
      |                     ^                     |
      |                     |                     |
      |               +----------------+          |
      |               | RepairApproval |--------->|
      |               +----------------+          |
      |                                           |
      |               +---------------+           |
      |<--------------| UnitRepairCount|          |
      |               +---------------+           |
      |                                           |
      |                                           |
      |               +--------------+            |
      |               | RepairMaterial|           |
      |               +--------------+            |
      |                     ^                     |
      |                     |                     |
      |               +--------------+            |
      |               | RepairPhoto  |            |
      |               +--------------+            |
      |                                           |
      |               +--------------+            |
      |               | RepairLog    |<---------->|
      |               +--------------+            |
```

## Database Relationships

### One-to-One Relationships
- User <-> Technician: Each Django User can be associated with at most one Technician profile
- User <-> CustomerUser: Each Django User can be associated with at most one CustomerUser profile
- Customer <-> CustomerPreference: Each Customer has exactly one preferences record
- Repair <-> RepairApproval: Each Repair has at most one approval record

### One-to-Many Relationships
- Customer -> CustomerUser: One customer can have multiple user accounts
- Customer -> Repair: One customer can have many repairs
- Customer -> UnitRepairCount: One customer can have many units with repair counts
- Technician -> Repair: One technician can perform many repairs
- Technician -> TechnicianSchedule: One technician has many schedule entries
- Repair -> RepairMaterial: One repair can use many materials
- Repair -> RepairPhoto: One repair can have many documentation photos
- Repair -> RepairLog: One repair can have many status change log entries

### Many-to-Many Relationships
The database schema doesn't use explicit many-to-many relationships through Django's ManyToManyField. Instead, relationships are modeled using ForeignKey and OneToOneField to maintain explicit control over relationship attributes.

## Database Performance Optimizations

### Indexes
The following indexes are implemented to optimize database performance:

#### Primary Indexes
- All tables have a primary key index on their `id` field

#### Foreign Key Indexes
- Django automatically creates indexes on all foreign key fields

#### Custom Indexes
- `Repair.queue_status`: Indexed for efficient filtering of repairs by status
- `Repair.customer`: Indexed to optimize customer-based repair lookups
- `Repair.technician`: Indexed to quickly find repairs assigned to specific technicians
- `Repair.repair_date`: Indexed for date-based filtering and sorting
- `UnitRepairCount.(customer, unit_number)`: Compound index for unique constraint and lookups
- `TechnicianSchedule.(technician, date)`: Compound index for schedule availability queries

### Query Optimization
When implementing views that access the database, the following optimization techniques are used:

- `select_related()` for eager loading of foreign key relationships
- `prefetch_related()` for optimized loading of reverse foreign key and many-to-many relationships
- Query-specific indexes for complex filtering operations
- Limited result sets with pagination to avoid retrieving unnecessary data

## Model Signals and Triggers

The database uses Django signals to maintain data consistency and implement business logic:

### Repair Status Change
When a Repair's `queue_status` field changes:
- A signal handler creates a new `RepairLog` entry to track the change
- If changed to "COMPLETED", a handler updates the corresponding `UnitRepairCount` record
- Cost calculation is triggered based on the repair count

### RepairApproval Creation
When a `RepairApproval` record is created or updated:
- If `approved=True`, the corresponding `Repair.queue_status` is updated to "APPROVED"
- If `approved=False`, the `Repair.queue_status` is updated to "DENIED"
- Notification signals may be triggered to alert relevant users

### User Creation
When users are created with specific roles:
- Users marked as technicians automatically get Technician profiles
- Users marked as customers get CustomerUser associations
- Default preferences are created for new customers

## Data Integrity and Constraints

### Unique Constraints
- `Customer.email`: Ensures unique email addresses for customers
- `UnitRepairCount.(customer, unit_number)`: One record per customer's unit
- `TechnicianSchedule.(technician, date, start_time)`: Prevents overlapping schedules

### Foreign Key Constraints
- Most relationships use `CASCADE` for deletions to maintain referential integrity
- Some use `SET_NULL` to preserve historical data even if related records are deleted

### Data Validation
Before saving to the database, Django models perform validation:
- Field type validation (strings, numbers, dates, etc.)
- Length constraints for text fields
- Range validation for numeric fields
- Custom validators for business logic

## Database Evolution Strategy

The database schema is designed to evolve with the application:

1. **Migration Planning**: Changes are planned to minimize disruption
2. **Testing**: Migrations are tested on development environments first
3. **Backup**: Production data is backed up before migrations
4. **Execution**: Migrations are applied during scheduled maintenance
5. **Verification**: Data integrity is verified after migration

### Future Expansion Areas
- **Repair Types**: Adding specialized fields for different repair techniques
- **Customer Categories**: Extending Customer model with categorization
- **Enhanced Reporting**: Adding aggregation tables for performance
- **Audit Trails**: Expanding logging for regulatory compliance

## Security Considerations

The database design incorporates several security features:

1. **Access Control**: All database access is mediated through Django's ORM with permission checks
2. **Query Isolation**: Customer data is filtered by appropriate permissions
3. **Audit Logging**: Critical changes are recorded in log tables
4. **Data Protection**: Sensitive fields use appropriate encryption methods
5. **SQL Injection Prevention**: Django's ORM provides protection against SQL injection

## Developer Guidelines

When working with the database schema:

1. **Use the ORM**: Avoid raw SQL in favor of Django's ORM methods
2. **Optimize Queries**: Use appropriate methods to minimize database load
3. **Transactional Operations**: Use `transaction.atomic()` for operations affecting multiple tables
4. **Migration Best Practices**:
   - Create and test migrations in development first
   - Use `RunPython` for data migrations requiring logic
   - Make migrations reversible whenever possible
   - Document complex migrations with comments

5. **Model Methods vs. Database Functions**:
   - Use model methods for business logic that spans multiple fields
   - Use database functions for operations that can be performed entirely in the database
   - Consider performance implications for large datasets

6. **Error Handling**:
   - Implement appropriate exception handling for database operations
   - Log database errors with sufficient context for debugging
   - Use retry mechanisms for transient failures