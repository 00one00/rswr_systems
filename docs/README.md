# Deployment Documentation

This directory contains sanitized deployment templates for the RS Systems application.

## Available Templates

1. **AWS_DEPLOYMENT_TEMPLATE.md** - Step-by-step AWS Elastic Beanstalk deployment guide
2. **DEPLOYMENT_TEMPLATE.md** - Comprehensive deployment guide with troubleshooting

## Security Note

These templates contain placeholder values (in brackets) that should be replaced with your actual configuration values. The original deployment guides have been removed from version control to protect sensitive infrastructure information.

## Usage

1. Copy the relevant template
2. Replace all bracketed placeholders with your actual values
3. Save as a private document outside of version control
4. Follow the deployment steps

## Important

Never commit files containing actual:
- Database endpoints
- Passwords or credentials
- Production URLs
- API keys or secrets

Keep your populated deployment guides in a secure location outside of this repository.