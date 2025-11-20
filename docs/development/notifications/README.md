# Notification System Documentation

## Overview

Complete documentation for the RS Systems notification system implementation. This multi-phase project adds comprehensive notification capabilities with email (AWS SES), SMS (AWS SNS), and in-app notifications for technicians, managers, and customers.

## Project Scope

**4-Tier Priority System:**
- **URGENT**: SMS + Email + In-app (approvals, denials, critical assignments)
- **HIGH**: SMS + In-app (new requests, completions, reassignments)
- **MEDIUM**: Email + In-app (status updates, photos, rewards)
- **LOW**: In-app only (notes, minor updates)

**Infrastructure:**
- AWS SES for email delivery
- AWS SNS for SMS delivery
- Celery + Redis for async task processing
- Signal-based event triggers
- Customizable email templates with branding

---

## Phase Documentation

### [Phase 1: Foundation & Models](PHASE_1_FOUNDATION_MODELS.md)
**Timeline**: Days 1-2

Core database models and architecture:
- Unified `Notification` model (polymorphic recipients)
- `NotificationPreference` models (technician & customer)
- `NotificationTemplate` model (reusable templates)
- `NotificationDeliveryLog` model (audit trail)
- Database migrations
- Contact verification fields

**Key Deliverables:**
- All notification models created
- Migrations completed
- Admin interface configured
- Unit tests for models

---

### [Phase 2: AWS Infrastructure](PHASE_2_AWS_INFRASTRUCTURE.md)
**Timeline**: Days 2-3

Cloud infrastructure setup:
- AWS SES configuration (email delivery)
  - Domain verification
  - DKIM setup
  - Sandbox exit
  - IAM permissions
- AWS SNS configuration (SMS delivery)
  - Spending limits
  - Transactional messaging
  - Cost monitoring
- Celery configuration
  - Redis broker setup
  - Worker deployment
  - Beat scheduler
  - Task routing
- Environment configuration

**Key Deliverables:**
- SES verified and production-ready
- SNS configured with spending limits
- Celery workers running
- Test commands for SES/SNS

---

### [Phase 3: Email Customization](PHASE_3_EMAIL_CUSTOMIZATION.md)
**Timeline**: Day 4

Professional email template system:
- `EmailBrandingConfig` model (singleton)
  - Logo upload and optimization
  - Color scheme customization
  - Company information
  - Social media links
- Base email template (HTML + plain text)
  - Responsive design
  - Email client compatibility
  - Brand consistency
- Notification-specific templates
  - Repair approved/denied
  - New assignment
  - Batch operations
  - Status updates
- Admin interface for branding
  - Color picker
  - Logo preview
  - Template preview system

**Key Deliverables:**
- Email branding system functional
- All notification templates created
- Preview system working
- Admin interface intuitive

---

### [Phase 4: Service Layer & Event Triggers](PHASE_4_SERVICE_LAYER.md)
**Timeline**: Days 5-6

Core notification business logic:
- `NotificationService`
  - Create notifications
  - Check preferences
  - Render templates
  - Queue delivery
- `EmailService`
  - Send via SES
  - Handle failures
  - Track delivery
- `SMSService`
  - Send via SNS
  - Phone validation
  - Cost tracking
- Celery tasks
  - Async email delivery
  - Async SMS delivery
  - Retry failed deliveries
  - Daily digest
- Signal handlers
  - Repair status changes
  - Technician assignments
  - Batch operations
  - Automatic triggers

**Key Deliverables:**
- All services implemented
- Signal handlers firing correctly
- Celery tasks executing
- Delivery logs recording attempts

---

### [Phase 5: User Preferences](PHASE_5_USER_PREFERENCES.md)
**Timeline**: Day 6

User interface for notification control:
- Technician preferences page
  - Channel toggles (email, SMS, in-app)
  - Category preferences
  - Quiet hours configuration
  - Daily digest mode
- Customer preferences page
  - Similar controls for customers
  - Batch notification options
- Contact verification
  - Email verification workflow
  - Phone verification (SMS code)
- Notification center
  - Notification bell component
  - Unread count badge
  - Notification dropdown
  - Mark as read functionality
- Notification history
  - Paginated list
  - Filters (read/unread, category)
  - Search functionality

**Key Deliverables:**
- Preference pages functional
- Verification workflows working
- Notification bell displaying unread count
- History view with filters

---

### [Phase 6: Monitoring, Testing & Deployment](PHASE_6_MONITORING_TESTING.md)
**Timeline**: Days 7-8

Production readiness:
- Comprehensive test suite
  - Unit tests (90%+ coverage)
  - Integration tests (signal handlers)
  - End-to-end tests (workflows)
  - Load tests (1000 notifications/min)
- Monitoring setup
  - CloudWatch metrics
  - Custom metrics (volume, delivery, cost)
  - CloudWatch alarms
  - Sentry integration
- Admin dashboard enhancements
  - Notification statistics
  - Delivery log admin
  - Retry actions
- Deployment procedures
  - Pre-deployment checklist
  - Step-by-step deployment
  - Verification steps
  - Gradual rollout plan
- Troubleshooting runbooks
  - Common issues
  - Diagnosis steps
  - Solutions
