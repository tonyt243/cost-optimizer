import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import statistics

dynamodb = boto3.resource('dynamodb')
cost_table = dynamodb.Table('CostOptimizer-CostAnalysis')
metrics_table = dynamodb.Table('CostOptimizer-ResourceMetrics')
recommendations_table = dynamodb.Table('CostOptimizer-Recommendations')

# EC2 Pricing (us-west-2, monthly)
EC2_PRICING = {
    't3.nano': Decimal('3.796'),
    't3.micro': Decimal('7.592'),
    't3.small': Decimal('15.184'),
    't3.medium': Decimal('30.368'),
    't3.large': Decimal('60.736')
}

# Downsize mapping
DOWNSIZE_MAP = {
    't3.large': 't3.medium',
    't3.medium': 't3.small',
    't3.small': 't3.micro',
    't3.micro': 't3.nano'
}


def get_recent_costs(days=7):
    """Get cost data from last N days"""
    
    print(f"Getting cost data for last {days} days...")
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Query by date using GSI
    try:
        response = cost_table.scan(
            FilterExpression='#d BETWEEN :start AND :end',
            ExpressionAttributeNames={'#d': 'date'},
            ExpressionAttributeValues={
                ':start': start_date.strftime('%Y-%m-%d'),
                ':end': end_date.strftime('%Y-%m-%d')
            }
        )
        
        items = response.get('Items', [])
        print(f"  Found {len(items)} cost analysis records")
        
        # Aggregate costs by resource
        resource_costs = defaultdict(list)
        
        for item in items:
            if 'breakdown_by_resource' in item:
                for resource, cost in item['breakdown_by_resource'].items():
                    resource_costs[resource].append(float(cost))
        
        # Calculate average costs
        avg_costs = {}
        for resource, costs in resource_costs.items():
            avg_costs[resource] = sum(costs) / len(costs)
        
        print(f"  Calculated costs for {len(avg_costs)} resources")
        return avg_costs
        
    except Exception as e:
        print(f"  Error getting costs: {str(e)}")
        return {}


def get_resource_usage(resource_id, days=7):
    """Get usage metrics for a resource over last N days"""
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    try:
        response = metrics_table.query(
            KeyConditionExpression='resource_id = :rid AND #ts BETWEEN :start AND :end',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':rid': resource_id,
                ':start': start_time.isoformat(),
                ':end': end_time.isoformat()
            }
        )
        
        items = response.get('Items', [])
        
        if not items:
            return None
        
        # Extract metrics
        resource_type = items[0].get('resource_type')
        
        if resource_type == 'EC2':
            # Calculate EC2 usage stats
            cpu_values = []
            for item in items:
                if 'metrics' in item and 'CPUUtilization_Average' in item['metrics']:
                    cpu_values.append(float(item['metrics']['CPUUtilization_Average']))
            
            if cpu_values:
                return {
                    'resource_type': 'EC2',
                    'instance_type': items[0].get('instance_type'),
                    'avg_cpu': statistics.mean(cpu_values),
                    'max_cpu': max(cpu_values),
                    'min_cpu': min(cpu_values),
                    'data_points': len(cpu_values)
                }
        
        elif resource_type == 'S3':
            # Get latest S3 metrics
            latest = items[-1]
            
            objects = 0
            size = 0
            
            if 'metrics' in latest:
                objects = latest['metrics'].get('NumberOfObjects', 0)
                size = latest['metrics'].get('BucketSizeBytes', 0)
            else:
                objects = latest.get('NumberOfObjects', 0)
                size = latest.get('BucketSizeBytes', 0)
            
            return {
                'resource_type': 'S3',
                'object_count': int(objects),
                'size_bytes': int(size),
                'data_points': len(items)
            }
        
        return None
        
    except Exception as e:
        print(f"  Error getting usage for {resource_id}: {str(e)}")
        return None


def generate_ec2_recommendations(resource_id, daily_cost, usage):
    """Generate recommendations for EC2 instance"""
    
    recommendations = []
    current_type = usage.get('instance_type', 't3.micro')
    monthly_cost = daily_cost * 30
    
    # Rule 1: Underutilized (CPU < 10%)
    if usage['avg_cpu'] < 10 and current_type in DOWNSIZE_MAP:
        recommended_type = DOWNSIZE_MAP[current_type]
        new_monthly_cost = float(EC2_PRICING[recommended_type])
        savings = monthly_cost - new_monthly_cost
        
        if savings > 0:
            recommendations.append({
                'recommendation_id': f"rec-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{resource_id[:8]}",
                'created_at': datetime.utcnow().isoformat(),
                'resource_id': resource_id,
                'resource_type': 'EC2',
                'severity': 'high' if savings > 3 else 'medium',
                'type': 'UNDERUTILIZED',
                'title': 'EC2 Instance Underutilized',
                'description': f'Instance running at {usage["avg_cpu"]:.1f}% average CPU over 7 days',
                'current_cost_monthly': Decimal(str(monthly_cost)),
                'recommended_action': f'Downsize from {current_type} to {recommended_type}',
                'estimated_savings_monthly': Decimal(str(savings)),
                'estimated_savings_yearly': Decimal(str(savings * 12)),
                'status': 'open',
                'metrics_summary': {
                    'avg_cpu_7d': Decimal(str(usage['avg_cpu'])),
                    'max_cpu_7d': Decimal(str(usage['max_cpu'])),
                    'min_cpu_7d': Decimal(str(usage['min_cpu']))
                },
                'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat()
            })
    
    # Rule 2: Idle (CPU < 5%)
    elif usage['avg_cpu'] < 5:
        savings = monthly_cost
        
        recommendations.append({
            'recommendation_id': f"rec-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{resource_id[:8]}",
            'created_at': datetime.utcnow().isoformat(),
            'resource_id': resource_id,
            'resource_type': 'EC2',
            'severity': 'high',
            'type': 'IDLE',
            'title': 'EC2 Instance Appears Idle',
            'description': f'Instance running at only {usage["avg_cpu"]:.1f}% average CPU',
            'current_cost_monthly': Decimal(str(monthly_cost)),
            'recommended_action': 'Consider stopping or terminating this instance',
            'estimated_savings_monthly': Decimal(str(savings)),
            'estimated_savings_yearly': Decimal(str(savings * 12)),
            'status': 'open',
            'metrics_summary': {
                'avg_cpu_7d': Decimal(str(usage['avg_cpu']))
            },
            'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat()
        })
    
    return recommendations


