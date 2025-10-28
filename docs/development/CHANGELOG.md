# Changelog - RS Systems

All notable changes to the RS Systems windshield repair management platform.

## Format
- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

---

## [1.5.0] - October 25, 2025

### 🎨 MAJOR UI/UX REDESIGN

#### Changed
- **Customer Account Settings Complete Redesign**: Transformed from cluttered Bootstrap forms to professional Tailwind CSS interface
  - **Card-based Layout**: Each section in visually separated cards with color-coded icon badges
  - **Tooltip System**: All help text converted to hover tooltips, reducing clutter by ~60%
  - **Tab Navigation**: Custom-styled tabs with smooth transitions and icons
  - **Better Visual Hierarchy**: Icons, improved typography, consistent spacing throughout
  - **Responsive Design**: Mobile-friendly grid layouts and touch-friendly spacing
  - **Interactive Enhancements**: Smooth animations for show/hide sections, hover states, focus rings
  - Location: `templates/customer_portal/account_settings.html`

#### Added
- **Lot Walking Configuration UI**: Customer-facing settings for configuring lot walking service preferences
  - **Scope**: Customer preferences and UI only - customers can configure when/how often they want lot walking
  - **What's Included**: Enable/disable service, set frequency (weekly/bi-weekly/monthly/quarterly), choose preferred days, set preferred time
  - **What's NOT Included**: Technician scheduling system that generates and manages lot walk schedules (planned for future release - see FUTURE_FEATURES.md)
  - **Data Model**: `CustomerRepairPreference` model stores all settings in database
  - **UI Location**: Customer portal → Account Settings → Repair Preferences tab → Lot Walking Schedule section
  - **Current Limitation**: Preferences are saved but scheduling automation not yet implemented - contact support to arrange lot walks

- **UI Design Guide**: Comprehensive documentation for maintaining consistent design across the system
  - Complete design system (colors, typography, spacing)
  - Reusable component library with code examples
  - Form patterns and interactive elements
  - Migration guide for updating existing pages
  - Icon usage guidelines and best practices
  - Location: `docs/development/UI_DESIGN_GUIDE.md`

#### Technical Details
- Replaced Bootstrap with Tailwind CSS for modern utility-first approach
- Implemented custom tooltip component with hover interactions
- Added conditional section animations with smooth transitions
- Enhanced tab switching with visual feedback
- Color-coded sections: Blue (personal), Yellow (approvals), Green (scheduling), Red (security)
- Professional form styling with focus states and validation feedback

---

## [1.4.0] - October 21, 2025

### 🚨 CRITICAL SECURITY FIXES

#### Security
- **CRITICAL**: Fixed approval bypass vulnerability where technicians could set repair status to COMPLETED to bypass customer approval requirements
  - Server-side enforcement of customer preferences regardless of status selected
  - Prevents unauthorized work and potential fraud
  - Location: `apps/technician_portal/views.py:313-333`

- **HIGH**: Fixed IntegrityError crash when technicians updated their own repairs
  - Preserved existing technician assignment for non-admin users
  - Location: `apps/technician_portal/views.py:381-386`

### Added

#### Manager Assignment System
- Managers can now assign REQUESTED repairs to technicians on their team
- Assignment automatically approves repair (customer already requested it)
- Assigned technicians receive notifications with direct links to repairs
- Team boundary enforcement (managers only assign to technicians they manage)
- New template: `templates/technician_portal/assign_repair.html`

#### Customer Approval Dashboard
- Prominent yellow alert banner for repairs needing approval (cannot be missed)
- Shows repair count, unit details, damage type, technician, cost estimate
- Quick approve/deny buttons directly on dashboard
- Confirmation dialog for deny action
- Mobile-responsive design
- Location: `templates/customer_portal/dashboard.html:200-268`

#### Customer Repair Preferences
- Three approval modes:
  1. **AUTO_APPROVE**: All field repairs auto-approved
  2. **REQUIRE_APPROVAL**: Customer approves every field repair
  3. **UNIT_THRESHOLD**: Auto-approve up to X units per visit
