import boto3
import logging
from botocore.exceptions import ClientError

s3_cli = boto3.client('s3')
bucket_name = "cost-optimizer-data-855521167206"
raw_object = "raw"
processed_object = "processed"
logs_object = "logs"

def UploadLogToS3Bucket(log):
    '''
    Uploads a log to the cost-optimizer-data-855521167206 bucket
    in the log object.

    :param log: The file_path to the log file
    '''
    if log == None: return None

    try:
        response = s3_cli.upload_file(log, bucket_name, logs_object + "/" + log)
    except ClientError as e:
        logging.error(e)
        return False
    
    return True

def DownloadLogFromS3Bucket(log, file_out):
    '''
    Downloads a log currently in the log object of the S3 Bucket

    :param log: The name of the log file
    :param file_out: The name of the local file
    '''
    if log == None: return None

    try:
        response = s3_cli.download_file(bucket_name, logs_object + "/" + log, file_out)
    except ClientError as e:
        logging.error(e)
        return False

    return True

