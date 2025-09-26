# Security Quick Reference

## 🚨 Emergency Response

### Suspicious User Found (like 'ygzwnplsgv')
```bash
# 1. Check the user
python manage.py security_audit --check-user ygzwnplsgv

# 2. If confirmed suspicious, delete from production
python manage.py shell
from django.contrib.auth.models import User
User.objects.filter(username='ygzwnplsgv').delete()

# 3. Check for related data
from apps.customer_portal.models import CustomerUser
from apps.technician_portal.models import Repair
CustomerUser.objects.filter(user__username='ygzwnplsgv').count()
Repair.objects.filter(customer__name='ygzwnplsgv').count()
```

### Under Attack - Rate Limiting Triggered
```bash
# Check recent failed logins
python manage.py shell
from apps.security.models import LoginAttempt
LoginAttempt.objects.filter(success=False).order_by('-timestamp')[:20]

# Block an IP immediately (add to settings)
# In settings_aws.py, add:
BLOCKED_IPS = ['attacker.ip.address']
```

### Mass Bot Registration
```bash
# Find and delete all suspicious users
python manage.py security_audit --delete-suspicious

# Temporarily disable registration
# In customer_portal/views.py, add at top of customer_register:
# return HttpResponse("Registration temporarily disabled", status=503)
```

## 📊 Monitoring Commands

### Daily Checks
```bash
# Run security audit
python manage.py security_audit

# Check failed logins today
python manage.py shell
from apps.security.models import LoginAttempt
from django.utils import timezone
from datetime import timedelta
today = timezone.now() - timedelta(days=1)
LoginAttempt.objects.filter(timestamp__gte=today, success=False).count()
```

### Find Suspicious Patterns
```bash
# Find users with no email
User.objects.filter(email='').exclude(username__startswith='tech')

# Find users who never logged in
User.objects.filter(last_login__isnull=True)

# Find random-looking usernames
import re
pattern = re.compile(r'^[a-z]{8,}$')
User.objects.filter(username__regex=r'^[a-z]{8,}$').values_list('username', flat=True)
```

## 🔧 Production Deployment Checklist

### Before Deploying Security Updates
1. ✅ Test locally with `python manage.py test apps.security`
2. ✅ Run migrations locally first
3. ✅ Backup production database
4. ✅ Have rollback plan ready

### Deploy Security Updates to AWS
```bash
# 1. Install new requirements
eb deploy

# 2. Run migrations on production
eb ssh
cd /var/app/current
source /var/app/venv/*/bin/activate
python manage.py migrate

# 3. Test security features
python manage.py security_audit
```

## 🛡️ Current Security Features

### Rate Limiting
- Login: 10 attempts/hour per IP
- Registration: 5 attempts/hour per IP

### Bot Protection
- Honeypot field in registration
- Username pattern validation
- Blocks: consonant-heavy strings, hex patterns, generic usernames

### Security Headers (Production)
- HSTS: 1 year with preload
- XSS Filter: Enabled
- Content Type: nosniff
- Frame Options: DENY
- Cookies: HttpOnly, Secure, SameSite

## 📝 Security Configurations

### Test Bot Detection Locally
```python
# In Django shell
from apps.customer_portal.views import is_suspicious_username

# Should return True (bot-like)
is_suspicious_username('ygzwnplsgv')  # True
is_suspicious_username('qwrtpsdfgh')  # True
is_suspicious_username('abcdefghij')  # True

# Should return False (legitimate)
is_suspicious_username('johndoe')     # False
is_suspicious_username('mike123')     # False
is_suspicious_username('customer1')   # False
```

### View Login Attempts
```python
from apps.security.models import LoginAttempt

# Recent failures
LoginAttempt.objects.filter(success=False).order_by('-timestamp')[:10]

# By specific IP
LoginAttempt.objects.filter(ip_address='192.168.1.1')

# Suspicious activity check
ip = '192.168.1.1'
suspicious, reason = LoginAttempt.check_suspicious_activity(ip_address=ip)
if suspicious:
    print(f"Block IP {ip}: {reason}")
```

## 🚀 AWS-Specific Commands

### Connect to Production Database
```bash
# Set up local environment for AWS DB
export USE_AWS_DB=true
python manage.py shell

# Now you're connected to production DB
from django.contrib.auth.models import User
User.objects.count()
```

### View Production Logs
```bash
# SSH into EB instance
eb ssh

# View application logs
tail -f /var/log/nginx/error.log
tail -f /var/app/current/logs/django.log

# View security-specific logs
grep "LoginAttempt" /var/app/current/logs/django.log
```

## 📧 Incident Reporting

When you find suspicious activity:

1. **Document**:
   - Username(s) affected
   - IP addresses involved
   - Time of activity
   - Type of attack (bot registration, brute force, etc.)

2. **Respond**:
   - Delete/disable suspicious accounts
   - Block IPs if necessary
   - Update security rules

3. **Prevent**:
   - Review how they got in
   - Update validation rules
   - Consider adding CAPTCHA if recurring

## 🔄 Regular Maintenance

### Weekly
```bash
python manage.py security_audit
```

### Monthly
```bash
# Clean old login attempts (keep 90 days)
python manage.py shell
from apps.security.models import LoginAttempt
from datetime import timedelta
from django.utils import timezone
cutoff = timezone.now() - timedelta(days=90)
LoginAttempt.objects.filter(timestamp__lt=cutoff).delete()
```

### Before Major Updates
- Backup database
- Test security features
- Review SECURITY_ROADMAP.md for next steps

---

**Remember**: The username 'ygzwnplsgv' was likely a bot registration. With the new protections in place, similar registrations will be blocked automatically.