- Server-side enforcement for security
- Admin interface for configuration
- Model: `CustomerRepairPreference` in `apps/customer_portal/models.py`
- Migration: `apps/customer_portal/migrations/0004_customerrepairpreference.py`

#### Notification Enhancements
- Added `repair` ForeignKey to `TechnicianNotification` model
- Notifications now show "View Repair" button linking directly to assigned work
- Works for both repair assignments and reward redemptions
- Migration: `apps/technician_portal/migrations/0008_techniciannotification_repair.py`

#### Repair Status Visibility Controls
- **REQUESTED repairs**: Only visible to managers
  - Non-managers attempting to view get error message
  - Filtered out of non-manager dashboard and repair lists
- **PENDING repairs**: Completely hidden from ALL technicians
  - Only visible in customer portal
  - Cannot be accessed via direct URL
  - Shows error if technician attempts to view

### Changed
- **Repair creation workflow**: Now enforces customer preferences server-side
- **Manager assignment**: Workflow separates customer-requested from field-discovered repairs
- **Dashboard layouts**: Updated for prominent approval alerts and assignment actions
- **Technician notifications**: Enhanced to include repair context and direct links

### Fixed
- Approval bypass vulnerability (technicians setting status to COMPLETED)
- IntegrityError on repair updates (NULL technician_id constraint)
- Missing notification links for assigned repairs
- Manager permission display in admin (managed_technicians field)
- Hidden field labels in repair form templates

### Security
- Server-side validation of customer approval preferences
- Default-deny security model (requires approval if preferences not configured)
- Role-based access control strictly enforced for repair visibility
- Team boundary enforcement for manager assignments

### Files Modified
13 files changed, ~1,023 additions:
- `apps/technician_portal/models.py` - Added repair field to TechnicianNotification
- `apps/technician_portal/views.py` - Security fixes, assignment logic, visibility filters
- `apps/customer_portal/models.py` - Added CustomerRepairPreference model
- `apps/customer_portal/admin.py` - CustomerRepairPreference admin interface
- `apps/customer_portal/views.py` - Approval workflow enhancements
- `templates/customer_portal/dashboard.html` - PENDING repairs alert section
- `templates/technician_portal/dashboard.html` - Notification repair links
- `templates/technician_portal/repair_detail.html` - Assignment button, visibility fixes
- `templates/technician_portal/repair_form.html` - Hide labels for hidden fields
- `templates/technician_portal/assign_repair.html` - NEW: Assignment page
- `apps/technician_portal/admin.py` - Fixed managed_technicians display
- `apps/technician_portal/forms.py` - Form validation updates
- `apps/technician_portal/urls.py` - Assignment URL route

---

## [1.3.0] - September 28, 2025

### 🎯 SPRINT 1: Core Pricing & Roles Infrastructure

#### Added

##### Custom Pricing System
- **CustomerPricing Model**: Customer-specific pricing overrides
  - Custom pricing tiers for 1st-5th+ repairs per unit
  - Volume discount configuration (threshold + percentage)
  - Tracking fields (created_by, timestamps, notes)
  - Model location: `apps/customer_portal/pricing_models.py`
  - Migration: `apps/customer_portal/migrations/0003_customerpricing.py`
  - Admin interface with organized fieldsets

##### Pricing Service Layer
- **Centralized Pricing Logic**: `apps/technician_portal/services/pricing_service.py`
  - `calculate_repair_cost(customer, repair_count)`: Core pricing calculation
  - `calculate_repair_cost_with_volume_discount()`: Applies volume discounts
  - `get_expected_repair_cost(customer, unit_number)`: Preview pricing
  - `can_manager_override_price(technician, amount)`: Permission validation
  - `apply_pricing_to_repair(repair)`: Repair integration
  - `get_pricing_info(customer)`: Comprehensive pricing data

##### Manager Role System
- **Enhanced Technician Model**: Manager capabilities added
  - `is_manager`: Boolean flag for manager status
  - `approval_limit`: Decimal field for override limit (e.g., $150)
  - `can_assign_work`: Permission for work distribution
  - `can_override_pricing`: Permission for pricing overrides
  - `managed_technicians`: M2M for team management

