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

## [1.6.1] - October 29, 2025

### 🔧 ADMIN ENHANCEMENTS

#### Added
- **Lot Walking Admin Configuration**: Full admin dashboard support for configuring customer lot walking preferences
  - **New Admin Fieldset**: "Lot Walking Service Settings" section in CustomerRepairPreference admin
  - **Enhanced Form**: `CustomerRepairPreferenceForm` now includes lot walking fields with custom widgets
  - **Day Selection**: Checkbox widget for selecting preferred days of the week (Monday-Sunday)
  - **Time Picker**: Time input widget with Django admin styling for preferred time selection
  - **Frequency Dropdown**: Select from Weekly, Bi-weekly, Monthly, or Quarterly schedules
  - **Form Validation**: Automatic validation ensures frequency is required when lot walking is enabled (time and days are optional)
  - **Data Storage**: Preferences stored in existing `CustomerRepairPreference.lot_walking_days` JSONField
  - **Location**: `apps/customer_portal/admin.py:88-202`

- **Enhanced Admin List Display**: Better visibility of lot walking settings at a glance
  - Added `lot_walking_enabled` column to list view (✓/✗ indicator)
  - Added `lot_walking_frequency` column showing schedule (Weekly/Bi-weekly/Monthly/Quarterly)
  - List view now shows: Customer | Approval Mode | Threshold | Lot Walking | Frequency | Updated

- **Advanced Filtering**: Quick filters for lot walking configuration
  - Filter by lot walking enabled (Yes/No)
  - Filter by lot walking frequency (Weekly/Bi-weekly/Monthly/Quarterly)
  - Combined with existing approval mode and date filters
  - Enables quick searches like "Show all customers with weekly lot walking"

#### Changed
- **CustomerRepairPreferenceForm**: Extended with lot walking UI components
  - Added `lot_walking_days_choices` field with checkbox widget
  - Custom `__init__()` method pre-populates checkboxes from JSON data
  - Custom `save()` method converts checkbox selections to JSON list
  - Enhanced `clean()` method validates lot walking dependencies
  - Time field widget styled with Django admin classes (`vTimeField`)

- **CustomerRepairPreferenceAdmin**: Reorganized with lot walking section
  - New fieldset between "Field Repair Approval Settings" and "Tracking"
  - Clear section description explaining lot walking configuration
  - Updated list_display to show lot walking status
  - Updated list_filter for lot walking options

#### Technical Details
- **No Database Changes**: Uses existing `lot_walking_enabled`, `lot_walking_frequency`, `lot_walking_time`, and `lot_walking_days` fields from `CustomerRepairPreference` model (added in v1.5.0)
- **Form Widget Pattern**: Converts between JSONField storage and checkbox UI seamlessly
- **Validation Rules**:
  - `lot_walking_frequency` required when `lot_walking_enabled` is True
  - `lot_walking_time` optional (preferred time can be left blank)
  - `lot_walking_days_choices` optional (defaults to empty list if not selected)
- **Admin Integration**: Fully integrated with Django admin using standard ModelAdmin patterns

#### Benefits
- ✅ Admins can configure lot walking schedules without database access
- ✅ User-friendly checkboxes replace manual JSON editing
- ✅ Time picker provides consistent time format
- ✅ Form validation prevents incomplete configurations
- ✅ List filters enable quick overview of lot walking customers
- ✅ Complements customer-facing lot walking UI from v1.5.0

#### Documentation Updates
- **Admin Guide**: Added "Lot Walking Service Configuration" section (lines 302-351)
- **Admin Guide**: Added Example 4 showing lot walking customer workflow (lines 391-406)
- **Admin Guide**: Added Task 6 for configuring lot walking service (lines 535-552)
- **Admin Guide**: Updated version to 1.6.1 and date to October 29, 2025

### Files Modified
2 files changed, ~140 additions:
- `apps/customer_portal/admin.py` - Enhanced form and admin configuration
- `docs/user-guides/ADMIN_GUIDE.md` - Documentation updates

---

## [1.6.0] - October 29, 2025

### 📸 IMAGE UPLOAD ENHANCEMENTS

#### Added
- **HEIC/HEIF Image Support**: Native iPhone photo format support for unedited AI training photos
  - Automatic conversion to JPEG for browser compatibility
  - Pillow-HEIF integration for server-side image processing
  - High-quality conversion (95% JPEG quality) preserves image details
  - Transparent conversion - users upload HEIC, system stores JPEG
  - Extensions: `.heic`, `.heif` now accepted alongside `.jpg`, `.jpeg`, `.png`, `.webp`
  - Location: `common/utils.py:convert_heic_to_jpeg()`

