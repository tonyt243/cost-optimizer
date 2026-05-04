import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

dynamodb = boto3.resource('dynamodb')
metrics_table = dynamodb.Table('CostOptimizer-ResourceMetrics')
analysis_table = dynamodb.Table('CostOptimizer-CostAnalysis')

# AWS Pricing (us-west-2, per month)
EC2_PRICING = {
    't3.nano': Decimal('3.796'),
    't3.micro': Decimal('7.592'),
    't3.small': Decimal('15.184'),
    't3.medium': Decimal('30.368'),
    't3.large': Decimal('60.736'),
    't2.micro': Decimal('8.468'),
    't2.small': Decimal('16.936'),
    't2.medium': Decimal('33.872')
}

# S3 Pricing (per GB per month, us-west-2)
S3_STANDARD_PRICE = Decimal('0.023')


def get_metrics_for_date(date_str, resource_type):
    """Get all metrics for a specific date and resource type"""
    
    print(f"Querying {resource_type} metrics for {date_str}")
    
    start_time = f"{date_str}T00:00:00"
    end_time = f"{date_str}T23:59:59"
    
    try:
        response = metrics_table.query(
            IndexName='DateIndex',
            KeyConditionExpression='resource_type = :type AND #ts BETWEEN :start AND :end',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':type': resource_type,
                ':start': start_time,
                ':end': end_time
            }
        )
        
        items = response.get('Items', [])
        print(f"  Found {len(items)} {resource_type} metrics")
        return items
        
    except Exception as e:
        print(f"  Error querying metrics: {str(e)}")
        return []


def calculate_ec2_costs(date_str):
    """Calculate EC2 costs for a specific date"""
    
    print(f"\nCalculating EC2 costs for {date_str}...")
    
    ec2_metrics = get_metrics_for_date(date_str, 'EC2')
    
    if not ec2_metrics:
        print("  No EC2 metrics found")
        return Decimal('0'), {}
    
    # Group by instance
    instance_hours = defaultdict(int)
    instance_types = {}
    
    for metric in ec2_metrics:
        instance_id = metric['resource_id']
        instance_type = metric.get('instance_type', 't3.micro')
        
        instance_hours[instance_id] += 1  # Each metric = 1 hour
        instance_types[instance_id] = instance_type
    
    # Calculate costs
    total_ec2_cost = Decimal('0')
    breakdown = {}
    
    for instance_id, hours in instance_hours.items():
        instance_type = instance_types.get(instance_id, 't3.micro')
        
        # Get hourly rate (monthly price / 730 hours)
        monthly_price = EC2_PRICING.get(instance_type, EC2_PRICING['t3.micro'])
        hourly_rate = monthly_price / Decimal('730')
        
        # Calculate cost for this instance
        instance_cost = hourly_rate * Decimal(str(hours))
        total_ec2_cost += instance_cost
        breakdown[instance_id] = instance_cost
        
        print(f"  {instance_id} ({instance_type}):")
        print(f"    Hours: {hours}")
        print(f"    Rate: ${hourly_rate:.4f}/hour")
        print(f"    Cost: ${instance_cost:.4f}")
    
    print(f"  Total EC2 cost: ${total_ec2_cost:.4f}")
    return total_ec2_cost, breakdown