##### Performance Tracking
- **Technician Metrics**:
  - `repairs_completed`: Auto-incremented counter
  - `average_repair_time`: Duration tracking (prepared for future)
  - `customer_rating`: Decimal field for satisfaction scores
  - `is_active`: Availability status
  - `working_hours`: JSON field for schedule

##### Manager Override UI
- **Pricing Override Section**: Visible only to authorized managers
  - Override price input with validation
  - Required reason field for audit trail
  - Displays expected cost and approval limit
  - Form validation checks manager permission and approval limit
  - Template: `templates/technician_portal/repair_form.html:140-170`

##### Admin Enhancements
- **Customer Pricing Admin**:
  - List display with customer, status, created date
  - Filters by use_custom_pricing and creation date
  - Search by customer name and notes
  - Organized fieldsets (Customer Settings, Repair Pricing, Volume Discounts, Tracking)
  - Auto-population of created_by field

- **Technician Admin**:
  - List display shows manager status and active state
  - Filters by expertise, is_manager, is_active, permissions
  - Organized fieldsets (Basic, Manager Capabilities, Performance, Schedule)
  - Horizontal filter for managed technicians M2M

### Changed
- **Repair Cost Calculation**: Now uses pricing service with customer-specific logic
- **Repair.save() Method**: Integrated with pricing service (lines 197-243)
- **Form Validation**: Multi-level validation (form, model, service)

### Fixed
- Template safety check bug (line 140 in repair_form.html)
- Added existence checks for user.technician before attribute access

### Testing
- ✅ 9/9 automated tests passing (see `test_sprint1.py`)
- ✅ Manual testing completed
- ✅ Sprint 1 Audit Report: All features verified and functional
- ✅ No regressions in existing functionality

### Performance
- OneToOne relationship prevents duplicate pricing records
- Indexes on customer and repair count fields
- `select_related` used in admin list views
- `get_or_create` for UnitRepairCount tracking

### Documentation
- Added `FEATURE_REFERENCE_GUIDE.md` - Complete feature explanations
- Added `ADMIN_DASHBOARD_GUIDE.md` - Step-by-step admin instructions
- Added `FEATURE_TESTING_GUIDE.md` - Testing procedures
- Added `SPRINT_1_AUDIT_REPORT.md` - Comprehensive testing results
- Added `QUICK_REFERENCE.md` - Quick user guide

---

## [1.2.0] - August 23, 2025

### Added
- **Automated Backup System**: Daily backups to S3
  - Database backups at 2:00 AM UTC
  - Media file backups
  - 30-day retention
  - Storage: S3 bucket `rs-systems-backups-20250823`
- **Backup Management Commands**: Manual backup triggers
- **Recovery Procedures**: Documented full system recovery

### Security
- **Enhanced Login Attempt Tracking**: IP and user agent logging
- **Security Audit Command**: `python manage.py security_audit`
  - Checks for suspicious users
  - Identifies attack patterns
  - Optional cleanup of bot accounts

---

## [1.1.0] - August 2025

### Added
- **Photo Upload System**: Customer damage photo upload
  - Mobile camera support
  - AWS S3 integration for production
  - Local media storage for development
  - Photo validation (type, size, integrity)
  - Before/after photo display in portals

- **Security Enhancements**:
  - Rate limiting on login (10 attempts/hour per IP)
  - Registration rate limiting (5/hour per IP)
  - Bot protection with honeypot fields
  - Username validation (blocks suspicious patterns)
  - Security headers (CSP, HSTS, X-Frame-Options)

### Changed
- **Forms**: Added `enctype="multipart/form-data"` for photo uploads
- **Models**: Added photo fields to Repair model
- **Settings**: AWS S3 configuration for production media storage

### Fixed
- Form validation error handling
- Mobile responsiveness for photo uploads
- File upload size limits

---

## [1.0.0] - July 2025

### Added
- **Customer Portal**: Self-service portal for fleet managers
  - Repair request submission
  - Status tracking
  - Approval workflow
  - Interactive analytics (D3.js visualizations)
  - Repair history viewing

