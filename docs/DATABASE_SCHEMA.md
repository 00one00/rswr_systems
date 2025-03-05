# Database Schema Documentation

## Overview
This document outlines the database schema for the RS Wind Repair Systems application. The database is designed to support both the Customer Portal and Technician Portal, with shared models for core functionality and portal-specific models for specialized features.

## Database Structure

### Core Models

#### Customer
Represents a company or organization that requests windshield repairs.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Primary key | PK, Auto-increment |
| name | CharField | Company name | max_length=255, Not Null |
| address | TextField | Physical address | Nullable |
| phone | CharField | Contact phone number | max_length=20, Nullable |
| email | EmailField | Contact email | Unique, Not Null |
| created_at | DateTimeField | Account creation date | Auto Now Add |
| updated_at | DateTimeField | Last update timestamp | Auto Now |
| is_active | BooleanField | Account status | Default=True |

#### Repair
Central model that tracks all windshield repair operations.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Primary key | PK, Auto-increment |
| technician | ForeignKey | Assigned technician | FK to Technician, Cascade, Nullable |
| customer | ForeignKey | Customer requesting repair | FK to Customer, SET_NULL, Nullable |
| unit_number | CharField | Vehicle/unit identifier | max_length=50, Not Null |
| repair_date | DateTimeField | When repair was performed | Default=now |
| description | TextField | Repair description | Nullable |
| cost | DecimalField | Cost of repair | max_digits=10, decimal_places=2, Default=0.00 |
| queue_status | CharField | Current workflow status | Choices, max_length=20, Default='PENDING' |
| damage_type | CharField | Type of damage | max_length=50, Nullable |
| drilled_before_repair | BooleanField | If drilling was performed | Default=False |
| windshield_temperature | FloatField | Temperature during repair | Nullable |
| resin_viscosity | CharField | Viscosity of resin used | max_length=50, Nullable |
| created_at | DateTimeField | Record creation date | Auto Now Add |
| updated_at | DateTimeField | Last update timestamp | Auto Now |

#### UnitRepairCount
Tracks the number of repairs performed on each customer unit.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Primary key | PK, Auto-increment |
| customer | ForeignKey | Customer owning the unit | FK to Customer, Cascade |
| unit_number | CharField | Vehicle/unit identifier | max_length=50 |
| repair_count | IntegerField | Number of repairs performed | Default=0 |

**Unique Constraint**: (customer, unit_number)

### Customer Portal Models

#### CustomerUser
Links Django User accounts to Customer entities.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Primary key | PK, Auto-increment |
| user | OneToOneField | Django user | FK to User, Cascade |
| customer | ForeignKey | Associated customer | FK to Customer, Cascade |
| is_primary_contact | BooleanField | Primary contact flag | Default=False |

#### CustomerPreference
Stores customer preferences for the portal.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Primary key | PK, Auto-increment |
| customer | OneToOneField | Customer | FK to Customer, Cascade |
| receive_email_notifications | BooleanField | Email notification preference | Default=True |
| receive_sms_notifications | BooleanField | SMS notification preference | Default=False |
| default_view | CharField | Default dashboard view | Choices, max_length=20, Default='REPAIRS' |

#### RepairApproval
Tracks customer approvals for repairs.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Primary key | PK, Auto-increment |
| repair | OneToOneField | Associated repair | FK to Repair, Cascade |
| approved | BooleanField | Approval status | Nullable |
| approved_by | ForeignKey | User who approved | FK to CustomerUser, SET_NULL, Nullable |
| approval_date | DateTimeField | When approval was made | Nullable |
| notes | TextField | Additional notes | Nullable |

### Technician Portal Models

#### Technician
Extends the Django User model for technician-specific information.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Primary key | PK, Auto-increment |
| user | OneToOneField | Django user | FK to User, Cascade |
| phone_number | CharField | Contact phone | max_length=20, Nullable |
| certification_level | CharField | Skill level | Choices, max_length=20 |
| hire_date | DateField | Hire date | Nullable |
| is_active | BooleanField | Active status | Default=True |

#### RepairMaterial
Tracks materials used during repairs.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Primary key | PK, Auto-increment |
| repair | ForeignKey | Associated repair | FK to Repair, Cascade |
| material_type | CharField | Type of material | max_length=100 |
| quantity | DecimalField | Amount used | max_digits=8, decimal_places=2 |
| cost | DecimalField | Material cost | max_digits=10, decimal_places=2 |
| recorded_at | DateTimeField | When recorded | Auto Now Add |

#### RepairPhoto
Stores photos related to repairs.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Primary key | PK, Auto-increment |
| repair | ForeignKey | Associated repair | FK to Repair, Cascade |
| photo | ImageField | Photo file | upload_to='repair_photos/' |
| upload_date | DateTimeField | Upload timestamp | Auto Now Add |
| description | TextField | Photo description | Nullable |

#### TechnicianSchedule
Manages technician availability and work schedule.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Primary key | PK, Auto-increment |
| technician | ForeignKey | Associated technician | FK to Technician, Cascade |
| date | DateField | Schedule date | Not Null |
| start_time | TimeField | Shift start time | Not Null |
| end_time | TimeField | Shift end time | Not Null |
| is_available | BooleanField | Availability flag | Default=True |
| notes | TextField | Schedule notes | Nullable |

