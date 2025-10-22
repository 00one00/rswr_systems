# Customer Portal Guide

User guide for customers using the RS Systems platform.

## Quick Start

**Portal URL**: `https://[your-domain]/app/login/`
**Registration**: `https://[your-domain]/app/register/`

---

## Getting Started

### Creating an Account

```
1. Visit registration page
2. Fill company information:
   - Company name
   - Contact name
   - Email address
   - Phone number
   - Address
3. Create password (minimum 8 characters)
4. Submit registration
5. You're automatically logged in
```

### First Login

After registration or subsequent logins:
```
1. Visit customer portal login page
2. Enter email and password
3. Click "Login"
4. Dashboard loads with your company's repairs
```

---

## Dashboard Overview

Your dashboard shows:

### 1. Pending Approvals (If Any)

**Yellow Alert Banner**:
```
⚠ 2 Repairs Awaiting Your Approval

Technicians found damage during inspection.
Review and approve/deny repairs below.
```

**Shows For Each Repair**:
- Unit number
- Damage type
- Technician name
- Estimated cost
- Technician notes
- Photos (if uploaded)
- **Approve** button (green)
- **Deny** button (red)

### 2. Repair Summary

- Total repairs
- Active repairs
- Completed repairs
- This month's repairs

### 3. Recent Repairs

List of your company's recent repairs with:
- Unit number
- Status
- Date
- Cost
- Technician

### 4. Quick Actions

- Submit Repair Request
- View All Repairs
- View Units
- Account Settings

---

## Submitting Repair Requests

When you know a unit needs service:

```
1. Click "Submit Repair Request"
2. Fill form:
   - Unit number: TRUCK-101
   - Damage type: CHIP / CRACK / BULLSEYE
   - Damage description: "Chip in driver view area, about 2 inches"
   - Location: (Optional) Where on windshield
3. Upload photos (recommended):
   - Click "Choose file" or use camera
   - Take clear photo of damage
   - Upload
4. Submit request
```

**What Happens Next**:
1. Your request is created (Status: REQUESTED)
2. Manager assigns technician to your repair
3. Repair is auto-approved (you already requested it)
4. Technician completes work
5. You receive invoice

**Expected Cost Display**:
```
Based on this unit's repair history,
estimated cost: $40.00

(This is an estimate - final cost calculated upon completion)
```

---

## Approving/Denying Field Repairs

When technician finds damage during inspection:

### Viewing Pending Repairs

**Yellow Alert Banner Appears**:
```
⚠ Repairs Awaiting Your Approval

Unit: TRUCK-203
Damage: CHIP
Technician: John Smith
Cost: $50.00
Notes: "Small chip found during scheduled lot walk,
        driver side, near wiper area. Recommend
        immediate repair to prevent spread."

[Approve] [Deny] [View Details]
```

### Approving a Repair

```
1. Review repair details
2. Check:
   - Is damage description accurate?
   - Is cost acceptable?
   - Is repair necessary?
3. Click "Approve" button
4. Repair status → APPROVED
5. Technician gets notification
6. Work can proceed
```

### Denying a Repair

```
1. Review repair details
2. If you don't want repair done
3. Click "Deny" button
4. Confirmation dialog appears:
   "Are you sure? This will cancel the repair request."
5. Confirm denial
6. Repair cancelled
7. Technician notified
```

**Why You Might Deny**:
- Unit scheduled for disposal
- Damage assessment incorrect
- Cost too high for current budget
- Prefer to handle internally

---

## Repair Approval Settings

Control how field-discovered repairs are handled.

### Three Options

**Option 1: Auto-Approve All** (Most Convenient)
```
Technicians can fix what they find immediately.
No approval needed.

Good for:
- Emergency services
- High-trust relationships
- Time-sensitive repairs
```

**Option 2: Require Approval** (Most Control)
```
You must approve every field-discovered repair.
Yellow alerts appear on dashboard.

Good for:
- Tight budget control
- Want to review all costs
- Prefer detailed oversight
```

**Option 3: Unit Threshold** (Balanced)
```
Auto-approve up to X units per visit,
then require approval for additional units.

Good for:
- Predictable costs
- Flexible control
- Large fleets
```

### Changing Your Settings

*Currently admin-only. Contact support to change your approval mode.*

**Future**: Self-service settings in Account Settings section.

---

## Viewing Repair History

### All Repairs View

```
1. Click "View All Repairs" from dashboard
2. See complete list of repairs
3. Filter by:
   - Status
   - Date range
   - Unit number
   - Technician
4. Sort by date, cost, status
```

### Repair Details

Click any repair to see:
```
- Full repair information
- Customer and technician notes
- Before/after photos
- Cost breakdown
- Status history
- Technician assigned
- Completion date
```

### Unit History

```
1. Click "View Units"
2. See all your units
3. Click unit number
4. View repair history for that unit
5. See:
   - Total repairs for unit
   - Cost per repair (shows pricing tier)
   - Damage patterns
   - Technician assignments
```

**Repair Cost Pattern**:
```
Unit: TRUCK-101

Repair #1: $50 (1st repair rate)
Repair #2: $40 (2nd repair rate)
Repair #3: $35 (3rd repair rate)
Repair #4: $30 (4th repair rate)
Repair #5+: $25 (5th+ repair rate)

Total repairs: 7
Total cost: $230
```

---

## Understanding Pricing

### Standard Pricing Tiers

**Per Unit** (based on repair count for that specific unit):
```
1st repair: $50
2nd repair: $40
3rd repair: $35
4th repair: $30
5th+ repairs: $25
```