def calculate_s3_costs(date_str):
    """Calculate S3 costs for a specific date"""
    
    print(f"\nCalculating S3 costs for {date_str}...")
    
    s3_metrics = get_metrics_for_date(date_str, 'S3')
    
    if not s3_metrics:
        print("  No S3 metrics found")
        return Decimal('0'), {}
    
    # Use latest metric for each bucket
    latest_metrics = {}
    for metric in s3_metrics:
        bucket_id = metric['resource_id']
        timestamp = metric['timestamp']
        
        if bucket_id not in latest_metrics or timestamp > latest_metrics[bucket_id]['timestamp']:
            latest_metrics[bucket_id] = metric
    
    # Calculate costs
    total_s3_cost = Decimal('0')
    breakdown = {}
    
    for bucket_id, metric in latest_metrics.items():
        # Get bucket size in bytes
        size_bytes = Decimal('0')
        
        # Handle both old and new S3 data formats
        if 'metrics' in metric and 'BucketSizeBytes' in metric['metrics']:
            size_bytes = Decimal(str(metric['metrics']['BucketSizeBytes']))
        elif 'BucketSizeBytes' in metric:
            size_bytes = Decimal(str(metric['BucketSizeBytes']))
        
        # Convert to GB and calculate daily cost
        size_gb = size_bytes / Decimal('1073741824')  # Bytes to GB
        daily_cost = (size_gb * S3_STANDARD_PRICE) / Decimal('30')  # Monthly rate to daily
        
        total_s3_cost += daily_cost
        breakdown[bucket_id] = daily_cost
        
        print(f"  {bucket_id}:")
        print(f"    Size: {size_gb:.6f} GB")
        print(f"    Daily cost: ${daily_cost:.6f}")
    
    print(f"  Total S3 cost: ${total_s3_cost:.6f}")
    return total_s3_cost, breakdown


def save_cost_analysis(date_str, ec2_cost, s3_cost, ec2_breakdown, s3_breakdown):
    """Save cost analysis to DynamoDB"""
    
    print(f"\nSaving cost analysis to DynamoDB...")
    
    total_cost = ec2_cost + s3_cost
    
    # Combine breakdowns
    breakdown_by_resource = {}
    for resource_id, cost in ec2_breakdown.items():
        breakdown_by_resource[resource_id] = cost
    for resource_id, cost in s3_breakdown.items():
        breakdown_by_resource[resource_id] = cost
    
    analysis_id = f"analysis-{date_str}"
    
    item = {
        'analysis_id': analysis_id,
        'date': date_str,
        'total_cost': total_cost,
        'ec2_cost': ec2_cost,
        's3_cost': s3_cost,
        'breakdown_by_resource': breakdown_by_resource,
        'cost_by_type': {
            'EC2': ec2_cost,
            'S3': s3_cost
        },
        'calculated_at': datetime.utcnow().isoformat()
    }
    
    analysis_table.put_item(Item=item)
    print(f"  Saved analysis: {analysis_id}")
    print(f"  Total: ${total_cost:.4f}")
    
    return item


def lambda_handler(event, context):
    """
    Calculate costs for yesterday
    Runs daily at midnight
    """
    
    print("="*60)
    print("COST ANALYSIS ENGINE - Starting")
    print("="*60)
    
    try:
        # Calculate for yesterday 
        yesterday = datetime.utcnow() - timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d')
        
        print(f"\nAnalyzing costs for: {date_str}")
        print(f"Current time (UTC): {datetime.utcnow().isoformat()}")
        
        # Calculate EC2 costs
        ec2_cost, ec2_breakdown = calculate_ec2_costs(date_str)
        
        # Calculate S3 costs
        s3_cost, s3_breakdown = calculate_s3_costs(date_str)
        
        # Save analysis
        analysis = save_cost_analysis(date_str, ec2_cost, s3_cost, ec2_breakdown, s3_breakdown)
        
        print("\n" + "="*60)
        print("COST ANALYSIS COMPLETE!")
        print("="*60)
        print(f"Date: {date_str}")
        print(f"Total Cost: ${analysis['total_cost']:.4f}")
        print(f"  EC2: ${ec2_cost:.4f}")
        print(f"  S3: ${s3_cost:.6f}")
        print(f"Resources analyzed: {len(ec2_breakdown) + len(s3_breakdown)}")
        print("="*60)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Cost analysis completed successfully',
                'date': date_str,
                'total_cost': float(analysis['total_cost']),
                'ec2_cost': float(ec2_cost),
                's3_cost': float(s3_cost),
                'resources_analyzed': len(ec2_breakdown) + len(s3_breakdown)
            })
        }
        
    except Exception as e:
        print("\n" + "="*60)
        print("ERROR IN COST ANALYSIS")
        print("="*60)
        print(f"Error: {str(e)}")
        
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Cost analysis failed'
            })
        }