# Future Features & Next Steps - RS Systems

**Last Updated**: October 21, 2025
**Purpose**: Track planned features for future implementation

---

## ✅ RECENTLY COMPLETED

### Customer Settings UI & Repair Preferences ✅ COMPLETED October 25, 2025
**What**: Improved account settings page with repair preference controls and lot walking configuration
**Status**: ✅ Implemented and tested (Customer-facing preferences UI only)
**Completed**: October 25, 2025
**Note**: This is the customer-facing configuration UI where customers set their lot walking preferences. The technician-side scheduling system that USES these preferences is a separate future feature (see below).

**What Was Delivered**:
1. ✅ Redesigned `templates/customer_portal/account_settings.html` with modern tabbed interface:
   - Tab 1: Personal Info (first name, last name, email)
   - Tab 2: Repair Preferences (NEW - configure approval workflow + lot walking)
   - Tab 3: Security (password change)

2. ✅ Updated `apps/customer_portal/views.py` account_settings view:
   - Implemented get_or_create pattern for CustomerRepairPreference
   - Added RepairPreferenceForm handling
   - Integrated form validation and saving

3. ✅ Created `apps/customer_portal/forms.py`:
   - RepairPreferenceForm with ModelForm pattern
   - Custom handling for JSONField (lot walking days)
   - Dynamic field visibility with JavaScript

4. ✅ Extended `CustomerRepairPreference` model with lot walking fields:
   - `lot_walking_enabled` - Enable/disable scheduled lot walking
   - `lot_walking_frequency` - Weekly, Bi-weekly, Monthly, Quarterly
   - `lot_walking_time` - Preferred time for lot walking
   - `lot_walking_days` - Selected days of week (JSONField)

**Repair Preference Features**:
- AUTO_APPROVE: Auto-approve all field repairs
- REQUIRE_APPROVAL: Customer approves each repair
- UNIT_THRESHOLD: Auto-approve up to X units per visit (with configurable threshold)

**Lot Walking Features**:
- Enable/disable lot walking service
- Set frequency (Weekly/Bi-weekly/Monthly/Quarterly)
- Specify preferred time
- Select preferred days of the week
- All settings stored in CustomerRepairPreference model

**Files Modified**:
- `apps/customer_portal/models.py` - Added lot walking fields to CustomerRepairPreference
- `apps/customer_portal/forms.py` - NEW: Created RepairPreferenceForm
- `apps/customer_portal/views.py` - Updated account_settings view with form handling
- `templates/customer_portal/account_settings.html` - Complete redesign with tabs

**Migration**: `0005_customerrepairpreference_lot_walking_days_and_more`

---

## 🎯 IMMEDIATE NEXT STEPS (Start Here Next Session)

### Lot Walking Scheduler Implementation (Technician-Side)
**Effort**: 4-5 days
**Priority**: HIGH - Customer UI is complete, need backend scheduling
**Status**:
- ✅ Customer preferences UI complete (customers can configure settings)
- ❌ Scheduling system not implemented (preferences are stored but not used)
- ❌ Technician interface not implemented

**Current State**:
- `apps/scheduling/` app exists but ALL files are empty (0 lines of code)
- `CustomerRepairPreference` model stores: `lot_walking_enabled`, `lot_walking_frequency`, `lot_walking_time`, `lot_walking_days`
- Data is saved to database but no code reads/uses these preferences yet

**What Needs Implementation**:

**1. Scheduling App Models** (`apps/scheduling/models.py` - currently empty):
```python
class LotWalkSchedule(models.Model):
    customer = models.ForeignKey(Customer)
    technician = models.ForeignKey(Technician)
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    frequency = models.CharField()  # Mirrors customer preference
    status = models.CharField(choices=['SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'])
    created_from_preference = models.BooleanField(default=True)
    notes = models.TextField()

class LotWalkRoute(models.Model):
    schedule = models.ForeignKey(LotWalkSchedule)
    customer_order = models.IntegerField()  # Route sequence
    estimated_duration = models.DurationField()
    actual_start_time = models.DateTimeField()
    actual_end_time = models.DateTimeField()
```

**2. Schedule Generation Service** (`apps/scheduling/services.py` - currently empty):
```python
class LotWalkScheduler:
    def generate_schedules_from_preferences():
        # Read all CustomerRepairPreference with lot_walking_enabled=True
        # For each preference:
        #   - Calculate next schedule date based on frequency
        #   - Match to available days (lot_walking_days)
        #   - Create LotWalkSchedule records
        #   - Assign to available technicians

    def assign_technician_to_schedule():
        # Smart assignment based on:
        #   - Technician availability (working_hours)
        #   - Geographic proximity
        #   - Current workload
        #   - Customer preferred_technicians
```

**3. Technician Calendar View** (new):
- File: `templates/technician_portal/lot_walk_calendar.html`
- View: `apps/scheduling/views.py` (currently empty)
- Features:
  - Calendar display (day/week/month views)
  - Show scheduled lot walks with customer names
  - Click to see lot walk details
  - Mark as started/completed
  - Add ad-hoc lot walks

**4. Mobile Lot Walking Interface**:
- Route list for technicians (ordered by location)
- GPS integration for navigation
- Quick repair creation during lot walk (auto-tags as lot walk repair)
- Checklist of customers on route
- Mark each customer inspection complete
- Summary report generation

