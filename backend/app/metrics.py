from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import os

# Initialize router
router = APIRouter(prefix="/api/metrics", tags=["metrics"])

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-west-2'))
metrics_table = dynamodb.Table(os.getenv('DYNAMODB_METRICS_TABLE', 'CostOptimizer-ResourceMetrics'))


# Pydantic models for response validation
class MetricData(BaseModel):
    """Individual metric data point"""
    CPUUtilization_Average: float
    CPUUtilization_Maximum: float
    NetworkIn_Sum: float
    NetworkOut_Sum: float
    DiskReadBytes_Sum: float
    DiskWriteBytes_Sum: float


class ResourceMetric(BaseModel):
    """Single resource metric item"""
    resource_id: str
    timestamp: str
    resource_type: str
    instance_type: Optional[str] = None
    metrics: dict
    collected_at: str

    class Config:
        # Allow Decimal types from DynamoDB
        json_encoders = {
            Decimal: float
        }


class MetricsResponse(BaseModel):
    """Response model for metrics endpoints"""
    count: int
    items: List[ResourceMetric]
    next_key: Optional[dict] = None


# Helper function to convert DynamoDB Decimal to float
def decimal_to_float(obj):
    """Recursively convert Decimal to float in dict"""
    if isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj


@router.get("/ec2", response_model=MetricsResponse)
async def get_all_ec2_metrics(
    start_date: Optional[str] = Query(None, description="Start date (ISO format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    last_key: Optional[str] = Query(None, description="Pagination key")
):
    """
    Retrieve all EC2 metrics from DynamoDB.
    
    Query parameters:
    - start_date: Filter metrics from this date onwards (YYYY-MM-DD)
    - end_date: Filter metrics up to this date (YYYY-MM-DD)
    - limit: Maximum items to return (1-1000, default: 100)
    - last_key: For pagination (returned in previous response)
    
    Returns:
    - count: Number of items returned
    - items: List of metric data points
    - next_key: Key for next page (if more data available)
    """
    
    try:
        # Build query parameters
        query_params = {
            'IndexName': 'DateIndex',
            'Limit': limit
        }
        
        # Add date range if provided
        if start_date and end_date:
            # Convert dates to ISO format timestamps
            start_timestamp = f"{start_date}T00:00:00"
            end_timestamp = f"{end_date}T23:59:59"
            
            query_params['KeyConditionExpression'] = (
                Key('resource_type').eq('EC2') &
                Key('timestamp').between(start_timestamp, end_timestamp)
            )
        elif start_date:
            start_timestamp = f"{start_date}T00:00:00"
            query_params['KeyConditionExpression'] = (
                Key('resource_type').eq('EC2') &
                Key('timestamp').gte(start_timestamp)
            )
        elif end_date:
            end_timestamp = f"{end_date}T23:59:59"
            query_params['KeyConditionExpression'] = (
                Key('resource_type').eq('EC2') &
                Key('timestamp').lte(end_timestamp)
            )
        else:
            # No date filter - get all EC2 metrics
            query_params['KeyConditionExpression'] = Key('resource_type').eq('EC2')
        
        # Add pagination key if provided
        if last_key:
            query_params['ExclusiveStartKey'] = eval(last_key)  # In production, use proper JSON parsing
        
        # Query DynamoDB
        response = metrics_table.query(**query_params)
        
        # Convert Decimal to float for JSON serialization
        items = decimal_to_float(response.get('Items', []))
        
        return {
            'count': len(items),
            'items': items,
            'next_key': response.get('LastEvaluatedKey')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")


@router.get("/ec2/{instance_id}", response_model=MetricsResponse)
async def get_ec2_instance_metrics(
    instance_id: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    last_key: Optional[str] = Query(None, description="Pagination key")
):
    """
    Retrieve metrics for a specific EC2 instance.
    
    Path parameters:
    - instance_id: EC2 instance ID (e.g., i-03fcdfc149b765c98)
    
    Query parameters:
    - start_date: Filter metrics from this date onwards (YYYY-MM-DD)
    - end_date: Filter metrics up to this date (YYYY-MM-DD)
    - limit: Maximum items to return (1-1000, default: 100)
    - last_key: For pagination
    
    Returns:
    - count: Number of items returned
    - items: List of metric data points for this instance
    - next_key: Key for next page (if more data available)
    """
    
    try:
        # Build query parameters
        query_params = {
            'Limit': limit
        }
        
        # Add date range if provided
        if start_date and end_date:
            start_timestamp = f"{start_date}T00:00:00"
            end_timestamp = f"{end_date}T23:59:59"
            
            query_params['KeyConditionExpression'] = (
                Key('resource_id').eq(instance_id) &
                Key('timestamp').between(start_timestamp, end_timestamp)
            )
        elif start_date:
            start_timestamp = f"{start_date}T00:00:00"
            query_params['KeyConditionExpression'] = (
                Key('resource_id').eq(instance_id) &
                Key('timestamp').gte(start_timestamp)
            )
        elif end_date:
            end_timestamp = f"{end_date}T23:59:59"
            query_params['KeyConditionExpression'] = (
                Key('resource_id').eq(instance_id) &
                Key('timestamp').lte(end_timestamp)
            )
        else:
            # No date filter - get all metrics for this instance
            query_params['KeyConditionExpression'] = Key('resource_id').eq(instance_id)
        
        # Add pagination key if provided
        if last_key:
            query_params['ExclusiveStartKey'] = eval(last_key)
        
        # Query DynamoDB
        response = metrics_table.query(**query_params)
        
        items = decimal_to_float(response.get('Items', []))
        
        # Check if instance exists
        if not items and not last_key:
            raise HTTPException(status_code=404, detail=f"No metrics found for instance {instance_id}")
        
        return {
            'count': len(items),
            'items': items,
            'next_key': response.get('LastEvaluatedKey')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")


@router.get("/s3", response_model=MetricsResponse)
async def get_all_s3_metrics(
    start_date: Optional[str] = Query(None, description="Start date (ISO format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    last_key: Optional[str] = Query(None, description="Pagination key")
):
    """
    Retrieve all S3 metrics from DynamoDB.
    
    Query parameters:
    - start_date: Filter metrics from this date onwards (YYYY-MM-DD)
    - end_date: Filter metrics up to this date (YYYY-MM-DD)
    - limit: Maximum items to return (1-1000, default: 100)
    - last_key: For pagination
    
    Returns:
    - count: Number of items returned
    - items: List of S3 metric data points
    - next_key: Key for next page (if more data available)
    """
    
    try:
        query_params = {
            'IndexName': 'DateIndex',
            'Limit': limit
        }
        
        # Add date range if provided
        if start_date and end_date:
            start_timestamp = f"{start_date}T00:00:00"
            end_timestamp = f"{end_date}T23:59:59"
            
            query_params['KeyConditionExpression'] = (
                Key('resource_type').eq('S3') &
                Key('timestamp').between(start_timestamp, end_timestamp)
            )
        elif start_date:
            start_timestamp = f"{start_date}T00:00:00"
            query_params['KeyConditionExpression'] = (
                Key('resource_type').eq('S3') &
                Key('timestamp').gte(start_timestamp)
            )
        elif end_date:
            end_timestamp = f"{end_date}T23:59:59"
            query_params['KeyConditionExpression'] = (
                Key('resource_type').eq('S3') &
                Key('timestamp').lte(end_timestamp)
            )
        else:
            query_params['KeyConditionExpression'] = Key('resource_type').eq('S3')
        
        if last_key:
            query_params['ExclusiveStartKey'] = eval(last_key)
        
        response = metrics_table.query(**query_params)
        
        items = decimal_to_float(response.get('Items', []))
        
        return {
            'count': len(items),
            'items': items,
            'next_key': response.get('LastEvaluatedKey')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving S3 metrics: {str(e)}")


@router.get("/summary")
async def get_metrics_summary():
    """
    Get a summary of collected metrics.
    
    Returns:
    - Total count of EC2 metrics
    - Total count of S3 metrics
    - Latest collection timestamp
    - Number of unique resources
    """
    
    try:
        # Get EC2 metrics count
        ec2_response = metrics_table.query(
            IndexName='DateIndex',
            KeyConditionExpression=Key('resource_type').eq('EC2'),
            Select='COUNT'
        )
        
        # Get S3 metrics count
        s3_response = metrics_table.query(
            IndexName='DateIndex',
            KeyConditionExpression=Key('resource_type').eq('S3'),
            Select='COUNT'
        )
        
        # Get latest EC2 metric for timestamp
        latest_ec2 = metrics_table.query(
            IndexName='DateIndex',
            KeyConditionExpression=Key('resource_type').eq('EC2'),
            ScanIndexForward=False,  # Descending order
            Limit=1
        )
        
        latest_timestamp = None
        if latest_ec2.get('Items'):
            latest_timestamp = latest_ec2['Items'][0].get('timestamp')
        
        return {
            'total_metrics': ec2_response['Count'] + s3_response['Count'],
            'ec2_metrics_count': ec2_response['Count'],
            's3_metrics_count': s3_response['Count'],
            'latest_collection': latest_timestamp,
            'status': 'active'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting summary: {str(e)}")