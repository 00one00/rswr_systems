# HTTPS Setup Guide for RS Systems

This guide explains how to configure HTTPS for the RS Systems application deployed on AWS Elastic Beanstalk.

## Current Status

The application is currently configured with comprehensive security features but is running on HTTP only because it uses the default Elastic Beanstalk domain (*.elasticbeanstalk.com) which doesn't support custom SSL certificates.

## Security Features Already Implemented

✅ **Content Security Policy (CSP)** - Prevents XSS attacks
✅ **Session Security** - Secure session handling with proper timeouts
✅ **Security Headers** - X-Frame-Options, X-Content-Type-Options, etc.
✅ **CSRF Protection** - Cross-Site Request Forgery protection
✅ **Input Validation** - Comprehensive form and data validation
✅ **HTTPS-Ready Configuration** - Ready to enable when SSL is available

## HTTPS Configuration Options

### Option 1: Custom Domain with ACM Certificate (Recommended)

1. **Purchase/Configure a Custom Domain**
   ```bash
   # Example: yourdomain.com
   ```

2. **Request SSL Certificate via AWS Certificate Manager**
   ```bash
   aws acm request-certificate \
     --domain-name yourdomain.com \
     --subject-alternative-names www.yourdomain.com \
     --validation-method DNS \
     --region us-east-1
   ```

3. **Validate the Certificate**
   - Follow DNS validation instructions in the AWS Console
   - Wait for certificate status to become "Issued"

4. **Configure HTTPS Using Our Script**
   ```bash
   python scripts/configure_https.py \
     --domain yourdomain.com \
     --cert-arn arn:aws:acm:us-east-1:123456789012:certificate/abcd1234-...
   ```

5. **Deploy Changes**
   ```bash
   eb deploy
   ```

6. **Update DNS**
   - Point your domain to the load balancer DNS name
   - Get the load balancer DNS: `eb status`

### Option 2: CloudFront with Custom Domain

1. **Create CloudFront Distribution**
   - Origin: Your EB environment URL
   - Custom domain with ACM certificate
   - Redirect HTTP to HTTPS

2. **Update Application Settings**
   ```bash
   eb setenv HTTPS_AVAILABLE=true FORCE_HTTPS=true
   eb deploy
   ```

### Option 3: Application Load Balancer with Custom Certificate

1. **Upload Custom Certificate**
   ```bash
   aws iam upload-server-certificate \
     --server-certificate-name my-certificate \
     --certificate-body file://public_key_cert_file.pem \
     --private-key file://my_private_key.pem \
     --certificate-chain file://my_certificate_chain_file.pem
   ```

2. **Configure Load Balancer**
   - Add HTTPS listener on port 443
   - Use uploaded certificate

## Environment Variables

The application uses these environment variables for HTTPS configuration:

| Variable | Values | Description |
|----------|--------|-------------|
| `HTTPS_AVAILABLE` | true/false | Whether HTTPS is configured at load balancer level |
| `FORCE_HTTPS` | true/false | Whether to redirect HTTP to HTTPS |
| `PRODUCTION_DOMAIN` | domain.com | Your custom domain name |

## Security Settings by Configuration

### HTTP Only (Current)
- ✅ CSP headers
- ✅ Security headers  
- ✅ Session security (non-secure cookies)
- ✅ CSRF protection
- ❌ SSL redirect
- ❌ Secure cookies

### HTTPS Available (HTTPS_AVAILABLE=true, FORCE_HTTPS=false)
- ✅ CSP headers
- ✅ Security headers
- ✅ Session security with secure cookies
- ✅ CSRF protection
- ❌ SSL redirect (both HTTP and HTTPS work)

### HTTPS Enforced (HTTPS_AVAILABLE=true, FORCE_HTTPS=true)
- ✅ CSP headers
- ✅ Security headers
- ✅ Session security with secure cookies
- ✅ CSRF protection
- ✅ SSL redirect (HTTP → HTTPS)
- ✅ HSTS headers

## Testing HTTPS Configuration

1. **Test HTTP to HTTPS Redirect**
   ```bash
   curl -I http://yourdomain.com
   # Should return 301/302 redirect to HTTPS
   ```

2. **Test Security Headers**
   ```bash
   curl -I https://yourdomain.com
   # Should include Strict-Transport-Security header
   ```

3. **Test Application Functionality**
   - Login/logout
   - Form submissions
   - API endpoints
   - Static file loading

## Troubleshooting

### Common Issues

1. **Certificate Not Found**
   - Verify certificate is in us-east-1 region
   - Check certificate status is "Issued"

2. **HTTPS Timeout**
   - Verify load balancer has HTTPS listener on port 443
   - Check security groups allow port 443

3. **Mixed Content Warnings**
   - Update CSP to allow HTTPS resources
   - Check for hardcoded HTTP URLs

4. **Session Issues**
   - Verify secure cookies are working
   - Check session timeout settings

### Debug Commands

```bash
# Check current environment variables
eb printenv

# Check load balancer configuration
aws elbv2 describe-listeners --load-balancer-arn $(aws elasticbeanstalk describe-environment-resources --environment-name rs-systems-prod --query "EnvironmentResources.LoadBalancers[0].Name" --output text)

# Check certificate status
aws acm describe-certificate --certificate-arn YOUR_CERT_ARN

# View application logs
eb logs
```

## Security Recommendations

1. **Always use HTTPS in production**
2. **Enable HSTS with long max-age**
3. **Use strong SSL/TLS configuration**
4. **Regular certificate renewal**
5. **Monitor security headers**

## Contact

For questions about HTTPS configuration, refer to this guide or consult the AWS documentation for Elastic Beanstalk and Certificate Manager.