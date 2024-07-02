import json
import boto3
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
import os

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

# Extract needed information
def extract_final_info(blocks):
    info = {
        "Issued To": "",
        "Responsible Person": "",
        "Address": "",
        "Waiver Number": "",
        "Operations Authorized": "",
        "List of Waived Regulations": "",
        "Effective Date Range": ""
    }

    capture_next = False
    address_line_count = 0

    for block in blocks:
        if block['BlockType'] == 'LINE' and block['Page'] == 1:
            text = block['Text']

            if "ISSUED TO" in text:
                capture_next = "Issued To"
            elif "ADDRESS" in text:
                capture_next = "Address"
                address_line_count = 0
            elif "Responsible Person:" in text:
                info["Responsible Person"] = text.split(":", 1)[1].strip()
            elif "Waiver Number:" in text:
                info["Waiver Number"] = text.split(":", 1)[1].strip()
            elif "OPERATIONS AUTHORIZED" in text:
                capture_next = "Operations Authorized"
                info[capture_next] = ""  # Initialize as empty to append lines
            elif "LIST OF WAIVED REGULATIONS BY SECTION AND TITLE" in text:
                capture_next = "List of Waived Regulations"
                info[capture_next] = ""  # Initialize as empty to append lines
            elif "effective from" in text.lower():
                date_parts = text.split("effective from", 1)[1].split(" to ", 1)
                if len(date_parts) == 2:
                    info["Effective Date Range"] = f"{date_parts[0].strip()} to {date_parts[1].strip()}"

            elif capture_next:
                if capture_next == "Address":
                    info[capture_next] += (text + " ") if address_line_count < 2 else ""
                    address_line_count += 1
                    if address_line_count == 2:
                        capture_next = False
                elif capture_next == "List of Waived Regulations":
                    # Append each new line to the List of Waived Regulations
                    info[capture_next] += text + " "
                    # Continue capturing until a new section starts
                    if any(keyword in text for keyword in ["STANDARD PROVISIONS"]):
                        capture_next = False
                elif capture_next == "Operations Authorized":
                    # Append each new line to the List of Waived Regulations
                    info[capture_next] += text + " "
                    # Continue capturing until a new section starts
                    if any(keyword in text for keyword in ["LIST OF WAIVED REGULATIONS BY SECTION AND TITLE"]):
                        capture_next = False
                else:
                    info[capture_next] = text
                    capture_next = False

    for key in info.keys():
        info[key] = info[key].strip()

    # Remove 'STANDARD PROVISIONS' from the final output if it was appended
    if "STANDARD PROVISIONS" in info["List of Waived Regulations"]:
        info["List of Waived Regulations"] = info["List of Waived Regulations"].replace("STANDARD PROVISIONS", "").strip()

    # Remove 'LIST OF WAIVED REGULATIONS BY SECTION AND TITLE' from the final output if it was appended
    if "LIST OF WAIVED REGULATIONS BY SECTION AND TITLE" in info["Operations Authorized"]:
        info["Operations Authorized"] = info["Operations Authorized"].replace("LIST OF WAIVED REGULATIONS BY SECTION AND TITLE", "").strip()

    return info

# S3 storage values
bucket_name = 'uav-waivers'
input_prefix = 'waivers-json/'
output_file_key = 'waivers_info.xlsx'

# List objects in the specified S3 bucket and prefix
response = s3.list_objects_v2(Bucket=bucket_name, Prefix=input_prefix)
print(response["Contents"]);
output_data = []

# Iterate through the files in the bucket
for obj in response.get('Contents', []):
    if obj['Key'].endswith('.json'):
        # Read the JSON file from S3
        json_file = s3.get_object(Bucket=bucket_name, Key=obj['Key'])
        textract_response = json.loads(json_file['Body'].read())
        final_extracted_info = extract_final_info(textract_response['Blocks'])
        output_data.append(final_extracted_info)

# Create a DataFrame from the output data
df = pd.DataFrame(output_data)

# Save the DataFrame to an Excel file in memory
excel_buffer = BytesIO()
df.to_excel(excel_buffer, index=False)

# Upload the Excel file to S3
s3.put_object(Bucket=bucket_name, Key=output_file_key, Body=excel_buffer.getvalue())

print(f"Data successfully written to s3://{bucket_name}/{output_file_key}")