**Unique Constraint**: (technician, date, start_time)

#### RepairLog
Tracks detailed history of repair status changes.

| Field | Type | Description | Constraints |
|-------|------|-------------|------------|
| id | AutoField | Primary key | PK, Auto-increment |
| repair | ForeignKey | Associated repair | FK to Repair, Cascade |
| previous_status | CharField | Status before change | Choices, max_length=20 |
| new_status | CharField | Status after change | Choices, max_length=20 |
| changed_by | ForeignKey | User making change | FK to User, SET_NULL, Nullable |
| timestamp | DateTimeField | When change occurred | Auto Now Add |
| notes | TextField | Change notes | Nullable |

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
- User <-> Technician
- User <-> CustomerUser
- Customer <-> CustomerPreference
- Repair <-> RepairApproval

### One-to-Many Relationships
- Customer -> CustomerUser (one customer, many users)
- Customer -> Repair (one customer, many repairs)
- Customer -> UnitRepairCount (one customer, many units)
- Technician -> Repair (one technician, many repairs)
- Technician -> TechnicianSchedule (one technician, many schedule entries)
- Repair -> RepairMaterial (one repair, many materials)
- Repair -> RepairPhoto (one repair, many photos)
- Repair -> RepairLog (one repair, many log entries)

### Many-to-Many Relationships
- No direct many-to-many relationships are implemented using Django's ManyToManyField.
- All relationships are modeled using ForeignKey or OneToOneField.

## Indexes and Performance Optimizations

### Primary Indexes
- All tables have a primary key index on their `id` field.

### Foreign Key Indexes
- Django automatically creates indexes on foreign key fields.

### Custom Indexes
- `Repair.queue_status`: Indexed for filtering repairs by status.
- `Repair.customer`: Indexed for filtering repairs by customer.
- `Repair.technician`: Indexed for filtering repairs by technician.
- `Repair.repair_date`: Indexed for date-based queries.
- `UnitRepairCount.(customer, unit_number)`: Compound index for unique constraint.
- `TechnicianSchedule.(technician, date)`: Compound index for schedule lookups.

## Database Triggers and Signals

### Model Signals

1. **Repair Status Change**:
   - When `Repair.queue_status` changes, a signal handler creates a new `RepairLog` entry.
   - If changed to "COMPLETED", updates the `UnitRepairCount` for the customer and unit.

2. **RepairApproval Creation**:
   - When a `RepairApproval` is created with `approved=True`, updates the corresponding `Repair.queue_status` to "APPROVED".
   - When a `RepairApproval` is created with `approved=False`, updates the corresponding `Repair.queue_status` to "DENIED".

3. **Repair Material Tracking**:
   - When a `RepairMaterial` is created or updated, a signal handler updates the `Repair.cost` field.

4. **User Creation**:
   - When a `User` with `is_technician=True` is created, automatically creates a corresponding `Technician` record.
   - When a `User` with `is_customer=True` is created, automatically creates a corresponding `CustomerUser` record.

## Data Migrations and Evolution

The schema is designed to support future expansions:

1. **Adding Repair Types**: The `Repair` model can be extended with additional fields for specialized repair types.
2. **Enhanced User Profiles**: `CustomerUser` and `Technician` models can be extended with additional profile fields.
3. **Workflow Customization**: The `queue_status` choices can be expanded to support more detailed workflow states.
4. **Reporting Metrics**: Additional models can be added for storing aggregated reporting data.

## Database Constraints and Data Integrity

### Unique Constraints
- `Customer.email`: Ensures unique email addresses for customers.
- `UnitRepairCount.(customer, unit_number)`: Ensures one count record per unit per customer.
- `TechnicianSchedule.(technician, date, start_time)`: Prevents scheduling conflicts.

### Foreign Key Constraints
- Most relationships use `CASCADE` for deletions to maintain data integrity.
- Some use `SET_NULL` where keeping history is important even if related records are deleted.

## Search Optimization

### Full Text Search
The application uses Django's database-agnostic query filtering. For production deployments with PostgreSQL, consider adding:

- Full-text search indexes on `Repair.description`
- Trigram similarity indexes for partial matching on `Customer.name` and `UnitRepairCount.unit_number`

## Backup and Recovery

Database backup strategies should include:

1. Regular full database backups
2. Point-in-time recovery capability
3. Transaction log backups
4. Data export utilities for key entities

## Security Considerations

The database design incorporates several security features:

1. **No direct model access**: All database access is mediated through Django's ORM.
2. **Permission-based filtering**: Queries filter data based on user permissions.
3. **Audit trails**: Changes to critical data like repair status are logged in `RepairLog`.
4. **Sensitive data protection**: User authentication is handled by Django's User model.

## Best Practices for Developers

When working with the database:

1. Use Django's ORM and avoid raw SQL when possible.
2. Leverage `select_related()` and `prefetch_related()` to optimize queries.
3. Use transactions for operations that modify multiple related records.
4. Follow migration best practices for schema changes:
   - Create and test migrations in development environments
   - Back up production data before applying migrations
   - Use RunPython for data migrations that require business logic 