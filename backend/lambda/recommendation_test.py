from decimal import Decimal
from unittest.mock import MagicMock
import sys
sys.modules['boto3'] = MagicMock()

from recommendation_engine import generate_s3_recommendations, generate_ec2_recommendations


def test_s3_empty_bucket():
    resource_id = "my-test-bucket-abc123"
    daily_cost = 0.05
    usage = {'object_count': 0, 'size_bytes': 0}

    results = generate_s3_recommendations(resource_id, daily_cost, usage)

    assert len(results) == 1
    rec = results[0]
    assert rec['type'] == 'EMPTY_BUCKET'
    assert rec['severity'] == 'low'
    assert rec['resource_type'] == 'S3'
    assert rec['status'] == 'open'
    assert rec['estimated_savings_monthly'] == Decimal(str(daily_cost * 30))
    assert rec['estimated_savings_yearly'] == Decimal(str(daily_cost * 30 * 12))

    print("\n[S3] Recommendation Generated:")
    print(f"   Resource:  {rec['resource_id']}")
    print(f"   Type:      {rec['type']}")
    print(f"   Title:     {rec['title']}")
    print(f"   Severity:  {rec['severity']}")
    print(f"   Action:    {rec['recommended_action']}")
    print(f"   Saves:     ${rec['estimated_savings_monthly']:.2f}/month  |  ${rec['estimated_savings_yearly']:.2f}/year")
    print(f"   Status:    {rec['status']}")
    print("   PASSED - S3 empty bucket recommendation triggered correctly")


def test_s3_non_empty_bucket_no_recommendation():
    resource_id = "my-test-bucket-abc123"
    daily_cost = 0.50
    usage = {'object_count': 100, 'size_bytes': 1024000}

    results = generate_s3_recommendations(resource_id, daily_cost, usage)

    assert len(results) == 0
    print("\n[S3] No Recommendation Generated:")
    print(f"   Resource:  {resource_id}")
    print(f"   Objects:   {usage['object_count']}  |  Size: {usage['size_bytes']} bytes")
    print("   PASSED - S3 non-empty bucket correctly skipped")


def test_ec2_underutilized():
    resource_id = "i-1234567890abcdef0"
    daily_cost = 2.0
    usage = {
        'resource_type': 'EC2',
        'instance_type': 't3.large',
        'avg_cpu': 5.0,
        'max_cpu': 12.0,
        'min_cpu': 1.0,
        'data_points': 20
    }

    results = generate_ec2_recommendations(resource_id, daily_cost, usage)

    assert len(results) == 1
    rec = results[0]
    assert rec['type'] == 'UNDERUTILIZED'
    assert rec['resource_type'] == 'EC2'
    assert 't3.medium' in rec['recommended_action']
    assert rec['status'] == 'open'

    print("\n[EC2] Recommendation Generated:")
    print(f"   Resource:  {rec['resource_id']}")
    print(f"   Type:      {rec['type']}")
    print(f"   Title:     {rec['title']}")
    print(f"   Severity:  {rec['severity']}")
    print(f"   CPU Avg:   {rec['metrics_summary']['avg_cpu_7d']}%")
    print(f"   Action:    {rec['recommended_action']}")
    print(f"   Saves:     ${rec['estimated_savings_monthly']:.2f}/month  |  ${rec['estimated_savings_yearly']:.2f}/year")
    print(f"   Status:    {rec['status']}")
    print("   PASSED - EC2 underutilized instance flagged correctly")


def test_ec2_idle():
    resource_id = "i-1234567890abcdef0"
    daily_cost = 1.0
    usage = {
        'resource_type': 'EC2',
        'instance_type': 't3.nano',
        'avg_cpu': 2.0,
        'max_cpu': 4.0,
        'min_cpu': 0.5,
        'data_points': 20
    }

    results = generate_ec2_recommendations(resource_id, daily_cost, usage)

    assert len(results) == 1
    rec = results[0]
    assert rec['type'] == 'IDLE'
    assert rec['severity'] == 'high'

    print("\n[EC2] Recommendation Generated:")
    print(f"   Resource:  {rec['resource_id']}")
    print(f"   Type:      {rec['type']}")
    print(f"   Title:     {rec['title']}")
    print(f"   Severity:  {rec['severity']}")
    print(f"   CPU Avg:   {rec['metrics_summary']['avg_cpu_7d']}%")
    print(f"   Action:    {rec['recommended_action']}")
    print(f"   Saves:     ${rec['estimated_savings_monthly']:.2f}/month  |  ${rec['estimated_savings_yearly']:.2f}/year")
    print(f"   Status:    {rec['status']}")
    print("   PASSED - EC2 idle instance flagged correctly")


def test_ec2_healthy_no_recommendation():
    resource_id = "i-1234567890abcdef0"
    daily_cost = 1.0
    usage = {
        'resource_type': 'EC2',
        'instance_type': 't3.medium',
        'avg_cpu': 55.0,
        'max_cpu': 80.0,
        'min_cpu': 30.0,
        'data_points': 20
    }

    results = generate_ec2_recommendations(resource_id, daily_cost, usage)

    assert len(results) == 0
    print("\n[EC2] No Recommendation Generated:")
    print(f"   Resource:  {resource_id}")
    print(f"   CPU Avg:   {usage['avg_cpu']}%  |  Instance: {usage['instance_type']}")
    print("   PASSED - EC2 healthy instance correctly skipped")


if __name__ == "__main__":
    print("=" * 55)
    print("   RECOMMENDATION ENGINE - LOCAL TESTS")
    print("=" * 55)

    test_s3_empty_bucket()
    test_s3_non_empty_bucket_no_recommendation()
    test_ec2_underutilized()
    test_ec2_idle()
    test_ec2_healthy_no_recommendation()

    print("\n" + "=" * 55)
    print("   ALL TESTS PASSED")
    print("=" * 55)