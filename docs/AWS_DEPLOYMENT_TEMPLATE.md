# AWS Deployment Guide Template for RS Systems

This guide walks through the process of deploying the RS Systems Django application to AWS Elastic Beanstalk.

## Prerequisites

1. AWS CLI installed and configured
2. EB CLI installed
3. Git

## Database Configuration

Your RDS PostgreSQL database should be configured with:
- **Endpoint**: [YOUR_RDS_ENDPOINT]
- **Port**: 5432
- **Username**: [YOUR_DB_USERNAME]
- **Database Name**: [YOUR_DB_NAME]

## Deployment Steps

### 1. Set Database Password

You need to set the database password securely using environment variables. Never commit passwords to the repository.

```bash
# Before deploying, set the password in your environment
export DB_PASSWORD='your_secure_password'
```

### 2. Initialize Elastic Beanstalk (if not already done)

```bash
cd /Users/drakeduncan/projects/rs_systems_branch2
eb init

# If prompted, select:
# - Region: us-east-1 (N. Virginia)
# - Application name: rs_systems_branch2
# - Platform: Python 3.13
```

### 3. Create Your Environment

```bash
eb create [YOUR_ENV_NAME] \
    --database.engine postgres \
    --database.username [YOUR_DB_USERNAME] \
    --database.password $DB_PASSWORD \
    --database.name [YOUR_DB_NAME] \
    --envvars DB_PASSWORD=$DB_PASSWORD
```

### 4. Deploy Your Application

For subsequent updates, simply run:

```bash
eb deploy
```

### 5. Open Your Application

```bash
eb open
```

## Troubleshooting

If you encounter deployment issues:

1. **Check Logs**:
   ```bash
   eb logs
   ```

2. **SSH into the instance**:
   ```bash
   eb ssh
   ```

3. **Database Connection Issues**:
   - Verify VPC security group allows connections from your EB environment
   - Check that your RDS instance is in the same VPC as your EB environment
   - Validate database credentials

4. **Static Files Issues**:
   - Check if collectstatic ran successfully
   - Verify STATIC_ROOT path in settings_aws.py

## Security Considerations

1. Store sensitive settings as environment variables
2. Never commit credentials to your repository
3. Configure security groups to restrict access
4. Enable encryption at rest for your database

## Maintenance

1. **Database Backups**:
   - Automated backups are enabled for the RDS instance
   - Retention period is 7 days

2. **Monitoring**:
   - Database Insights is enabled (Standard)
   - Encryption is enabled using AWS KMS

## Important Environment Variables

These are set in the .ebextensions/04_env_vars.config file:
- DB_NAME: [YOUR_DB_NAME]
- DB_USER: [YOUR_DB_USERNAME]
- DB_HOST: [YOUR_RDS_ENDPOINT]
- DB_PORT: 5432
- USE_HTTPS: true

The DB_PASSWORD should be set securely through the Elastic Beanstalk console or using the eb setenv command.

## Note

Replace all placeholders in brackets with your actual values:
- [YOUR_RDS_ENDPOINT]: Your actual RDS endpoint
- [YOUR_DB_USERNAME]: Your actual database username
- [YOUR_DB_NAME]: Your actual database name
- [YOUR_ENV_NAME]: Your chosen environment name