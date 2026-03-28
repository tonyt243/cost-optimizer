import json
import boto3
from datetime import datetime, timedelta

dynamo = boto3.resource('dynamodb')
resource_metrics_table = dynamo.Table('CostOptimizer-ResourceMetrics')
s3_client = boto3.client('s3')
cloudwatch_client = boto3.client('cloudwatch')


def lambda_handler(event, context):
    # Retrieve the name of all buckets
    paginator = s3_client.get_paginator('list_buckets')
    bucket_list = []

    for page in paginator.paginate():
        for bucket in page.get('Buckets', []):
            bucket_list.append(bucket['Name'])

    try:
        for bucket in bucket_list:
            # Retrieve metrics for all buckets
            response_bucket_size = cloudwatch_client.get_metric_statistics(
                Namespace = 'AWS/S3',
                Dimensions = [
                    {'Name' : 'BucketName', 'Value' : bucket},
                    {'Name' : 'StorageType', 'Value' : 'StandardStorage'}
                ],
                MetricName = "BucketSizeBytes",
                StartTime = datetime.now() - timedelta(hours=24),
                EndTime = datetime.now(),
                Period = 86400,
                Statistics = ['Average'],
                Unit = 'Bytes'
            )
            response_object_count = cloudwatch_client.get_metric_statistics(
                Namespace = 'AWS/S3',
                Dimensions = [
                    {'Name' : 'BucketName', 'Value' : bucket},
                    {'Name' : 'StorageType', 'Value' : 'StandardStorage'}
                ],
                MetricName = "NumberOfObjects",
                StartTime = datetime.now() - timedelta(hours=24),
                EndTime = datetime.now(),
                Period = 86400,
                Statistics = ['Average'],
                Unit = 'Count'
            )

            # Store into the ResourceMetrics table
            if response_bucket_size['Datapoints']:
                bucket_size = response_bucket_size['Datapoints'][-1]['Average']
                object_count = response_object_count['Datapoints'][-1]['Average']

                resource_metrics_table.put_item(
                    Item={
                        'resource_id': bucket,
                        'resource_type': 's3StandardStorage',
                        'timestamp': str(datetime.now()),
                        'BucketSizeBytes': int(bucket_size),
                        'NumberOfObjects': int(object_count)
                    }
                )
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps("Error in parsing buckets " + e)
        }

    return {
        'statusCode': 200,
        'body': json.dumps('S3 Metrics Collected Successfully')
    }
