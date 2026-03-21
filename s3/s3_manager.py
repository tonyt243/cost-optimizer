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

    :param log: The file path to the log file
    '''
    if log == None: return False

    try:
        response = s3_cli.upload_file(log, bucket_name, logs_object + "/" + log)
    except ClientError as e:
        logging.error(e)
        return False
    except FileNotFoundError as f:
        logging.error(f)
        return False
    
    return True

def UploadRawToS3Bucket(raw):
    '''
    Uploads raw data to the cost-optimizer-data-855521167206 bucket
    in the raw object.

    :param raw: The file path to the raw file
    '''
    if raw == None: return False

    try:
        response = s3_cli.upload_file(raw, bucket_name, raw_object + "/" + raw)
    except ClientError as e:
        logging.error(e)
        return False
    except FileNotFoundError as f:
        logging.error(f)
        return False
    
    return True

def UploadProcessedToS3Bucket(proc):
    '''
    Uploads processed data to the cost-optimizer-data-855521167206 bucket
    in the processed object.

    :param proc: The file path to the processed file
    '''
    if proc == None: return False

    try:
        response = s3_cli.upload_file(proc, bucket_name, processed_object + "/" + proc)
    except ClientError as e:
        logging.error(e)
        return False
    except FileNotFoundError as f:
        logging.error(f)
        return False
    
    return True

def DownloadLogFromS3Bucket(log, file_out):
    '''
    Downloads a log currently in the log object of the S3 Bucket

    :param log: The name of the log file
    :param file_out: The name of the local file to output to
    '''
    if log == None: return False

    try:
        response = s3_cli.download_file(bucket_name, logs_object + "/" + log, file_out)
    except ClientError as e:
        logging.error(e)
        return False

    return True

def DownloadRawFromS3Bucket(raw, file_out):
    '''
    Downloads a raw currently in the raw object of the S3 Bucket

    :param raw: The name of the raw file
    :param file_out: The name of the local file to output to
    '''
    if raw == None: return False

    try:
        response = s3_cli.download_file(bucket_name, raw_object + "/" + raw, file_out)
    except ClientError as e:
        logging.error(e)
        return False
    
    return True

def DownloadProcessedFromS3Bucket(proc, file_out):
    '''
    Downloads a processed file currently in the processed object of
    the S3 Bucket.

    :param proc: The name of the processed file
    :param file_out: The name of the local file to output to
    '''
    if proc == None: return False

    try:
        response = s3_cli.download_file(bucket_name, processed_object + "/" + proc, file_out)
    except ClientError as e:
        logging.error(e)
        return False
    
    return True