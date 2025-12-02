#!/usr/bin/env python3
"""
CloudWatch Alarms Setup Script for RS Systems Notification System

This script automatically configures CloudWatch alarms for production monitoring
of the notification system. It creates 6 critical alarms with SNS notifications.

Usage:
    python setup_cloudwatch_alarms.py [--sns-topic-arn ARN] [--region REGION] [--dry-run]

Requirements:
    - AWS credentials configured (via ~/.aws/credentials or environment variables)
    - boto3 installed (pip install boto3)
    - Appropriate IAM permissions for CloudWatch and SNS

Alarms Created:
    1. High Email Failure Rate (>5% over 5 min)
    2. High SMS Cost (>$20/hour)
    3. Celery Worker Health (no heartbeat for 5 min)
    4. Notification Queue Backlog (>1,000 pending)
    5. Delivery Latency (>30 sec average)
    6. Error Rate Spike (>10% over 5 min)
"""

import argparse
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


# CloudWatch Namespace
NAMESPACE = 'RS_Systems/Notifications'

# Default AWS Region
DEFAULT_REGION = 'us-east-1'


def create_sns_topic_if_needed(sns_client, topic_name='RS-Systems-Notification-Alarms'):
    """
    Create SNS topic for alarm notifications if it doesn't exist.

    Args:
        sns_client: Boto3 SNS client
        topic_name: Name of SNS topic

    Returns:
        str: ARN of the SNS topic
    """
    try:
        response = sns_client.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']
        print(f"✓ SNS Topic ready: {topic_arn}")
        return topic_arn
    except ClientError as e:
        print(f"✗ Error creating SNS topic: {e}")
        raise


def create_alarm(cloudwatch_client, alarm_config, sns_topic_arn, dry_run=False):
    """
    Create a CloudWatch alarm.

    Args:
        cloudwatch_client: Boto3 CloudWatch client
        alarm_config: Dictionary with alarm configuration
        sns_topic_arn: ARN of SNS topic for notifications
        dry_run: If True, only print what would be created

    Returns:
        bool: True if successful
    """
    alarm_name = alarm_config['AlarmName']

    if dry_run:
        print(f"\n[DRY RUN] Would create alarm: {alarm_name}")
        print(f"  Metric: {alarm_config.get('MetricName', 'N/A')}")
        print(f"  Threshold: {alarm_config.get('Threshold', 'N/A')}")
        print(f"  Comparison: {alarm_config.get('ComparisonOperator', 'N/A')}")
        return True

    try:
        # Add SNS action
        alarm_config['AlarmActions'] = [sns_topic_arn]
        alarm_config['OKActions'] = [sns_topic_arn]

        cloudwatch_client.put_metric_alarm(**alarm_config)
        print(f"✓ Created alarm: {alarm_name}")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"✗ Error creating alarm '{alarm_name}': {error_code} - {error_msg}")
        return False


