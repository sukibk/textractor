import requests
from bs4 import BeautifulSoup
import boto3
import os
from dotenv import load_dotenv

# URL of the page containing PDF links
url = "https://www.faa.gov/uas/commercial_operators/part_107_waivers/waivers_issued?page=3"

# AWS S3 bucket name and subfolder
bucket_name = "auvsi-uav-waivers"
subfolder = "waivers-raw-pdf"  # specify the subfolder in your S3 bucket

# Load environment variables from .env file
load_dotenv()
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')

# Initialize boto3 S3 client with credentials
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

# Download pdf file to subfolder if it doesn't exist there already
def download_pdf_to_s3(pdf_url, bucket_name, s3_key):
    # Check if the file already exists in S3
    try:
        s3.head_object(Bucket=bucket_name, Key=s3_key)
        print(f"File {s3_key} already exists in S3. Skipping...")
    except Exception as e:
        # File does not exist, download and upload
        response = requests.get(pdf_url)
        s3.put_object(Bucket=bucket_name, Key=s3_key, Body=response.content)
        print(f"Downloaded {pdf_url} to s3://{bucket_name}/{s3_key}")

# Get pdf links from the actual Web page
def get_pdf_links(page_url):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    pdf_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.lower().endswith('.pdf'):
            pdf_links.append(href)
    return pdf_links

pdf_links = get_pdf_links(url)

for pdf_link in pdf_links:
    pdf_url = pdf_link
    if not pdf_url.startswith('http'):
        pdf_url = f"https://www.faa.gov{pdf_url}"
    pdf_name = os.path.basename(pdf_url)
    s3_key = f"{subfolder}/{pdf_name}"
    download_pdf_to_s3(pdf_url, bucket_name, s3_key)