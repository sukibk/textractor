import requests
from bs4 import BeautifulSoup
import boto3
import os
import fitz  # PyMuPDF for PDF processing
from dotenv import load_dotenv
from io import BytesIO

# Base URL with a placeholder for the page number
base_url = "https://www.faa.gov/uas/commercial_operators/part_107_waivers/waivers_issued?page={}"

# AWS S3 bucket name and subfolder
bucket_name = "auvsi-uav-waivers"
subfolder = "waivers-raw-pdf"  # Specify the subfolder in your S3 bucket

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


# Download PDF file to subfolder if it doesn't exist there already
def download_and_store_first_page(pdf_url, bucket_name, s3_key):
    # Check if the file already exists in S3
    try:
        s3.head_object(Bucket=bucket_name, Key=s3_key)
        print(f"File {s3_key} already exists in S3. Skipping...")
        return
    except Exception as e:
        # File does not exist, proceed to download and store first page
        response = requests.get(pdf_url)
        if response.status_code == 200:
            with BytesIO(response.content) as pdf_file:
                # Load the PDF into PyMuPDF
                pdf_document = fitz.open(stream=pdf_file, filetype="pdf")

                # Create a new PDF to store only the first page
                first_page_pdf = fitz.open()  # Empty PDF

                # Insert the first page from the original PDF
                first_page_pdf.insert_pdf(pdf_document, from_page=0, to_page=0)

                # Save the single-page PDF to a BytesIO object
                single_page_pdf_io = BytesIO()
                first_page_pdf.save(single_page_pdf_io)
                first_page_pdf.close()
                pdf_document.close()

                # Upload the single-page PDF to S3
                single_page_pdf_io.seek(0)
                s3.put_object(Bucket=bucket_name, Key=s3_key, Body=single_page_pdf_io.getvalue())
                print(f"Stored first page of {pdf_url} to s3://{bucket_name}/{s3_key}")


# Get PDF links from a specific page
def get_pdf_links(page_url):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    pdf_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.lower().endswith('.pdf'):
            pdf_links.append(href)
    return pdf_links


# Iterate through multiple pages
start_page = 1
end_page = 1  # Adjust the range as needed

for page_number in range(start_page, end_page + 1):
    page_url = base_url.format(page_number)
    print(f"Processing page: {page_url}")
    pdf_links = get_pdf_links(page_url)

    for pdf_link in pdf_links:
        pdf_url = pdf_link
        if not pdf_url.startswith('http'):
            pdf_url = f"https://www.faa.gov{pdf_url}"

        # Extract the file name directly from the URL
        pdf_name = os.path.basename(pdf_url)  # Get the name from the URL
        # s3_key = f"{subfolder}/{pdf_name}"
        #
        # download_and_store_first_page(pdf_url, bucket_name, s3_key)

        # Only process the PDF if its name contains "2024"
        if "2024" in pdf_name:
            s3_key = f"{subfolder}/{pdf_name}"
            download_and_store_first_page(pdf_url, bucket_name, s3_key)
        else:
            print(f"Skipping {pdf_name}, as it does not contain '2024'")