**Example**:
```
TRUCK-101's 1st repair: $50
TRUCK-101's 2nd repair: $40
TRUCK-102's 1st repair: $50  (different unit, starts at $50)
TRUCK-101's 3rd repair: $35
```

### Custom Pricing

*If your company has negotiated rates*

You may have:
- **Custom tier pricing**: Different rates than standard
- **Volume discounts**: Discount after X total repairs
- **Contract pricing**: Special negotiated rates

**How It Works**:
- System applies automatically
- You see correct prices on dashboard
- Invoices reflect your custom rates
- Contact admin for pricing questions

### Volume Discounts

*If configured for your company*

```
Example:
- Threshold: 10 repairs
- Discount: 15%
- You've completed: 12 repairs

Next repair:
- Base price: $35 (3rd repair for this unit)
- Volume discount: 15% off
- Final price: $35 × 0.85 = $29.75
```

---

## Analytics & Reporting

### Dashboard Charts

**Repairs Over Time**:
- Monthly trend
- Seasonal patterns
- Growth tracking

**Cost Analysis**:
- Total spending
- Average cost per repair
- Monthly costs

**Unit Performance**:
- Most repaired units
- Cost by unit
- Damage type distribution

### Exporting Data

*Future feature: Download repair history as CSV for your records*

---

## Mobile Usage

### Mobile App Features

**Optimized For**:
- Phone and tablet
- Portrait and landscape
- Touch interfaces
- Mobile cameras

**Key Features**:
- Submit requests on the go
- Upload photos with device camera
- Approve/deny from anywhere
- View dashboard and repairs

**Taking Photos**:
```
1. Request repair submission
2. Click photo upload field
3. Mobile device asks: "Take Photo" or "Choose Existing"
4. Take clear photo of damage
5. Upload directly to request
```

---

## Common Workflows

### Workflow 1: Requesting Service

```
You know unit needs repair
      ↓
Submit repair request
      ↓
Manager assigns technician
      ↓
Technician completes work
      ↓
You receive invoice
```

### Workflow 2: Field Discovery (Auto-Approve)

```
Technician finds damage
      ↓
Creates repair
      ↓
Auto-approved (your setting)
      ↓
Technician completes work
      ↓
You receive invoice
```

### Workflow 3: Field Discovery (Requires Approval)

```
Technician finds damage
      ↓
Creates repair
      ↓
Yellow alert on your dashboard
      ↓
You review and approve
      ↓
Technician gets notification
      ↓
Technician completes work
      ↓
You receive invoice
```

---

## Troubleshooting

### "I don't see the approval alert"

**Check**:
- Are any repairs in PENDING status?
- Refresh your dashboard
- Check "View All Repairs" for PENDING

**Possible Reasons**:
- No pending repairs
- Repairs already approved/denied
- Your setting is auto-approve

### "I approved a repair but nothing happened"

**Expected**:
- Approval processes immediately
- Alert disappears
- Repair shows as APPROVED
- Technician gets notification

**If Not Working**:
- Check internet connection
- Refresh page
- Check "All Repairs" for status

### "Photos won't upload"

**Check**:
- File size under 5MB
- File type: JPG or PNG
- Internet connection stable
- Try different photo

**Solutions**:
- Resize large photos
- Convert to JPG
- Use mobile camera (smaller files)
- Contact support

### "Expected cost seems wrong"

**Common Causes**:
- System shows standard pricing
- You have custom pricing (different)
- Volume discount not yet qualified
- Contact admin to verify pricing

---

## Best Practices

### Submitting Requests
- ✓ Clear damage descriptions
- ✓ Include photos when possible
- ✓ Accurate unit numbers
- ✓ Submit promptly when damage found

### Reviewing Approvals
- ✓ Review promptly (technician waiting)
- ✓ Check damage description matches photos
- ✓ Verify cost is acceptable
- ✓ Contact support with questions before denying

### Managing Costs
- ✓ Review approval settings quarterly
- ✓ Monitor repair patterns
- ✓ Address units with frequent damage
- ✓ Use analytics to identify trends

### Communication
- ✓ Keep contact info updated
- ✓ Respond to notifications
- ✓ Provide feedback on service
- ✓ Report issues promptly

---

## Quick Reference

### Repair Statuses

| Status | Meaning | Your Action |
|--------|---------|-------------|
| REQUESTED | You submitted request | Wait for assignment |
| PENDING | Awaiting your approval | Approve or deny |
| APPROVED | Approved, ready for work | No action needed |
| IN_PROGRESS | Work underway | No action needed |
| COMPLETED | Work done | Review invoice |
| CLOSED | Invoiced and paid | Done |

### Common Actions

| Task | How To |
|------|--------|
| Submit request | Dashboard → "Submit Request" |
| Approve repair | Dashboard → Yellow alert → "Approve" |
| Deny repair | Dashboard → Yellow alert → "Deny" |
| View history | "View All Repairs" |
| Check unit | "View Units" → Click unit number |
| Upload photo | Request form → "Choose file" |

---

## Getting Help

### Support Contact
- **Email**: [support@yourdomain.com]
- **Phone**: [Support number]
- **Hours**: [Business hours]

### Resources
- User guide (this document)
- FAQ section (coming soon)
- Video tutorials (coming soon)

### Providing Feedback
We value your input!
- Feature requests
- Bug reports
- UX improvements
- General feedback

Contact your account manager or support team.

---

**Last Updated**: October 21, 2025
**For**: RS Systems v1.4.0
**Portal**: Customer Portal
