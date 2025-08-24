#!/usr/bin/env python3
"""
AWS Cost Monitor for RS Systems
Tracks and reports AWS service costs
"""
import boto3
import datetime
import json
from decimal import Decimal

def get_current_month_costs():
    """Get current month's costs by service"""
    ce = boto3.client('ce', region_name='us-east-1')
    
    # Get first and last day of current month
    now = datetime.datetime.now()
    start_date = now.replace(day=1).strftime('%Y-%m-%d')
    
    # Get first day of next month
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    
    end_date = next_month.strftime('%Y-%m-%d')
    
    try:
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        return response
        
    except Exception as e:
        print(f"Error getting costs: {e}")
        return None

def format_cost_report(cost_data):
    """Format cost data into readable report"""
    if not cost_data or 'ResultsByTime' not in cost_data:
        return "No cost data available"
    
    report = []
    report.append("=" * 50)
    report.append("RS Systems AWS Cost Report")
    report.append("=" * 50)
    
    total_cost = Decimal('0')
    
    for result in cost_data['ResultsByTime']:
        period = result['TimePeriod']
        report.append(f"Period: {period['Start']} to {period['End']}")
        report.append("-" * 30)
        
        # Sort services by cost (highest first)
        services = []
        for group in result['Groups']:
            service = group['Keys'][0]
            cost = Decimal(group['Metrics']['BlendedCost']['Amount'])
            services.append((service, cost))
            total_cost += cost
        
        services.sort(key=lambda x: x[1], reverse=True)
        
        for service, cost in services:
            if cost > 0:
                report.append(f"{service:<30} ${cost:>8.2f}")
        
        report.append("-" * 40)
        report.append(f"{'TOTAL':<30} ${total_cost:>8.2f}")
        report.append("")
    
    # Add cost breakdown analysis
    report.append("Cost Analysis:")
    report.append("-" * 20)
    
    if total_cost > 0:
        for service, cost in services[:5]:  # Top 5 services
            if cost > 0:
                percentage = (cost / total_cost) * 100
                report.append(f"{service}: {percentage:.1f}% of total")
    
    # Add optimization recommendations
    report.append("\nOptimization Recommendations:")
    report.append("-" * 30)
    
    if total_cost > 50:
        report.append("• Consider RDS instead of SQLite for better cost efficiency at scale")
    if total_cost > 100:
        report.append("• Review EC2 instance sizing - consider Reserved Instances")
    
    report.append("• Regular backup cleanup is automated (30-day retention)")
    report.append("• Monitor unused resources monthly")
    
    return "\n".join(report)

def get_forecast():
    """Get cost forecast for next month"""
    ce = boto3.client('ce', region_name='us-east-1')
    
    # Forecast for next 30 days
    start_date = datetime.datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    
    try:
        response = ce.get_cost_forecast(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Metric='BLENDED_COST',
            Granularity='MONTHLY'
        )
        
        return response
        
    except Exception as e:
        print(f"Error getting forecast: {e}")
        return None

def main():
    """Main cost monitoring function"""
    print("Fetching AWS cost data...")
    
    # Current month costs
    current_costs = get_current_month_costs()
    if current_costs:
        cost_report = format_cost_report(current_costs)
        print(cost_report)
    
    # Forecast
    print("\n" + "=" * 50)
    print("Cost Forecast (Next 30 Days)")
    print("=" * 50)
    
    forecast = get_forecast()
    if forecast and 'ForecastResultsByTime' in forecast:
        for result in forecast['ForecastResultsByTime']:
            period = result['TimePeriod']
            amount = result['MeanValue']
            print(f"Period: {period['Start']} to {period['End']}")
            print(f"Predicted Cost: ${float(amount):.2f}")
    else:
        print("Forecast data not available (may require more billing history)")
    
    # Resource summary
    print("\n" + "=" * 50)
    print("Current Resource Summary")
    print("=" * 50)
    
    try:
        # EC2 instances
        ec2 = boto3.client('ec2', region_name='us-east-1')
        instances = ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        instance_count = sum(len(r['Instances']) for r in instances['Reservations'])
        print(f"EC2 Instances: {instance_count}")
        
        # S3 buckets
        s3 = boto3.client('s3')
        buckets = s3.list_buckets()
        print(f"S3 Buckets: {len(buckets['Buckets'])}")
        
        # RDS instances
        rds = boto3.client('rds', region_name='us-east-1')
        db_instances = rds.describe_db_instances()
        print(f"RDS Instances: {len(db_instances['DBInstances'])}")
        
        # Load balancers
        elbv2 = boto3.client('elbv2', region_name='us-east-1')
        lbs = elbv2.describe_load_balancers()
        print(f"Load Balancers: {len(lbs['LoadBalancers'])}")
        
    except Exception as e:
        print(f"Error getting resource summary: {e}")

if __name__ == '__main__':
    main()