- **Technician Portal**: Repair management interface
  - Queue-based repair workflow (REQUESTED → PENDING → APPROVED → IN_PROGRESS → COMPLETED)
  - Smart pricing based on unit repair frequency ($50 → $25 scale)
  - Customer and unit management
  - Photo documentation viewing
  - Reward fulfillment

- **Rewards & Referrals System**:
  - Referral code generation
  - Point-based rewards (500 points per referral)
  - Flexible redemption options (percentage discounts, fixed amounts, free services)
  - Automatic reward application to repairs

- **Admin Interface**:
  - User management
  - Repair oversight
  - Reward configuration
  - System analytics

- **Authentication**:
  - Portal separation (customer/technician/admin)
  - Role-based permissions
  - Django group-based access control

- **API**:
  - RESTful API with Django REST Framework
  - Token authentication
  - Interactive Swagger documentation
  - Comprehensive endpoints for repairs, customers, rewards

### Infrastructure
- **Database**: PostgreSQL (production), SQLite (development)
- **Static Files**: WhiteNoise serving
- **Deployment**: AWS Elastic Beanstalk support
- **WSGI Server**: Gunicorn for production

---

## Version History Summary

| Version | Date | Focus | Status |
|---------|------|-------|--------|
| 1.4.0 | Oct 21, 2025 | Critical Security Fixes & Workflow | ✅ Deployed |
| 1.3.0 | Sep 28, 2025 | Sprint 1: Pricing & Roles | ✅ Complete |
| 1.2.0 | Aug 23, 2025 | Backup & Security | ✅ Complete |
| 1.1.0 | Aug 2025 | Photos & Security | ✅ Complete |
| 1.0.0 | Jul 2025 | Initial Release | ✅ Complete |

---

## Upcoming Features

### Sprint 2: Customer Management & Workflow (Planned)
- Fleet management customer settings
- Simplified single approval workflow
- Lot walking implementation with auto-approval
- Batch invoicing

### Sprint 3: Notification System (Planned)
- Email notifications for all repair events
- SMS notifications (Twilio/AWS SNS)
- Webhook system for integrations
- Notification frequency settings

### Sprint 4: Mobile & UX Features (Planned)
- Progressive Web App (PWA) with offline mode
- Mobile camera capture enhancements
- GPS location tracking
- Voice notes capability
- Digital signature capture

---

## Migration Guide

### Upgrading to 1.4.0

**Before Deployment:**
```bash
# 1. Backup database
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > pre_upgrade_backup.sql

# 2. Review changes
git diff v1.3.0..v1.4.0

# 3. Check for breaking changes
# None - this is a backward-compatible update
```

**Deployment Steps:**
```bash
# 1. Deploy application
eb deploy

# 2. Run migrations
eb ssh
cd /var/app/current
source /var/app/venv/*/bin/activate
python manage.py migrate

# 3. Verify critical fixes
# Test customer approval workflow
# Test manager assignment
# Verify security enforcement
```

**Post-Deployment:**
- Configure customer repair preferences via admin
- Test approval workflows with real users
- Monitor security audit logs
- Verify notification links work

---

## Breaking Changes

### Version 1.4.0
- **None**: Fully backward compatible

### Version 1.3.0
- **Repair Pricing**: Now uses pricing service; custom modifications to pricing logic may need updates
- **Manager Permissions**: New permission checks; ensure managers have correct flags set

### Version 1.1.0
- **Media Files**: S3 configuration required for production photo uploads

---

## Deprecation Notices

### Current
- No features currently deprecated

### Future
- **SQLite for Production**: Will be deprecated in future versions (PostgreSQL recommended)
- **Legacy Login URLs** (`/accounts/login/`, `/login/`): Will redirect to portal selection indefinitely but may be removed in v2.0.0

---

## Contributors

- Development Team
- Security Team
- QA Testing Team

---

## Resources

- **Documentation**: `/docs` directory
- **Issue Tracker**: GitHub Issues
- **Security**: `docs/security/INCIDENT_RESPONSE.md`
- **Deployment**: `docs/deployment/AWS_DEPLOYMENT.md`

---

**Latest Version**: 1.4.0
**Last Updated**: October 21, 2025
**Status**: Production Ready ✅