def generate_s3_recommendations(resource_id, daily_cost, usage):
    """Generate recommendations for S3 bucket"""
    
    recommendations = []
    monthly_cost = daily_cost * 30
    
    # Rule: Empty bucket
    if usage['object_count'] == 0:
        recommendations.append({
            'recommendation_id': f"rec-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{resource_id[:8]}",
            'created_at': datetime.utcnow().isoformat(),
            'resource_id': resource_id,
            'resource_type': 'S3',
            'severity': 'low',
            'type': 'EMPTY_BUCKET',
            'title': 'S3 Bucket is Empty',
            'description': 'Bucket contains no objects',
            'current_cost_monthly': Decimal(str(monthly_cost)),
            'recommended_action': 'Consider deleting this empty bucket',
            'estimated_savings_monthly': Decimal(str(monthly_cost)),
            'estimated_savings_yearly': Decimal(str(monthly_cost * 12)),
            'status': 'open',
            'metrics_summary': {
                'object_count': usage['object_count'],
                'size_bytes': usage['size_bytes']
            },
            'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat()
        })
    
    return recommendations


def lambda_handler(event, context):
    """
    Generate cost-saving recommendations
    Runs daily after cost calculation
    """
    
    print("="*60)
    print("RECOMMENDATION ENGINE - Starting")
    print("="*60)
    
    try:
        # Get cost data from last 7 days
        resource_costs = get_recent_costs(days=7)
        
        if not resource_costs:
            print("No cost data available")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No cost data available for analysis',
                    'recommendations_generated': 0
                })
            }
        
        print(f"\nAnalyzing {len(resource_costs)} resources...")
        
        all_recommendations = []
        
        # Generate recommendations for each resource
        for resource_id, daily_cost in resource_costs.items():
            print(f"\n  Analyzing: {resource_id}")
            print(f"    Average daily cost: ${daily_cost:.4f}")
            
            # Get usage metrics
            usage = get_resource_usage(resource_id, days=7)
            
            if not usage:
                print(f"    No usage data available")
                continue
            
            # Generate recommendations based on resource type
            if usage['resource_type'] == 'EC2':
                print(f"    Instance type: {usage.get('instance_type')}")
                print(f"    Average CPU: {usage.get('avg_cpu', 0):.1f}%")
                
                recommendations = generate_ec2_recommendations(resource_id, daily_cost, usage)
                
            elif usage['resource_type'] == 'S3':
                print(f"    Objects: {usage.get('object_count', 0)}")
                print(f"    Size: {usage.get('size_bytes', 0)} bytes")
                
                recommendations = generate_s3_recommendations(resource_id, daily_cost, usage)
            
            else:
                continue
            
            if recommendations:
                print(f"    Generated {len(recommendations)} recommendation(s)")
                all_recommendations.extend(recommendations)
            else:
                print(f"    No recommendations (resource is optimized)")
        
        # Save recommendations to DynamoDB
        print(f"\nSaving {len(all_recommendations)} recommendations...")
        
        total_savings = Decimal('0')
        
        for rec in all_recommendations:
            recommendations_table.put_item(Item=rec)
            total_savings += rec['estimated_savings_monthly']
            
            print(f"  ✅ {rec['title']}")
            print(f"     Resource: {rec['resource_id']}")
            print(f"     Savings: ${rec['estimated_savings_monthly']:.2f}/month")
        
        print("\n" + "="*60)
        print("RECOMMENDATION ENGINE - Complete")
        print("="*60)
        print(f"Resources analyzed: {len(resource_costs)}")
        print(f"Recommendations generated: {len(all_recommendations)}")
        print(f"Total potential savings: ${total_savings:.2f}/month")
        print(f"Annual savings: ${total_savings * 12:.2f}/year")
        print("="*60)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Recommendations generated successfully',
                'recommendations_generated': len(all_recommendations),
                'total_monthly_savings': float(total_savings),
                'total_yearly_savings': float(total_savings * 12),
                'resources_analyzed': len(resource_costs)
            })
        }
        
    except Exception as e:
        print("\n" + "="*60)
        print("ERROR IN RECOMMENDATION ENGINE")
        print("="*60)
        print(f"Error: {str(e)}")
        
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Recommendation generation failed'
            })
        }