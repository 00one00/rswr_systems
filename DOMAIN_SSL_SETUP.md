# Domain and SSL Setup Guide

## Current Status
- ✅ All security fixes implemented and deployed
- ✅ Application is running and healthy on AWS
- ✅ SSL certificate created in ACM
- ✅ Main domain (rockstarwindshield.repair) validated successfully
- ❌ Subdomain certificates still pending validation
- ❌ Domain not yet pointed to AWS infrastructure

## Steps to Complete Setup

### 1. Complete SSL Certificate Validation

You need to add these DNS records to your Squarespace DNS settings:

**For www.rockstarwindshield.repair:**
- **Name:** `_3a0a85810caea3024fc7dfc6887d89c9.www.rockstarwindshield.repair.`
- **Type:** CNAME
- **Value:** `_25d39035b5faed6186e94e8f8cb6a6cc.xlfgrmvvlj.acm-validations.aws.`

**For app.rockstarwindshield.repair:**
- **Name:** `_b0495e93dffe214ed843a2df8ef023a0.app.rockstarwindshield.repair.`
- **Type:** CNAME
- **Value:** `_1ef51ba7314f4da7314c2cbabec63b1f.xlfgrmvvlj.acm-validations.aws.`

### 2. Point Your Domain to AWS

Add these DNS records to your Squarespace DNS settings:

**For the main domain:**
- **Name:** `@` (or leave blank for root domain)
- **Type:** CNAME
- **Value:** `rs-systems-prod.eba-jtjhm8nz.us-east-1.elasticbeanstalk.com`

**For www subdomain:**
- **Name:** `www`
- **Type:** CNAME
- **Value:** `rs-systems-prod.eba-jtjhm8nz.us-east-1.elasticbeanstalk.com`

**For app subdomain:**
- **Name:** `app`
- **Type:** CNAME
- **Value:** `rs-systems-prod.eba-jtjhm8nz.us-east-1.elasticbeanstalk.com`

### 3. Wait for DNS Propagation

- DNS changes can take 24-48 hours to fully propagate
- SSL certificate validation usually happens within 30 minutes after DNS records are added
- You can check certificate status with: `aws acm describe-certificate --certificate-arn arn:aws:acm:us-east-1:973196283632:certificate/b4b2be04-0d3d-4b5e-80cb-d6a98922b0d9 --region us-east-1`

### 4. Enable HTTPS Configuration

Once the SSL certificate shows status "ISSUED", enable HTTPS:

1. Edit `.ebextensions/08_https_redirect.config`
2. Uncomment the HTTPS listener configuration
3. Change environment variables to:
   - `HTTPS_AVAILABLE: "true"`
   - `FORCE_HTTPS: "true"`
4. Rename `09_https_redirect.config.disabled` to `09_https_redirect.config`
5. Deploy with: `eb deploy`

### 5. Test Your Setup

After DNS propagation:
- Test HTTP: `http://rockstarwindshield.repair`
- Test HTTPS: `https://rockstarwindshield.repair`
- Test www: `https://www.rockstarwindshield.repair`
- Test app subdomain: `https://app.rockstarwindshield.repair`

## Security Features Implemented

✅ **Content Security Policy (CSP)** - Prevents XSS attacks
✅ **HTTP Strict Transport Security (HSTS)** - Forces HTTPS
✅ **X-Frame-Options** - Prevents clickjacking
✅ **X-Content-Type-Options** - Prevents MIME-type sniffing
✅ **Referrer-Policy** - Controls referrer information
✅ **Permissions-Policy** - Restricts browser features
✅ **Cross-Origin Policies** - Protects against cross-origin attacks
✅ **Secure Session Management** - HTTPOnly, Secure, SameSite cookies
✅ **CSRF Protection** - Cross-Site Request Forgery protection

## Current Configuration

### SSL Certificate ARN
```
arn:aws:acm:us-east-1:973196283632:certificate/b4b2be04-0d3d-4b5e-80cb-d6a98922b0d9
```

### Elastic Beanstalk Environment
```
Environment: rs-systems-prod
CNAME: rs-systems-prod.eba-jtjhm8nz.us-east-1.elasticbeanstalk.com
Region: us-east-1
Status: Ready
Health: Green
```

## Troubleshooting

### If domain doesn't resolve:
1. Check DNS propagation: `nslookup rockstarwindshield.repair`
2. Verify CNAME records are correctly set in Squarespace
3. Wait up to 48 hours for full propagation

### If SSL certificate validation fails:
1. Double-check DNS validation records
2. Ensure records are added exactly as shown (including trailing dots)
3. Check AWS ACM console for validation status

### If HTTPS redirect fails:
1. Ensure certificate status is "ISSUED"
2. Check that HTTPS listener is configured correctly
3. Verify environment variables are set properly

## Next Steps After Domain Setup

1. Update any hardcoded URLs in your application
2. Set up monitoring and alerting
3. Configure backup and recovery procedures
4. Review and update security policies regularly
5. Set up SSL certificate auto-renewal monitoring

## Contact Information

- AWS Certificate ARN: `arn:aws:acm:us-east-1:973196283632:certificate/b4b2be04-0d3d-4b5e-80cb-d6a98922b0d9`
- Elastic Beanstalk Environment: `rs-systems-prod`
- Region: `us-east-1`