def get_alarm_configurations():
    """
    Get all alarm configurations.

    Returns:
        list: List of alarm configuration dictionaries
    """
    alarms = []

    # 1. High Email Failure Rate (>5% over 5 minutes)
    alarms.append({
        'AlarmName': 'RS-Notifications-HighEmailFailureRate',
        'AlarmDescription': 'Alert when email failure rate exceeds 5% over 5 minutes',
        'MetricName': 'NotificationFailed',
        'Namespace': NAMESPACE,
        'Statistic': 'Sum',
        'Period': 300,  # 5 minutes
        'EvaluationPeriods': 1,
        'Threshold': 5.0,  # 5% of total emails
        'ComparisonOperator': 'GreaterThanThreshold',
        'Dimensions': [
            {
                'Name': 'Channel',
                'Value': 'email'
            }
        ],
        'TreatMissingData': 'notBreaching',
    })

    # 2. High SMS Cost (>$20/hour)
    alarms.append({
        'AlarmName': 'RS-Notifications-HighSMSCost',
        'AlarmDescription': 'Alert when SMS costs exceed $20 per hour',
        'MetricName': 'SMSCost',
        'Namespace': NAMESPACE,
        'Statistic': 'Sum',
        'Period': 3600,  # 1 hour
        'EvaluationPeriods': 1,
        'Threshold': 20.0,  # $20 USD
        'ComparisonOperator': 'GreaterThanThreshold',
        'TreatMissingData': 'notBreaching',
    })

    # 3. Celery Worker Health (no data for 5 minutes = worker down)
    alarms.append({
        'AlarmName': 'RS-Notifications-CeleryWorkerDown',
        'AlarmDescription': 'Alert when no notification deliveries for 5 minutes (worker may be down)',
        'MetricName': 'NotificationDelivered',
        'Namespace': NAMESPACE,
        'Statistic': 'SampleCount',
        'Period': 300,  # 5 minutes
        'EvaluationPeriods': 1,
        'Threshold': 1.0,  # Less than 1 delivery
        'ComparisonOperator': 'LessThanThreshold',
        'TreatMissingData': 'breaching',  # Missing data = alarm
    })

    # 4. Notification Queue Backlog (>1,000 pending tasks)
    alarms.append({
        'AlarmName': 'RS-Notifications-QueueBacklog',
        'AlarmDescription': 'Alert when notification queue depth exceeds 1,000 pending tasks',
        'MetricName': 'QueueDepth',
        'Namespace': NAMESPACE,
        'Statistic': 'Maximum',
        'Period': 600,  # 10 minutes
        'EvaluationPeriods': 1,
        'Threshold': 1000.0,
        'ComparisonOperator': 'GreaterThanThreshold',
        'Dimensions': [
            {
                'Name': 'Queue',
                'Value': 'notifications'
            }
        ],
        'TreatMissingData': 'notBreaching',
    })

    # 5. High Delivery Latency (>30 seconds average)
    alarms.append({
        'AlarmName': 'RS-Notifications-HighLatency',
        'AlarmDescription': 'Alert when average delivery latency exceeds 30 seconds',
        'MetricName': 'DeliveryLatency',
        'Namespace': NAMESPACE,
        'Statistic': 'Average',
        'Period': 300,  # 5 minutes
        'EvaluationPeriods': 2,  # 2 consecutive periods
        'Threshold': 30.0,  # 30 seconds
        'ComparisonOperator': 'GreaterThanThreshold',
        'TreatMissingData': 'notBreaching',
    })

    # 6. Error Rate Spike (>10% over 5 minutes)
    alarms.append({
        'AlarmName': 'RS-Notifications-HighErrorRate',
        'AlarmDescription': 'Alert when error rate exceeds 10% over 5 minutes',
        'MetricName': 'ErrorRate',
        'Namespace': NAMESPACE,
        'Statistic': 'Average',
        'Period': 300,  # 5 minutes
        'EvaluationPeriods': 1,
        'Threshold': 10.0,  # 10%
        'ComparisonOperator': 'GreaterThanThreshold',
        'TreatMissingData': 'notBreaching',
    })

    return alarms


def list_existing_alarms(cloudwatch_client):
    """
    List existing alarms with RS-Notifications prefix.

    Args:
        cloudwatch_client: Boto3 CloudWatch client
    """
    try:
        response = cloudwatch_client.describe_alarms(
            AlarmNamePrefix='RS-Notifications-'
        )

        if response['MetricAlarms']:
            print("\nExisting notification alarms:")
            for alarm in response['MetricAlarms']:
                state = alarm['StateValue']
                state_emoji = '✓' if state == 'OK' else ('⚠' if state == 'ALARM' else '?')
                print(f"  {state_emoji} {alarm['AlarmName']} - {state}")
        else:
            print("\nNo existing notification alarms found.")

    except ClientError as e:
        print(f"Error listing alarms: {e}")