**5. Notification System**:
- Technician: "You have a lot walk scheduled for [Customer] tomorrow at [Time]"
- Technician: Morning reminder on day of lot walk
- Customer: "Technician [Name] is starting your lot walk"
- Customer: "Lot walk complete - [X] repairs found" (with approval links if needed)

**6. Management Commands** (for automation):
```bash
python manage.py generate_lot_walk_schedules  # Run daily via cron
python manage.py send_lot_walk_reminders      # Run in morning
```

**7. Integration with Existing Repair Workflow**:
- When technician creates repair during lot walk, tag with lot_walk_schedule_id
- Apply customer's field_repair_approval_mode automatically
- Group repairs from same lot walk visit for reporting
- Link repairs to lot walk schedule for tracking

**Files to Create/Modify**:
- `apps/scheduling/models.py` (currently 0 lines) - Add Schedule models
- `apps/scheduling/services.py` (currently 0 lines) - Add scheduler service
- `apps/scheduling/views.py` (currently 0 lines) - Add calendar views
- `apps/scheduling/urls.py` (currently 0 lines) - Add URL routes
- `templates/technician_portal/lot_walk_calendar.html` - NEW
- `templates/technician_portal/lot_walk_route.html` - NEW
- `core/management/commands/generate_lot_walk_schedules.py` - NEW
- `core/management/commands/send_lot_walk_reminders.py` - NEW

**Testing Checklist**:
- [ ] Customer preferences automatically generate schedules
- [ ] Schedules respect customer's selected days/times
- [ ] Technicians see schedules in calendar view
- [ ] Technicians receive notifications before lot walks
- [ ] Repairs created during lot walk are properly tagged
- [ ] Lot walk completion updates schedule status
- [ ] Route optimization works for multiple customers

**Dependencies**:
- ✅ CustomerRepairPreference model (complete)
- ❌ Scheduling app buildout (empty)
- ❌ Enhanced notification system
- ❌ Mobile interface improvements

---

## 🚀 READY TO IMPLEMENT (After Settings UI)

### 1. Fleet Management Customer Settings
**Effort**: 1-2 days

Add fields to Customer model (`core/models.py`):
```python
fleet_size = models.IntegerField(default=0)
service_mode = models.CharField(choices=['SCHEDULED', 'ON_CALL', 'HYBRID'])
payment_terms = models.CharField(choices=['NET_30', 'NET_60', 'PREPAID'])
preferred_technicians = models.ManyToManyField('technician_portal.Technician')
```

### 2. Batch Operations for Repairs
**Effort**: 3-4 days

Features:
- Multi-select checkboxes on repair lists
- Bulk assign repairs to technician
- Group status updates
- Batch actions with confirmation dialogs

Files to create:
- `apps/technician_portal/services/batch_service.py`
- `static/js/batch_operations.js`

### 3. Advanced Repair Filtering
**Effort**: 1-2 days

Add filters to repair lists:
- Date range picker
- Status multi-select
- Customer/technician filter
- Unit number search
- Cost range

Consider using django-filter package.

---

## 📧 EMAIL NOTIFICATION SYSTEM (Deferred)

**Status**: No email infrastructure configured yet
**Dependencies**: SendGrid or AWS SES account

Features needed:
- Email on repair status changes
- Approval request notifications
- Daily/weekly digest emails
- User notification preferences

Environment variables needed:
```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_key
```

---

## 💰 INVOICING & BILLING (Deferred)

**Status**: Not in current codebase
**Priority**: High for business operations
**Effort**: 3-4 weeks

Features:
- Auto-generate invoices on repair completion
- Batch invoicing (multiple repairs → one invoice)
- PDF download (use WeasyPrint or ReportLab)
- Payment status tracking
- Optional: Stripe/Square integration

Models to create:
- Invoice (invoice_number, customer, total, status, due_date)
- InvoiceLineItem (invoice, repair, description, amount)

---

## 📊 ANALYTICS DASHBOARD (Deferred)

Features:
- Technician performance metrics
- Revenue analysis by customer/technician/month
- Repair pattern trends
- Export to CSV/Excel

---

## 📱 MOBILE PWA FEATURES (Deferred)

Features:
- Offline mode with service workers
- Camera capture for repair photos
- GPS location tracking
- Voice notes
- Digital signatures
- Push notifications

---

## 🔮 ADVANCED FEATURES (Long-term)

- **Smart Assignment**: Auto-assign repairs based on workload, distance, skills
- **Predictive Maintenance**: Analyze patterns, predict failures
- **Quality Assurance**: Photo verification, customer surveys, warranty tracking
- **API Integrations**: Webhooks, third-party system integrations

---

## 📝 SUGGESTED PRIORITY ORDER

1. Customer Settings UI (immediate next step)
2. Batch Operations
3. Advanced Filtering
4. Fleet Management Settings
5. Invoicing System
6. Email Notifications
7. Analytics Dashboard
8. Mobile PWA
9. Smart Assignment
10. Predictive Maintenance

---

## 📚 Related Documentation

- `docs/development/WORKFLOW_IMPLEMENTATION.md` - Sprint tracking
- `docs/development/CHANGELOG.md` - Version history
- `docs/deployment/AWS_DEPLOYMENT.md` - Deployment guide
