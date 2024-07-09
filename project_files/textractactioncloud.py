import boto3
import time
import json
import logging
import os
from PyPDF2 import PdfReader
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS S3 bucket name and subfolder
bucket_name = 'uav-waivers'
subfolder = 'waivers-raw-pdf'

# S3 bucket to save Textract results
results_dir = 'waivers-json'
os.makedirs(results_dir, exist_ok=True)

# Load environment variables from .env file
load_dotenv()
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')

# Initialize the S3 and Textract clients
try:
    s3_client = boto3.client('s3',
                             aws_access_key_id=aws_access_key_id,
                             aws_secret_access_key=aws_secret_access_key,
                             region_name=aws_region)


    textract_client = boto3.client('textract',
                                   aws_access_key_id=aws_access_key_id,
                                   aws_secret_access_key=aws_secret_access_key,
                                   region_name=aws_region)
except (NoCredentialsError, PartialCredentialsError) as e:
    logger.error("AWS credentials not found or incomplete: %s", str(e))
    raise

# Supported document extensions
SUPPORTED_EXTENSIONS = ('.pdf', '.jpg', '.jpeg', '.png', '.tiff')

# Get PDF files from S3 source subfolder
def get_s3_files(bucket, subfolder):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=subfolder)
        files = [item['Key'] for item in response.get('Contents', []) if
                 item['Key'].lower().endswith(SUPPORTED_EXTENSIONS)]
        return files
    except Exception as e:
        logger.error("Failed to list objects in S3 bucket: %s", str(e))
        return []

# Check if the result file already exists in S3 results directory
def result_exists(file_name):
    result_key = f"{results_dir}/{os.path.basename(file_name).replace('.pdf', '.json')}"
    try:
        s3_client.head_object(Bucket=bucket_name, Key=result_key)
        return True
    except Exception as e:
        return False

# PDF validation - Check if PDF is corrupted
def validate_pdf(bucket, document):
    local_path = f"/tmp/{os.path.basename(document)}"
    try:
        s3_client.download_file(bucket, document, local_path)
        with open(local_path, 'rb') as f:
            reader = PdfReader(f)
            num_pages = len(reader.pages)
            logger.info("%s is a valid PDF with %d pages.", document, num_pages)
            return True
    except Exception as e:
        logger.error("%s is not a valid PDF. Error: %s", document, str(e))
        return False
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

# Textract service
def start_textract(bucket, document):
    try:
        response = textract_client.start_document_text_detection(
            DocumentLocation={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': document
                }
            }
        )
        return response['JobId']
    except Exception as e:
        logger.error("Failed to start Textract job on %s. Error: %s", document, str(e))
        raise

# Getting textract results
def get_textract_result(job_id):
    while True:
        response = textract_client.get_document_text_detection(JobId=job_id)
        status = response['JobStatus']
        if status in ['SUCCEEDED', 'FAILED']:
            return response
        logger.info("Waiting for Textract job %s to complete. Current status: %s", job_id, status)
        time.sleep(5)

# Saving results to S3 results subfolder
def save_results(response, file_name):
    local_path = os.path.join('/tmp', os.path.basename(file_name).replace('.pdf', '.json'))
    s3_key = f"{results_dir}/{os.path.basename(local_path)}"
    try:
        with open(local_path, 'w') as f:
            json.dump(response, f)
        logger.info("Results saved to %s", local_path)

        # Upload the JSON file back to S3
        s3_client.upload_file(local_path, bucket_name, s3_key)
        logger.info("Uploaded %s to S3 bucket %s", local_path, results_dir)
    except Exception as e:
        logger.error("Failed to save or upload results for %s. Error: %s", file_name, str(e))

# Main function
def process_documents(bucket, subfolder):
    files = get_s3_files(bucket, subfolder)
    for file in files:
        result_key = f"{results_dir}/{os.path.basename(file).replace('.pdf', '.json')}"
        if result_exists(result_key):
            logger.info("Skipping %s as result already exists.", file)
            continue
        if file.lower().endswith('.pdf') and not validate_pdf(bucket, file):
            logger.warning("Skipping invalid PDF file: %s", file)
            continue
        logger.info("Processing %s", file)
        try:
            job_id = start_textract(bucket, file)
            response = get_textract_result(job_id)
            save_results(response, file)
        except textract_client.exceptions.UnsupportedDocumentException as e:
            logger.error("Failed to process %s. Error: %s", file, str(e))
        except Exception as e:
            logger.error("An unexpected error occurred while processing %s. Error: %s", file, str(e))

process_documents(bucket_name, subfolder)
