# Future Features & Next Steps - RS Systems

**Last Updated**: October 21, 2025
**Purpose**: Track planned features for future implementation

---

## ✅ RECENTLY COMPLETED

### Customer Settings UI & Repair Preferences ✅ COMPLETED October 25, 2025
**What**: Improved account settings page with repair preference controls and lot walking configuration
**Status**: ✅ Implemented and tested
**Completed**: October 25, 2025

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
