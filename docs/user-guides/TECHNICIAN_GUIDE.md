# Technician Portal Guide

User guide for repair technicians using the RS Systems platform.

## Quick Start

**Portal URL**: `https://[your-domain]/tech/login/`
**Login**: Use your assigned username and password

---

## Dashboard Overview

After login, your dashboard shows:

1. **Customer Requested Repairs** (Managers only)
   - Repairs submitted by customers
   - Status: REQUESTED
   - Action: Assign to team members

2. **My Assigned Repairs**
   - Repairs assigned to you
   - Status: APPROVED, IN_PROGRESS
   - Action: Work on and complete

3. **Notifications**
   - New assignments
   - Reward redemptions
   - System alerts

4. **Quick Stats**
   - Repairs completed today
   - Pending assignments
   - Notifications unread

---

## Working with Repairs

### View Repair Details

```
Click any repair to see:
- Customer information
- Unit number
- Damage type
- Status
- Cost estimate
- Photos (if uploaded)
- Notes (customer and technician)
```

### Update Repair Status

**Status Flow**:
```
REQUESTED → (Manager assigns) → APPROVED
APPROVED → IN_PROGRESS → COMPLETED → CLOSED
```

**Actions**:
1. Click "Edit" on repair
2. Update status to next stage
3. Add technician notes
4. Upload completion photos (optional)
5. Save

### Adding Photos

```
1. Edit repair
2. Scroll to "Photo Documentation"
3. Before photo: [Choose file]
4. After photo: [Choose file]
5. Additional photos: [Choose files]
6. Save
```

**Photo Tips**:
- Clear, well-lit images
- Show damage clearly
- Before AND after photos
- Max 5MB per photo
- Formats: JPG, PNG

---

## Creating Field Repairs

When you find damage during inspection:

```
1. Click "Create New Repair"
2. Fill form:
   - Customer: [Select]
   - Unit number: UNIT123
   - Damage type: CHIP/CRACK/BULLSEYE
   - Damage description: "Chip in driver view area"
   - Technician notes: "Found during lot walk"
3. Upload photos
4. Submit
```

**Important**:
- System checks customer approval preferences
- May require customer approval before work
- If "PENDING", wait for customer to approve
- If "APPROVED", you can proceed with work

### Customer Approval Requirements

**AUTO_APPROVE Customers**:
- Your repair is APPROVED immediately
- Start work right away
- Complete and invoice

**REQUIRE_APPROVAL Customers**:
- Your repair goes to PENDING
- Customer sees alert on their dashboard
- Wait for customer approval
- You'll get notification when approved

---

## Manager Features

*Available only if you're designated as a manager*

### Assigning Customer-Requested Repairs

```
1. Dashboard shows "Customer Requested Repairs"
2. Click on REQUESTED repair
3. Click "Assign to Technician"
4. Select technician from dropdown
5. Submit assignment
```

**What Happens**:
- Repair status → APPROVED
- Assigned tech gets notification
- Notification includes direct link to repair
- You can only assign to technicians on your team

### Pricing Override

*Available if you have override permission*

```
1. Create or edit repair
2. Scroll to "Manager Pricing Override"
3. Enter override price: $75.00
4. Enter reason: "Customer complaint - goodwill gesture"
5. Save
```

**Limits**:
- Cannot exceed your approval limit
- Reason is required
- System tracks all overrides
- Use sparingly

**When to Override**:
- Customer complaints
- Special circumstances
- Damage caused by technician error
- VIP customer goodwill

**When NOT to Override**:
- Regular discounts (use custom pricing)
- Every repair (unsustainable)
- Without good reason (audit trail)

---

## Repair Workflows

### Workflow 1: Customer-Requested Repair

*For managers assigning work*

```
1. Customer submits request
   Status: REQUESTED

2. You see it on dashboard
   (Non-managers don't see REQUESTED)

3. Assign to technician
   Status: APPROVED
   Tech gets notification

4. Tech completes work
   Status: IN_PROGRESS → COMPLETED

5. Closed after invoicing
   Status: CLOSED
```

### Workflow 2: Field-Discovered (Auto-Approve)

*Customer has auto-approve enabled*

```
1. You find damage during inspection
2. Create repair
   System checks preferences
   Status: APPROVED immediately

3. Complete repair
   Status: IN_PROGRESS → COMPLETED

4. Invoice customer
   Status: CLOSED
```

### Workflow 3: Field-Discovered (Requires Approval)

*Customer requires approval*

```
1. You find damage during inspection
2. Create repair
   System checks preferences
   Status: PENDING

3. Repair disappears from your view
   (Customer portal only)

4. Customer approves on their dashboard
   You get notification
   Status: APPROVED

5. Complete repair
   Status: IN_PROGRESS → COMPLETED

6. Invoice customer
   Status: CLOSED
```

