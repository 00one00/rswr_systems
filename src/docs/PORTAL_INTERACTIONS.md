# Portal Interactions and Shared Components

## Overview
The RSWR Systems application consists of two primary user interfaces: the Customer Portal and the Technician Portal. Though these portals serve different user groups with distinct needs, they interact with shared data structures and coordinate workflow processes to create a seamless experience. This document explains how these portals communicate, which components they share, and how data flows between them.

## Shared Data Architecture

### Core Shared Models
Both portals interact with the same underlying database models, but with different access patterns and permissions:

#### Repair Model
The central entity connecting both portals:
- **Customer Portal Usage**: Customers view repair status, submit repair requests, and approve/deny repairs
- **Technician Portal Usage**: Technicians update repair details, change status, and document work performed
- **Data Flow**: Status changes in either portal are immediately reflected in the other

#### Customer Model
Company information shared across portals:
- **Customer Portal Usage**: Displayed as the user's own organization
- **Technician Portal Usage**: Referenced to identify which customer a repair belongs to
- **Data Flow**: Profile updates in Customer Portal are visible to technicians

#### UnitRepairCount Model
Tracks repair history for specific vehicles:
- **Customer Portal Usage**: Powers data visualizations on the dashboard
- **Technician Portal Usage**: Updated when repairs are completed and used for cost calculations
- **Data Flow**: Incremented by technician actions, visualized for customers

### Bridging Models
These models specifically connect the two portals:

#### CustomerUser Model
Links Django users to customer companies:
- **Primary Usage**: Customer Portal login and permissions
- **Technician Portal Interaction**: Used to identify primary contacts
- **Permission Role**: Limits customer users to seeing only their company's data

#### RepairApproval Model
Tracks the customer approval workflow:
- **Primary Usage**: Created/updated when customers approve or deny repairs
- **Technician Portal Interaction**: Determines which repairs can proceed to work
- **Permission Role**: Ensures work is performed only on approved repairs

## Workflow Interactions

### Complete Repair Lifecycle
The repair process spans both portals in a coordinated workflow:

#### 1. Initiation Phase
- **Customer-Initiated**: 
  - Customer creates repair request in Customer Portal
  - Status automatically set to REQUESTED
  - Appears in Technician Portal under customer requests queue
  - Technician reviews and can accept or deny

- **Technician-Initiated**:
  - Technician creates repair record in Technician Portal
  - Status automatically set to PENDING
  - Appears in Customer Portal awaiting approval
  - Customer must review and approve/deny

#### 2. Approval Process
- Customer views pending repair in Customer Portal
- Customer approves or denies the repair:
  - On approval, a RepairApproval record is created with `approved=True`
  - On denial, a RepairApproval record is created with `approved=False`
- Status changes to APPROVED or DENIED based on customer decision
- If approved, the repair appears as available for work in Technician Portal

#### 3. Work Phase
- Technician claims repair in Technician Portal
- Status updated to IN_PROGRESS
- Customer sees real-time status update in Customer Portal
- Technician adds technical details (temperature, resin viscosity, etc.)

#### 4. Completion Phase
- Technician marks repair as COMPLETED in Technician Portal
- System automatically:
  - Updates the UnitRepairCount for that customer/unit
  - Calculates the final cost based on repair history
- Repair appears in completed history for both portals
- Customer can view final details in Customer Portal

### Status Synchronization
Status changes operate with these guarantees:

- **Real-time Updates**: Changes are immediately visible in both portals
- **Workflow Enforcement**: Portal interfaces only allow valid status transitions
- **Audit Trail**: Status changes are logged with timestamp and user information
- **Notifications**: Status changes can trigger notifications to relevant parties

## Implementation Architecture

### Database Level Integration

#### Transaction Management
- **Atomic Operations**: Multi-step processes use database transactions
- **Consistency Protection**: Status changes have appropriate locks
- **Signal Framework**: Django signals update related models

#### Data Access Patterns
- **Shared Models, Different Views**: Both portals query the same tables but expose different fields
- **Permission Filtering**: Database queries automatically filter by user permissions
- **Prefetch Optimization**: Related data is loaded efficiently to reduce database load

### API Layer Integration

#### Authentication & Authorization
- **Auth System**: Django's authentication handles portal access
- **Permission Classes**: Different user types have different capabilities
- **Login Routing**: Users are directed to appropriate portal based on role

