from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta
from decimal import Decimal

router = APIRouter()

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


@router.get("/summary")
async def get_summary():
    """
    Get a summary of all metrics collected
    
    Returns:
    - Total metrics count
    - EC2 metrics count
    - S3 metrics count
    - Latest collection timestamp
    - System status
    """
    
    try:
        metrics_table = dynamodb.Table('CostOptimizer-ResourceMetrics')
        
        # Get total count
        response = metrics_table.scan(
            Select='COUNT'
        )
        total_count = response.get('Count', 0)
        
        # Count by resource type
        ec2_response = metrics_table.scan(
            FilterExpression='resource_type = :type',
            ExpressionAttributeValues={':type': 'EC2'},
            Select='COUNT'
        )
        ec2_count = ec2_response.get('Count', 0)
        
        s3_response = metrics_table.scan(
            FilterExpression='resource_type = :type',
            ExpressionAttributeValues={':type': 'S3'},
            Select='COUNT'
        )
        s3_count = s3_response.get('Count', 0)
        
        # Get latest timestamp
        latest_response = metrics_table.scan(
            Limit=1,
            ScanIndexForward=False
        )
        
        latest_timestamp = None
        if latest_response.get('Items'):
            latest_timestamp = latest_response['Items'][0].get('timestamp')
        
        return {
            'total_metrics': total_count,
            'ec2_metrics_count': ec2_count,
            's3_metrics_count': s3_count,
            'latest_collection': latest_timestamp,
            'status': 'active'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving summary: {str(e)}")


@router.get("/ec2")
async def get_ec2_metrics(
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)")
):
    """
    Get EC2 metrics
    
    Parameters:
    - limit: Number of records to return (1-100)
    - start_date: Optional start date filter
    
    Returns list of EC2 metrics ordered by timestamp (newest first)
    """
    
    try:
        metrics_table = dynamodb.Table('CostOptimizer-ResourceMetrics')
        
        if start_date:
            # Query with date filter
            start_timestamp = f"{start_date}T00:00:00"
            end_timestamp = f"{start_date}T23:59:59"
            
            response = metrics_table.query(
                IndexName='DateIndex',
                KeyConditionExpression=Key('resource_type').eq('EC2') & Key('timestamp').between(start_timestamp, end_timestamp),
                Limit=limit,
                ScanIndexForward=False
            )
        else:
            # Scan without date filter
            response = metrics_table.scan(
                FilterExpression='resource_type = :type',
                ExpressionAttributeValues={':type': 'EC2'},
                Limit=limit
            )
        
        items = decimal_to_float(response.get('Items', []))
        
        # Sort by timestamp descending
        items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return {
            'count': len(items),
            'items': items
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving EC2 metrics: {str(e)}")


@router.get("/ec2/{instance_id}")
async def get_ec2_instance_metrics(
    instance_id: str,
    limit: int = Query(24, ge=1, le=100),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)")
):
    """
    Get metrics for a specific EC2 instance
    
    Parameters:
    - instance_id: EC2 instance ID
    - limit: Number of records to return
    - start_date: Optional start date filter
    """
    
    try:
        metrics_table = dynamodb.Table('CostOptimizer-ResourceMetrics')
        
        if start_date:
            start_timestamp = f"{start_date}T00:00:00"
            end_timestamp = f"{start_date}T23:59:59"
            
            response = metrics_table.query(
                KeyConditionExpression=Key('resource_id').eq(instance_id) & Key('timestamp').between(start_timestamp, end_timestamp),
                Limit=limit,
                ScanIndexForward=False
            )
        else:
            response = metrics_table.query(
                KeyConditionExpression=Key('resource_id').eq(instance_id),
                Limit=limit,
                ScanIndexForward=False
            )
        
        items = decimal_to_float(response.get('Items', []))
        
        return {
            'instance_id': instance_id,
            'count': len(items),
            'items': items
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving instance metrics: {str(e)}")


@router.get("/s3")
async def get_s3_metrics(
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get S3 bucket metrics
    
    Returns latest metrics for S3 buckets
    """
    
    try:
        metrics_table = dynamodb.Table('CostOptimizer-ResourceMetrics')
        
        response = metrics_table.scan(
            FilterExpression='resource_type = :type',
            ExpressionAttributeValues={':type': 'S3'},
            Limit=limit
        )
        
        items = decimal_to_float(response.get('Items', []))
        
        # Sort by timestamp descending
        items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return {
            'count': len(items),
            'items': items
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving S3 metrics: {str(e)}")


@router.get("/costs/summary")
async def get_cost_summary(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """
    Get cost summary for the last N days
    
    Returns:
    - Total costs
    - Average daily cost
    - Cost breakdown by service
    - Cost trend
    """
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query cost analysis data
        response = dynamodb.Table('CostOptimizer-CostAnalysis').scan(
            FilterExpression='#d BETWEEN :start AND :end',
            ExpressionAttributeNames={'#d': 'date'},
            ExpressionAttributeValues={
                ':start': start_date.strftime('%Y-%m-%d'),
                ':end': end_date.strftime('%Y-%m-%d')
            }
        )
        
        items = decimal_to_float(response.get('Items', []))
        
        if not items:
            return {
                'total_cost': 0,
                'average_daily_cost': 0,
                'ec2_total': 0,
                's3_total': 0,
                'days_analyzed': 0
            }
        
        # Calculate totals
        total_cost = sum(item.get('total_cost', 0) for item in items)
        ec2_total = sum(item.get('ec2_cost', 0) for item in items)
        s3_total = sum(item.get('s3_cost', 0) for item in items)
        
        return {
            'total_cost': round(total_cost, 2),
            'average_daily_cost': round(total_cost / len(items), 2),
            'ec2_total': round(ec2_total, 2),
            's3_total': round(s3_total, 2),
            'days_analyzed': len(items),
            'cost_breakdown': {
                'EC2': round(ec2_total, 2),
                'S3': round(s3_total, 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cost summary: {str(e)}")


@router.get("/costs/trends")
async def get_cost_trends(
    days: int = Query(30, ge=1, le=90, description="Number of days")
):
    """
    Get daily cost trends over time
    
    Returns array of daily costs for charting
    """
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        response = dynamodb.Table('CostOptimizer-CostAnalysis').scan(
            FilterExpression='#d BETWEEN :start AND :end',
            ExpressionAttributeNames={'#d': 'date'},
            ExpressionAttributeValues={
                ':start': start_date.strftime('%Y-%m-%d'),
                ':end': end_date.strftime('%Y-%m-%d')
            }
        )
        
        items = decimal_to_float(response.get('Items', []))
        
        # Sort by date
        items.sort(key=lambda x: x.get('date', ''))
        
        # Format for charting
        trends = [
            {
                'date': item.get('date'),
                'total_cost': round(item.get('total_cost', 0), 2),
                'ec2_cost': round(item.get('ec2_cost', 0), 2),
                's3_cost': round(item.get('s3_cost', 0), 2)
            }
            for item in items
        ]
        
        return {
            'trends': trends,
            'days': len(trends)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cost trends: {str(e)}")


@router.get("/recommendations")
async def get_recommendations(
    status: Optional[str] = Query(None, description="Filter by status: open, applied, dismissed")
):
    """
    Get cost optimization recommendations
    
    Returns active recommendations with potential savings
    """
    
    try:
        recommendations_table = dynamodb.Table('CostOptimizer-Recommendations')
        
        if status:
            response = recommendations_table.scan(
                FilterExpression='#s = :status',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':status': status}
            )
        else:
            response = recommendations_table.scan()
        
        items = decimal_to_float(response.get('Items', []))
        
        # Sort by created_at descending (newest first)
        items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Calculate total savings
        total_monthly_savings = sum(
            item.get('estimated_savings_monthly', 0) 
            for item in items 
            if item.get('status') == 'open'
        )
        
        total_yearly_savings = total_monthly_savings * 12
        
        return {
            'recommendations': items,
            'count': len(items),
            'total_monthly_savings': round(total_monthly_savings, 2),
            'total_yearly_savings': round(total_yearly_savings, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving recommendations: {str(e)}")


@router.get("/recommendations/{recommendation_id}")
async def get_recommendation_detail(recommendation_id: str):
    """
    Get details for a specific recommendation
    """
    
    try:
        recommendations_table = dynamodb.Table('CostOptimizer-Recommendations')
        
        # Query by recommendation_id
        response = recommendations_table.scan(
            FilterExpression='recommendation_id = :rid',
            ExpressionAttributeValues={':rid': recommendation_id}
        )
        
        items = decimal_to_float(response.get('Items', []))
        
        if not items:
            raise HTTPException(status_code=404, detail=f"Recommendation {recommendation_id} not found")
        
        return items[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving recommendation: {str(e)}")