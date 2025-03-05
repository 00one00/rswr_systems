# Portal Interactions and Shared Components

## Overview
The RSWR Systems application consists of two primary portals: the Customer Portal and the Technician Portal. While these portals serve different user groups with distinct needs, they share underlying data structures and interact with each other through several mechanisms. This document outlines how these portals interact and what components they share.

## Shared Data Models

### Core Models
Both portals interact with these shared core models:

#### Repair
The central model that stores all repair information, accessed by both portals with different permissions:
- **Customer Portal**: Views status, requests approvals, initiates new repairs
- **Technician Portal**: Updates status, adds technical details, documents work

#### Customer
Stores customer information:
- **Customer Portal**: Accessed as the current user's organization
- **Technician Portal**: Referenced to identify which customer a repair belongs to

#### UnitRepairCount
Tracks repair counts for specific customer units:
- **Customer Portal**: Used for visualizations in dashboards
- **Technician Portal**: Updated when repairs are completed

### Linking Models

#### CustomerUser
Links Django User accounts to Customer records:
- **Primary Use**: Customer Portal
- **Technician Portal Interaction**: Used to identify customer contacts

#### RepairApproval
Tracks customer approval status for repairs:
- **Primary Use**: Customer Portal for approving/denying
- **Technician Portal Interaction**: Determines if work can proceed

## Workflow Interactions

### Repair Lifecycle
1. **Initiation**:
   - Customer creates repair request in Customer Portal
   - Status set to REQUESTED
   - Appears in Technician Portal queue

2. **Approval Process**:
   - Customer approves/denies in Customer Portal
   - RepairApproval record created/updated
   - Status changes to APPROVED or DENIED
   - If approved, appears as available in Technician Portal

3. **Work Process**:
   - Technician claims repair in Technician Portal
   - Updates status to IN_PROGRESS
   - Customer sees status update in Customer Portal

4. **Completion**:
   - Technician marks repair as COMPLETED
   - Updates UnitRepairCount
   - Customer sees completion in Customer Portal
   - Repair appears in history for both portals

### State Synchronization
- Status changes in either portal are immediately reflected in the other
- Approval actions in Customer Portal affect work availability in Technician Portal
- Technical details added in Technician Portal appear in detailed views for customers
- Cost calculations in Technician Portal affect billing information seen by customers

## Technical Implementation

### Database Transaction Management
- Atomic transactions ensure data consistency across portals
- Status changes are locked to prevent race conditions
- Signal handlers update related models when primary models change

### Permission Management
- Customers can only see their own repairs
- Technicians can see all repairs but have limited edit rights on completed repairs
- Administrators have full access to both portals

### API and Backend Services

#### Shared Endpoints
Some API endpoints serve both portals with permission-based filtering:
- Repair detail lookups
- Unit information

#### Portal-Specific Endpoints
- Customer Portal: Approval actions, visualization data
- Technician Portal: Queue management, material tracking

### Authentication and Authorization
- Django's authentication system controls access to both portals
- Group-based permissions separate customer users from technician users
- Some views check user type to redirect to appropriate portal

## Data Visualization Bridge

### Repair Statistics
- Technician Portal generates repair data
- Customer Portal visualizes this data for customers
- Both portals may show the same metrics but with different scope:
  - Customers see only their repairs
  - Technicians see their assigned repairs or all repairs

### UnitRepairCount Updates
1. Technician completes a repair
2. Trigger updates the UnitRepairCount
3. Customer Portal uses this data for the "Repairs by Unit" visualization

## File and Media Sharing

### Repair Photos
- Uploaded via Technician Portal
- Viewable in Customer Portal repair details
- Stored in shared media directory with permission controls

### Documentation
- Technical documentation created in Technician Portal
- Summary information visible to customers
- Detailed information only visible to technicians

## Communication Bridge

### Notifications
- Status changes trigger notifications
- Customer approvals notify assigned technicians
- Repair completions notify customers

### Comments and Notes
- Internal notes (technician-only)
- Customer-visible notes
- Permission system controls visibility

## Integration Points Summary

| Feature | Customer Portal | Technician Portal | Interaction Method |
|---------|----------------|-------------------|-------------------|
| Repair Status | View | Update | Shared Model, Database Triggers |
| Repair Details | View Limited Info | Create, View Full Info | Shared Model with Permission Filtering |
| Repair Approval | Approve/Deny | View Approval Status | RepairApproval Model |
| Unit Tracking | View Statistics | Update Counts | UnitRepairCount Model |
| Documentation | View Summaries | Create, Upload | Shared FileField with Permission Controls |
| Notifications | Receive | Generate | Django Signals, Email/SMS Service |

## Considerations for Developers

### Adding New Features
When adding features that affect both portals:
1. Consider permission implications
2. Update both portal interfaces as needed
3. Ensure notifications flow appropriately
4. Test from both user perspectives

### Debugging Interactions
When troubleshooting cross-portal issues:
1. Check permission settings
2. Verify signal handlers are functioning
3. Test transaction integrity
4. Review notification logs

### Performance Considerations
- Shared queries should be optimized and cached when possible
- Consider using select_related and prefetch_related for related model access
- Use database indexes for frequently queried fields
- Implement appropriate caching for visualizations and statistics 