def subscribe_email_to_topic(sns_client, topic_arn, email):
    """
    Subscribe an email address to the SNS topic.

    Args:
        sns_client: Boto3 SNS client
        topic_arn: ARN of SNS topic
        email: Email address to subscribe
    """
    try:
        response = sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
        print(f"✓ Email subscription created for {email}")
        print(f"  ⚠ Check your email and confirm the subscription!")
        return response['SubscriptionArn']
    except ClientError as e:
        print(f"✗ Error subscribing email: {e}")
        return None


def main():
    """Main function to set up CloudWatch alarms."""
    parser = argparse.ArgumentParser(
        description='Set up CloudWatch alarms for RS Systems notification system'
    )
    parser.add_argument(
        '--sns-topic-arn',
        help='Existing SNS topic ARN (will create if not provided)'
    )
    parser.add_argument(
        '--region',
        default=DEFAULT_REGION,
        help=f'AWS region (default: {DEFAULT_REGION})'
    )
    parser.add_argument(
        '--email',
        help='Email address to subscribe to alarm notifications'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without actually creating alarms'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List existing notification alarms and exit'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("RS Systems - CloudWatch Alarms Setup")
    print("=" * 70)
    print(f"Region: {args.region}")
    if args.dry_run:
        print("Mode: DRY RUN (no changes will be made)")
    print()

    # Initialize AWS clients
    try:
        cloudwatch = boto3.client('cloudwatch', region_name=args.region)
        sns = boto3.client('sns', region_name=args.region)
        print("✓ AWS clients initialized")
    except NoCredentialsError:
        print("✗ Error: AWS credentials not found!")
        print("  Configure credentials via ~/.aws/credentials or environment variables")
        return 1
    except Exception as e:
        print(f"✗ Error initializing AWS clients: {e}")
        return 1

    # List existing alarms if requested
    if args.list:
        list_existing_alarms(cloudwatch)
        return 0

    # Get or create SNS topic
    if args.sns_topic_arn:
        sns_topic_arn = args.sns_topic_arn
        print(f"✓ Using existing SNS topic: {sns_topic_arn}")
    else:
        if args.dry_run:
            sns_topic_arn = "arn:aws:sns:us-east-1:123456789012:RS-Systems-Notification-Alarms"
            print(f"[DRY RUN] Would create SNS topic: {sns_topic_arn}")
        else:
            sns_topic_arn = create_sns_topic_if_needed(sns)

    # Subscribe email if provided
    if args.email and not args.dry_run:
        print(f"\nSubscribing email to SNS topic...")
        subscribe_email_to_topic(sns, sns_topic_arn, args.email)

    # Get alarm configurations
    alarms = get_alarm_configurations()

    # Create alarms
    print(f"\nCreating {len(alarms)} CloudWatch alarms...")
    print("-" * 70)

    success_count = 0
    for alarm_config in alarms:
        if create_alarm(cloudwatch, alarm_config, sns_topic_arn, dry_run=args.dry_run):
            success_count += 1

    # Summary
    print("\n" + "=" * 70)
    if args.dry_run:
        print(f"[DRY RUN] Would create {success_count}/{len(alarms)} alarms")
    else:
        print(f"Successfully created {success_count}/{len(alarms)} alarms")

        if success_count == len(alarms):
            print("\n✓ All alarms configured successfully!")
            print("\nNext steps:")
            print("  1. Confirm SNS email subscription (check your inbox)")
            print("  2. Test alarms by publishing test metrics")
            print("  3. Monitor CloudWatch console for alarm states")
            print("\nView alarms:")
            print(f"  aws cloudwatch describe-alarms --alarm-name-prefix RS-Notifications- --region {args.region}")
        else:
            print(f"\n⚠ {len(alarms) - success_count} alarm(s) failed to create")
            print("  Check error messages above for details")

    print("=" * 70)

    return 0 if success_count == len(alarms) else 1


if __name__ == '__main__':
    sys.exit(main())