- **Increased Upload Size Limits**: Expanded from 2.5MB to 10MB
  - Django settings: `DATA_UPLOAD_MAX_MEMORY_SIZE` and `FILE_UPLOAD_MAX_MEMORY_SIZE` set to 10MB
  - AWS Nginx configuration: `client_max_body_size` set to 10MB
  - Application validation remains at 5MB with clear error messages
  - Supports high-resolution photos for AI model training
  - Locations: `rs_systems/settings.py`, `rs_systems/settings_aws.py`, `.ebextensions/00_nginx_upload.config`

- **Image Conversion Utility**: New shared utility module for image processing
  - Handles HEIC to JPEG conversion
  - Graceful error handling (returns original file if conversion fails)
  - Maintains filename with changed extension (.heic → .jpg)
  - Updates MIME type for proper browser handling
  - Location: `common/utils.py`

#### Fixed
- **Localhost Upload Failures**: "Not an image or corrupted image" error for files 2.5MB-5MB
  - Root cause: Django's 2.5MB default limit smaller than validation limit
  - Solution: Increased Django upload limits to 10MB

- **AWS Upload Failures**: "413 Request Entity Too Large" error
  - Root cause: Nginx default 1MB limit rejected uploads before reaching Django
  - Solution: Added nginx configuration for 10MB client_max_body_size

- **HEIC Preview Issues**: HEIC images uploaded but didn't display in browser
  - Root cause: Browsers don't support HEIC format natively
  - Solution: Automatic server-side conversion to JPEG on upload

#### Changed
- **Photo Field Validators**: Extended to accept HEIC/HEIF extensions
  - `damage_photo_before` and `damage_photo_after` now accept 6 formats
  - Help text updated to mention HEIC support
  - Migration: `apps/technician_portal/migrations/0009_alter_repair_damage_photo_after_and_more.py`

- **Upload Validation**: MIME type checks now include HEIC formats
  - Customer portal: `image/heic` and `image/heif` added to allowed types
  - Error messages updated to mention HEIC support
  - Location: `apps/customer_portal/views.py:619`

- **View Processing**: All upload views now convert HEIC to JPEG automatically
  - Customer portal: `request_repair` view
  - Technician portal: `create_repair` and `update_repair` views
  - Conversion happens before form processing
  - Locations: `apps/customer_portal/views.py`, `apps/technician_portal/views.py`

#### Technical Details
- **Dependencies Added**: `pillow-heif==1.1.1` for HEIC support
- **Plugin Registration**: Auto-registers HEIC opener on app startup
  - Location: `apps/technician_portal/apps.py:ready()`
- **AWS Deployment Ready**: All configurations compatible with Elastic Beanstalk
- **File Formats Supported**: JPEG, PNG, WebP, HEIC, HEIF
- **Max File Size**: 10MB (system) / 5MB (validation with user-friendly error)

#### Benefits
- ✅ Users can upload unedited iPhone photos directly
- ✅ High-resolution photos supported for AI training
- ✅ Browser compatibility maintained (all photos viewable)
- ✅ Consistent user experience across all devices
- ✅ No user action required (automatic conversion)
- ✅ Better image quality for damage documentation

### Files Modified
11 files changed, ~250 additions:
- `common/utils.py` - NEW: HEIC conversion utility
- `requirements.txt` - Added pillow-heif dependency
- `rs_systems/settings.py` - Increased upload size limits
- `rs_systems/settings_aws.py` - Increased upload size limits
- `.ebextensions/00_nginx_upload.config` - NEW: Nginx upload configuration
- `apps/technician_portal/models.py` - Extended file validators
- `apps/technician_portal/apps.py` - Registered HEIC plugin
- `apps/customer_portal/views.py` - HEIC conversion + validation
- `apps/technician_portal/views.py` - HEIC conversion in create/update
- `apps/technician_portal/migrations/0009_*.py` - NEW: Photo field migration

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
| 1.6.1 | Oct 29, 2025 | Admin Lot Walking Configuration | ✅ Complete |
| 1.6.0 | Oct 29, 2025 | Image Upload Enhancements | ✅ Complete |
| 1.5.0 | Oct 25, 2025 | UI/UX Redesign & Lot Walking | ✅ Complete |
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

**Latest Version**: 1.6.1
**Last Updated**: October 29, 2025
**Status**: Production Ready ✅
