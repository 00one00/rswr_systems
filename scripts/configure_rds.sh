#!/bin/bash

# Script to configure RDS database for RS Systems production

echo "Checking RDS instance status..."

# Wait for RDS instance to be available
while true; do
    STATUS=$(aws rds describe-db-instances \
        --db-instance-identifier rs-systems-production-db \
        --query "DBInstances[0].DBInstanceStatus" \
        --output text 2>/dev/null)
    
    if [ "$STATUS" == "available" ]; then
        echo "RDS instance is available!"
        break
    else
        echo "Current status: $STATUS - waiting..."
        sleep 30
    fi
done

# Get the endpoint
ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier rs-systems-production-db \
    --query "DBInstances[0].Endpoint.Address" \
    --output text)

PORT=$(aws rds describe-db-instances \
    --db-instance-identifier rs-systems-production-db \
    --query "DBInstances[0].Endpoint.Port" \
    --output text)

echo "RDS Endpoint: $ENDPOINT"
echo "RDS Port: $PORT"

# Construct the DATABASE_URL
DATABASE_URL="postgresql://rsadmin:RSsystems2025Prod!@$ENDPOINT:$PORT/rsystemsdb"

echo ""
echo "DATABASE_URL for Elastic Beanstalk:"
echo "$DATABASE_URL"
echo ""

# Set the environment variable in Elastic Beanstalk
echo "Setting DATABASE_URL in Elastic Beanstalk environment..."
eb setenv DATABASE_URL="$DATABASE_URL" \
    RAILWAY_DATABASE_URL="$DATABASE_URL" \
    USE_RAILWAY_DB=true \
    ENVIRONMENT=production \
    -e rs-systems-production

echo "Configuration complete!"
echo ""
echo "Next steps:"
echo "1. Deploy the updated code: eb deploy rs-systems-production"
echo "2. Run migrations: eb ssh -e rs-systems-production"
echo "   Then: source /var/app/venv/*/bin/activate && cd /var/app/current && python manage.py migrate"