#### Portal-Specific APIs
Each portal exposes its own optimized API endpoints:

- **Customer Portal APIs**:
  - Unit repair data visualization
  - Repair frequency analysis
  - Approval workflow actions

- **Technician Portal APIs**:
  - Repair queue management
  - Technical detail recording
  - Status update workflow

#### Shared API Patterns
Common patterns across all APIs:
- **Consistent Response Format**: All APIs use standard response structures
- **Error Handling**: Standardized error reporting with appropriate HTTP codes
- **Input Validation**: Data validation follows consistent rules
- **Pagination**: Large datasets are paginated with consistent controllers

### Frontend Integration

#### Data Flow Architecture
Data flows between portals through these mechanisms:

1. **Database Updates**: Most communication flows through database changes
2. **Status Notifications**: Status changes trigger appropriate UI updates
3. **Session Data**: User context maintains consistent state
4. **API Responses**: Standardized API responses ensure data consistency

#### Visualization Data Flow
A key integration point is the data visualization process:
1. Technician actions generate repair data
2. Data is processed and stored in the database
3. Customer Portal APIs access processed data
4. D3.js visualizations render the data for customers

## Cross-Portal Features

### Data Visualization Bridge
- Repair statistics generated in Technician Portal flow to Customer Portal visualizations
- Both portals may show similar metrics but scoped to appropriate access:
  - Customers see only their company's data
  - Technicians see assigned repairs or all repairs (administrators)

### Document Sharing
- Repair documentation flows between portals with appropriate permissions
- Technical specifications recorded by technicians are selectively visible to customers
- Photos and documentation are stored in shared storage but with access controls

### Communication Channels
Several features bridge communication between portals:

#### Status-Based Notifications
- Status changes trigger appropriate notifications
- Customer approvals notify assigned technicians
- Repair completions may notify customers

#### Comments and Notes
- Internal notes visible only to technicians
- Customer-facing notes visible in both portals
- Approval reasons and technical notes with role-based visibility

## Integration Testing Strategy

Testing these integrations follows these approaches:

### 1. End-to-End Workflow Testing
- Complete repair lifecycle testing from creation through completion
- Multi-user scenarios with both portal types simultaneously
- Validation of data consistency across portals

### 2. Status Transition Testing
- Testing all valid and invalid status transitions
- Stress testing concurrent status updates
- Validation of correct permissions for status changes

### 3. Data Consistency Testing
- Verification that data changes in one portal correctly appear in the other
- Performance testing of data synchronization
- Edge case testing for unusual data scenarios

## Troubleshooting Integration Issues

When debugging cross-portal issues, consider these common areas:

### 1. Permission Problems
- Check if user has correct role assignment
- Verify row-level permissions are filtering correctly
- Examine view-level permission checks

### 2. Signal Handler Issues 
- Verify signal handlers are registered and executing
- Check for exceptions in signal handlers
- Examine transaction boundaries that might affect signals

### 3. Synchronization Timing
- Look for race conditions in near-simultaneous updates
- Check transaction isolation levels
- Verify correct locking strategy for critical updates

### 4. Data Consistency Errors
- Validate model save methods for unexpected behaviors
- Check for partial updates in multi-step processes
- Review serialization/deserialization for API data

## Developer Guidelines

### Adding New Integrated Features
When implementing features that span both portals:

1. **Design for Both Perspectives**:
   - Consider how the feature appears to customers
   - Design technician interactions with the same data
   - Document the integration points clearly

2. **Follow Integration Patterns**:
   - Use established patterns for cross-portal communication
   - Leverage the signal system for updates
   - Maintain consistent permission strategy

3. **Test Both Sides**:
   - Create tests from both customer and technician perspectives
   - Validate correct data visibility and permissions
   - Test performance impact on both portals

4. **Document Integration Points**:
   - Note which models bridge between portals
   - Document status transitions and triggers
   - Explain permission implications

## Optimization Considerations

### Performance Optimization
- Use query optimization for shared models
- Consider caching for frequently accessed repair data
- Implement database indexes for common lookup patterns

### UI Responsiveness
- Handle loading states for cross-portal operations
- Provide feedback for operations that trigger workflows
- Implement optimistic UI updates where appropriate

### Scalability Planning
- Design for increasing numbers of repairs and customers
- Optimize database access for shared models
- Consider partitioning or sharding for very large deployments