import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamo_db = boto3.resource('dynamodb')
cost_analysis_table = dynamo_db.Table('CostOptimizer-CostAnalysis')
resource_metrics_table = dynamo_db.Table('CostOptimizer-ResourceMetrics')

def AddItemToCostAnalysis(item):
    '''
    Adds a new item to the CostOptimizer-CostAnalysis table in
    DynamoDB. The item must be a 3-tuple, otherwise the item
    will not be added.

    :param item: Contains a tuple of the form 
                (analysis_id, DateIndex, date)
    :returns: True if the item was added; False otherwise
    '''
    if len(item) != 3: return False

    for i in range(len(item)):
        if item[i] is None:
            return False

    Item={
        'analysis_id' : item[0],
        'DateIndex' : item[1],
        'date' : item[2]
    }
    try:
        cost_analysis_table.put_item(Item)
    except Exception as e:
        return False

    return True

def AddItemToResourceMetrics(item):
    '''
    Adds a new item to the CostOptimizer-ResourceMetrics table in
    DynamoDB. The item must be a 3-tuple, otherwise the item
    will not be added.

    :param item: Contains a tuple of the form 
                (resource_id, timestamp, resource_type)
    :returns: True if the item is added; False otherwise
    '''
    if len(item) != 4: return False

    for i in range(len(item)):
        if item[i] is None:
            return False

    Item={
        'resource_id' : item[0],
        'timestamp' : item[1],
        'resource_type' : item[2],
        'timestamp' : item[1]
    }
    
    try:
        resource_metrics_table.put_item(Item)
    except Exception as e:
        return False

    return True


def GetItemFromCostAnalysis(key):
    '''
    Retrieves an item from the CostOptimizer-CostAnalysis table in
    DynamoDB. The key cannot be a null value.

    :param key: The primary key analysis_id
    :returns: The query using the key; None otherwise
    '''
    if key == None: return None

    response = cost_analysis_table.query(
        KeyConditionExpression = Key('analysis_id').eq(key)
    )

    items = response['Item']

    return items

def GetItemFromResourceMetrics(key):
    '''
    Retrieves an item from the CostOptimizer-CostAnalysis table in
    DynamoDB. The key cannot be a null value.

    :param key: The primary key analysis_id
    :returns: The query using the key; None otherwise
    '''
    if key == None: return None

    response = resource_metrics_table.query(
        KeyConditionExpression = Key('analysis_id').eq(key)
    )

    items = response['Item']

    return items