---

## Visibility Rules

### What You Can See

**Regular Technicians**:
- ✓ APPROVED repairs assigned to you
- ✓ IN_PROGRESS repairs you're working on
- ✓ COMPLETED repairs you finished
- ✗ REQUESTED repairs (managers only)
- ✗ PENDING repairs (customer approval)

**Managers**:
- ✓ REQUESTED repairs (for assignment)
- ✓ All APPROVED repairs
- ✓ Team members' repairs
- ✗ PENDING repairs (customer approval)

**Why You Can't See PENDING**:
- These need customer approval
- Customer sees them on their dashboard
- You'll get notification when approved
- Prevents confusion and duplicate work

---

## Notifications

### Types

1. **Assignment Notifications**
   ```
   "You have been assigned Repair #123 for ABC Logistics - Unit 456"
   [View Repair] button
   ```

2. **Approval Notifications**
   ```
   "Repair #123 has been approved by customer"
   [View Repair] button
   ```

3. **Reward Redemptions**
   ```
   "Customer redeemed reward - awaiting fulfillment"
   [View Details] button
   ```

### Managing Notifications

```
1. Click notification bell icon
2. View unread notifications
3. Click "View Repair" or "View Details"
4. Notification marked as read
```

---

## Pricing Information

### How Repair Costs Are Calculated

**Standard Pricing** (per unit):
- 1st repair: $50
- 2nd repair: $40
- 3rd repair: $35
- 4th repair: $30
- 5th+ repairs: $25

**Custom Pricing** (some customers):
- Customer-specific rates
- Set by admin
- You'll see correct price automatically

**Volume Discounts**:
- Applied after customer reaches threshold
- Automatic calculation
- Shows in repair cost

**Manager Overrides**:
- Manually set price
- Requires reason
- Within approval limit

### Expected Cost Display

When creating/editing repairs:
```
Expected cost: $40.00
(Based on 2nd repair for this unit)
```

This helps you know what to expect before finalizing.

---

## Best Practices

### Documentation
- ✓ Add clear technician notes
- ✓ Upload before/after photos
- ✓ Describe damage accurately
- ✓ Note any complications

### Communication
- ✓ Update status promptly
- ✓ Add notes about delays
- ✓ Contact manager for issues
- ✓ Explain override reasons clearly

### Professionalism
- ✓ Complete work thoroughly
- ✓ Keep customers informed
- ✓ Follow approval processes
- ✓ Maintain quality standards

### Efficiency
- ✓ Batch similar repairs
- ✓ Take photos during inspection
- ✓ Update status in real-time
- ✓ Use quick actions when available

---

## Troubleshooting

### "I can't see a repair I created"

**Likely Cause**: Repair is PENDING customer approval

**Solution**:
- Check customer's approval preferences
- Wait for customer approval notification
- Contact manager if urgent

### "Override section not showing"

**Check**:
- Are you a manager? ✓
- Do you have override permission? ✓
- Are you in /tech/ portal (not /admin/)? ✓

**Solution**: Contact admin to grant manager permissions

### "Assignment list is empty"

**Possible Reasons**:
- No customers have submitted requests
- Requests already assigned by other managers
- You're not designated as a manager

**Solution**: Check with team lead or admin

### "Can't update repair status"

**Check**:
- Is repair assigned to you? ✓
- Are you following proper status flow? ✓
- Is form showing validation errors? ✓

**Solution**: Review error messages, contact support if persists

---

## Mobile Tips

### Using on Mobile Device

**Photo Capture**:
- Use native camera button
- Take photos in good lighting
- Ensure focus is clear
- Upload immediately

**Quick Actions**:
- Dashboard optimized for mobile
- Large touch targets
- Simplified forms
- Fast status updates

**Best Practices**:
- Use portrait orientation for forms
- Landscape for photos
- Save frequently
- Check upload confirmations

---

## Quick Reference

### Status Meanings

| Status | Meaning | Your Action |
|--------|---------|-------------|
| REQUESTED | Customer wants repair | Assign (managers only) |
| PENDING | Awaiting customer approval | Wait for notification |
| APPROVED | Ready to work | Start repair |
| IN_PROGRESS | Work underway | Complete repair |
| COMPLETED | Work done | System will invoice |
| CLOSED | Invoiced | Done - view only |

### Common Actions

| Task | Steps |
|------|-------|
| View repairs | Dashboard → Click repair |
| Create repair | "Create New Repair" → Fill form → Save |
| Update status | Edit repair → Change status → Save |
| Add photos | Edit repair → Upload files → Save |
| Override price | Edit → Override section → Enter price + reason |
| Assign repair | Repair detail → "Assign" → Select tech |

---

**Last Updated**: October 21, 2025
**For**: RS Systems v1.4.0
**Support**: Contact your team lead or system administrator
