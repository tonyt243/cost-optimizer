import json
import boto3
from datetime import datetime, timedelta

dynamo = boto3.resource('dynamodb')
resource_metrics_table = dynamo.Table('CostOptimizer-ResourceMetrics')
s3_client = boto3.client('s3')
cloudwatch_client = boto3.client('cloudwatch')


def lambda_handler(event, context):
    print("Starting S3 metrics collection")
    
    # Retrieve the name of all buckets
    paginator = s3_client.get_paginator('list_buckets')
    bucket_list = []
    try:
        for page in paginator.paginate():
            for bucket in page.get('Buckets', []):
                bucket_list.append(bucket['Name'])

        print(f"Found {len(bucket_list)} buckets")

        for bucket in bucket_list:
            print(f"Processing bucket: {bucket}")
            
            # Retrieve metrics for all buckets
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=2) 
            
            response_bucket_size = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/S3',
                Dimensions=[
                    {'Name': 'BucketName', 'Value': bucket},
                    {'Name': 'StorageType', 'Value': 'StandardStorage'}
                ],
                MetricName="BucketSizeBytes",
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Average']
                
            )
            
            response_object_count = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/S3',
                Dimensions=[
                    {'Name': 'BucketName', 'Value': bucket},
                    {'Name': 'StorageType', 'Value': 'AllStorageTypes'} 
                ],
                MetricName="NumberOfObjects",
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Average']
                
            )

            print(f"  Bucket size datapoints: {len(response_bucket_size.get('Datapoints', []))}")
            print(f"  Object count datapoints: {len(response_object_count.get('Datapoints', []))}")

            # Store into the ResourceMetrics table
            if response_bucket_size.get('Datapoints'):
                bucket_size = response_bucket_size['Datapoints'][-1]['Average']
                object_count = response_object_count['Datapoints'][-1]['Average'] if response_object_count.get('Datapoints') else 0

                resource_metrics_table.put_item(
                    Item={
                        'resource_id': bucket,
                        'resource_type': 'S3',
                        'timestamp': datetime.utcnow().isoformat(),
                        'metrics': {
                        'BucketSizeBytes': int(bucket_size),
                        'NumberOfObjects': int(object_count)
                    },
                    'collected_at': datetime.utcnow().isoformat()
                }
            )
                print(f"Saved metrics for {bucket}")
            else:
                print(f"No metrics data available for {bucket} yet")
                
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error in parsing buckets: {str(e)}")
        }

    return {
        'statusCode': 200,
        'body': json.dumps('S3 Metrics Collected Successfully')
    }
