import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize AWS clients
ec2_client = boto3.client('ec2')
cloudwatch_client = boto3.client('cloudwatch')
dynamodb = boto3.resource('dynamodb')

# DynamoDB table
table = dynamodb.Table('CostOptimizer-ResourceMetrics')

def lambda_handler(event, context):
    """
    Lambda function to collect EC2 metrics and store in DynamoDB
    Triggered hourly by CloudWatch Events
    """
    
    print("Starting EC2 metrics collection...")
    
    try:
        # Get all EC2 instances
        response = ec2_client.describe_instances()
        
        instances_processed = 0
        metrics_collected = 0
        
        # Process each instance
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                instance_state = instance['State']['Name']
                
                print(f"Processing instance: {instance_id} ({instance_type}) - {instance_state}")
                
                # Only collect metrics for running instances
                if instance_state == 'running':
                    # Get metrics from CloudWatch
                    metrics = get_instance_metrics(instance_id)
                    
                    # Store in DynamoDB
                    save_to_dynamodb(instance_id, instance_type, metrics)
                    
                    instances_processed += 1
                    metrics_collected += len(metrics)
                else:
                    print(f"Skipping {instance_id} - not running")
        
        result = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'EC2 metrics collection completed',
                'instances_processed': instances_processed,
                'metrics_collected': metrics_collected
            })
        }
        
        print(f"Collection complete: {instances_processed} instances, {metrics_collected} metrics")
        return result
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error collecting metrics',
                'error': str(e)
            })
        }


def get_instance_metrics(instance_id):
    """
    Get CloudWatch metrics for an EC2 instance
    Returns metrics for the last hour
    """
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    metrics = {}
    
    # Define metrics to collect
    metric_queries = [
        {
            'name': 'CPUUtilization',
            'statistics': ['Average', 'Maximum']
        },
        {
            'name': 'NetworkIn',
            'statistics': ['Sum']
        },
        {
            'name': 'NetworkOut',
            'statistics': ['Sum']
        },
        {
            'name': 'DiskReadBytes',
            'statistics': ['Sum']
        },
        {
            'name': 'DiskWriteBytes',
            'statistics': ['Sum']
        }
    ]
    
    # Collect each metric
    for metric_query in metric_queries:
        metric_name = metric_query['name']
        statistics = metric_query['statistics']
        
        try:
            response = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=statistics
            )
            
            # Extract values
            if response['Datapoints']:
                datapoint = response['Datapoints'][0]
                
                for stat in statistics:
                    key = f"{metric_name}_{stat}"
                    # Convert to Decimal for DynamoDB
                    metrics[key] = Decimal(str(datapoint.get(stat, 0)))
            else:
                # No data available, set to 0
                for stat in statistics:
                    key = f"{metric_name}_{stat}"
                    metrics[key] = Decimal('0')
                    
        except Exception as e:
            print(f"Error getting {metric_name}: {str(e)}")
            # Set default values on error
            for stat in statistics:
                key = f"{metric_name}_{stat}"
                metrics[key] = Decimal('0')
    
    return metrics


def save_to_dynamodb(instance_id, instance_type, metrics):
    """
    Save metrics to DynamoDB table
    """
    
    try:
        # Prepare item
        item = {
            'resource_id': instance_id,
            'timestamp': datetime.utcnow().isoformat(),
            'resource_type': 'EC2',
            'instance_type': instance_type,
            'metrics': metrics,
            'collected_at': datetime.utcnow().isoformat()
        }
        
        # Put item in table
        table.put_item(Item=item)
        
        print(f"Saved metrics for {instance_id} to DynamoDB")
        
    except Exception as e:
        print(f"Error saving to DynamoDB: {str(e)}")
        raise