- Performance optimizations
  - Query optimization
  - Caching strategy
  - Rate limiting

**Key Deliverables:**
- All tests passing
- Monitoring dashboards configured
- Deployment runbook created
- Performance optimized

---

## Quick Start

### Development Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. Create notification templates
python manage.py create_notification_templates

# 4. Configure email branding
python manage.py setup_email_branding

# 5. Start Redis (if not running)
redis-server

# 6. Start Celery worker (separate terminal)
celery -A rs_systems worker --loglevel=info

# 7. Start Celery beat (separate terminal)
celery -A rs_systems beat --loglevel=info

# 8. Run Django server
python manage.py runserver
```

### Testing

```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test apps.core.tests.test_notification_service

# Run with coverage
coverage run --source='.' manage.py test
coverage report

# Test SES connection
python manage.py test_ses your@email.com

# Test SNS connection
python manage.py test_sns +12025551234
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Repair Events                        │
│  (Created, Approved, Denied, Assigned, Completed)       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 Django Signals                          │
│  (post_save handlers detect status changes)            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              NotificationService                        │
│  • Create Notification record                          │
│  • Check user preferences                              │
│  • Render email/SMS templates                          │
│  • Determine delivery channels (priority-based)        │
└──┬──────────────────────────────────────────────────┬───┘
   │                                                  │
   ▼                                                  ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│     Celery Task Queue    │          │   In-App Notification    │
│  (Redis Broker)          │          │  (Database record)       │
└──┬───────────────────┬───┘          └──────────────────────────┘
   │                   │
   ▼                   ▼
┌──────────────┐  ┌──────────────┐
│ EmailService │  │  SMSService  │
│              │  │              │
│ • Render     │  │ • Validate   │
│ • Send (SES) │  │ • Send (SNS) │
│ • Log result │  │ • Log result │
└──────┬───────┘  └──────┬───────┘
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│   AWS SES    │  │   AWS SNS    │
│   (Email)    │  │    (SMS)     │
└──────┬───────┘  └──────┬───────┘
       │                 │
       ▼                 ▼
┌──────────────────────────────────┐
│   NotificationDeliveryLog        │
│  (Audit trail for all deliveries)│
└──────────────────────────────────┘
```

---

## Event-to-Priority Mapping Reference

| Event | Recipient | Priority | Channels | Template |
|-------|-----------|----------|----------|----------|
| Repair created (PENDING) | Customer | HIGH | SMS + In-app | `repair_pending_approval` |
| Repair approved | Technician | URGENT | SMS + Email + In-app | `repair_approved` |
| Repair denied | Technician | URGENT | SMS + Email + In-app | `repair_denied` |
| Technician assigned | Technician | HIGH | SMS + In-app | `repair_assigned` |
| Technician reassigned | Old Tech | MEDIUM | Email + In-app | `repair_reassigned_away` |
| Repair in progress | Customer | MEDIUM | Email + In-app | `repair_in_progress` |
| Repair completed | Customer | HIGH | SMS + In-app | `repair_completed` |
| Batch approved | Technician | URGENT | SMS + Email + In-app | `batch_approved` |
| Batch denied | Technician | URGENT | SMS + Email + In-app | `batch_denied` |
| Reward redemption | Technician | MEDIUM | Email + In-app | `reward_redemption` |

---

## Cost Estimates

**Assumptions:**
- 100 technicians, 50 customers
- 10 notifications/user/day = 1,500/day = 45,000/month

**Monthly Costs:**
- Email (27,000 @ $0.0001): **$2.70**
- SMS (13,500 @ $0.00645): **$87.08**
- Redis ElastiCache (t3.micro): **$12.96**
- **Total: ~$102/month**

**Optimization Tips:**
- Use email for non-urgent (much cheaper)
- Allow SMS opt-out for non-critical categories
- Implement daily digests
- Monitor weekly and adjust

---

## Support & Troubleshooting

### Common Issues

**Emails not sending?**
→ See [Phase 6: Troubleshooting](PHASE_6_MONITORING_TESTING.md#troubleshooting-runbook)

**High SMS costs?**
→ Review priority mapping, encourage email preferences

**Celery tasks stuck?**
→ Check Redis connection, restart workers

**Notifications not triggering?**
→ Verify signals registered in apps.py

### Getting Help

- **Documentation**: Start with phase-specific docs
- **Logs**: Check `/var/log/rs_systems/celery.log`
- **Monitoring**: CloudWatch dashboard
- **Sentry**: Error tracking and stack traces

---

## Next Steps

After completing all 6 phases:

1. **Week 1**: Internal testing with staff
2. **Week 2**: Pilot with 25% of technicians
3. **Week 3**: Full technician rollout
4. **Week 4**: Customer rollout
5. **Month 2**: Optimize based on usage patterns
6. **Quarter 2**: Advanced features (push notifications, webhooks, analytics)

---

## Contributing

When updating notification system:

1. Update appropriate phase documentation
2. Add tests for new functionality
3. Update this README if architecture changes
4. Document any new environment variables
5. Update cost estimates if infrastructure changes

---

## Documentation Updates

**Last Updated**: November 2025
**Version**: 1.0
**Author**: Development Team
**Status**: Ready for Implementation
