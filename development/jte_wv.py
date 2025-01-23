import json
import boto3
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
import os
from openpyxl import Workbook
from dateutil import parser
import re
from utils.module import check_waiver_codes as obtain_code_entries
#from project_files.utils.module import parse_address as get_address

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

# Defining strings to be removed from objects
string_remove = {
    "location": "This certificate is issued for the operations specifically described hereinafter. No person shall conduct any operation pursuant to the"
}

# Extract needed information
def extract_final_info(blocks, key):
    info = {
        "Issued To": "",
        "Responsible Person": "",
        "Address": "",
        "Street Name and Number": "",
        "City": "",
        "State": "",
        "Zip Code": "",
        "Waiver Number": "",
        "Operations Authorized": "",
        "List of Waived Regulations": "",
        "Effective Date": "",
        "Expire Date": "",
        "Waiver URL": ""
    }

    capture_next = False
    address_line_count = 0

    info["Waiver URL"] = key.replace("json", "pdf").replace("waivers-pdf", "https://www.faa.gov/sites/faa.gov/files/")

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
            elif "Responsible Party:" in text:
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
                    start_date = parser.parse(date_parts[0].strip())
                    end_date = parser.parse(date_parts[1].strip().split(",")[0].strip())
                    info["Effective Date"] = start_date.strftime('%m/%d/%Y')
                    info["Expire Date"] = end_date.strftime('%m/%d/%Y')

            elif capture_next:
                if capture_next == "Address":
                    info[capture_next] += (text + " ") if address_line_count < 3 else ""
                    address_line_count += 1
                    if address_line_count == 3:
                        capture_next = False
                        address_components = get_address(info["Address"])
                        if address_components:
                            info["Street Name and Number"] = address_components.get("Street Address", "")
                            info["City"] = address_components.get("City", "")
                            info["State"] = address_components.get("State", "")
                            info["Zip Code"] = address_components.get("ZIP Code", "")
                        else:
                            # Handle the case where address_components is None
                            info["Street Name and Number"] = "Unknown"
                            info["City"] = "Unknown"
                            info["State"] = "Unknown"
                            info["Zip Code"] = "Unknown"

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
        info["List of Waived Regulations"] = info["List of Waived Regulations"].replace("STANDARD PROVISIONS",
                                                                                        "").strip()

    # Remove 'LIST OF WAIVED REGULATIONS BY SECTION AND TITLE' from the final output if it was appended
    if "LIST OF WAIVED REGULATIONS BY SECTION AND TITLE" in info["Operations Authorized"]:
        info["Operations Authorized"] = info["Operations Authorized"].replace(
            "LIST OF WAIVED REGULATIONS BY SECTION AND TITLE", "").strip()
    # Remove redundant string from ["Address"]
    if string_remove["location"] in info["Address"]:
        info["Address"] = info["Address"].replace(
            string_remove["location"], "").strip()

    return info

# S3 storage values
bucket_name = 'auvsi-uav-waivers'
input_prefix = 'waivers-json/'
output_file_key = 'waivers_info.xlsx'

# Create a new Excel file with the required sheets
wb = Workbook()
waiver_data_sheet = wb.active
waiver_data_sheet.title = "Waiver Data"
locations_sheet = wb.create_sheet(title="Locations")

# Set up the headers for the sheets
waiver_data_headers = [
    "Operator ID",
    "Company ID",
    "Full Operator ID",
    "Effective Date",
    "Expire Date",
    "Waiver Number",
    "Waiver URL",
    "Daylight Operations (14 CFR § 107.29 Daylight operation)",
    "VLOS Operations (14 CFR §107.31 Visual line of sight aircraft operation)",
    "Visual Observer (14 CFR § 107.33 Visual observer)",
    "Multiple UAS (14 CFR § 107.35 Operation of multiple small unmanned aircraft)",
    "Over People (14 CFR § 107.39 Operation over human beings)",
    "Operation in Certain Airspace (14 CFR §107.41)",
    "Operating Limitations (14 CFR § 107.51 (a) for small unmanned aircraft)",
    "Operating Limitations (14 CFR §107.51 (b), (c) and (d) Operating limitations for small unmanned aircraft)",
    "Moving Vehicle or Aircraft (14 CFR § 107.25(b) Operation from a moving vehicle or aircraft)",
    "Over Moving Vehicles (14 CFR §107.145—Operation over Moving Vehicles)",
    "Operations Authorized"
]
locations_headers = [
    "Operator ID", "Company ID", "Full Operator ID", "Responsible Person",
    "Address", "City", "State", "ZIP", "Email", "Other Company", "Website", "Company"
]

waiver_data_sheet.append(waiver_data_headers)
locations_sheet.append(locations_headers)

# List objects in the specified S3 bucket and prefix
response = s3.list_objects_v2(Bucket=bucket_name, Prefix=input_prefix)
#output_data = []

# Iterate through the files in the bucket
for obj in response.get('Contents', []):
    if obj['Key'].endswith('.json'):
        # Read the JSON file from S3
        json_file = s3.get_object(Bucket=bucket_name, Key=obj['Key'])
        textract_response = json.loads(json_file['Body'].read())
        final_extracted_info = extract_final_info(textract_response['Blocks'], obj['Key'])
        #append(final_extracted_info)

        responsible_person = final_extracted_info["Responsible Person"].strip()
        address_street = final_extracted_info["Street Name and Number"].strip()
        address_city = final_extracted_info["City"].strip()
        address_state = final_extracted_info["State"].strip()
        address_zip = final_extracted_info["Zip Code"].strip()

        # Check if Responsible Person exists in Locations table
        location_match = None
        for row in locations_sheet.iter_rows(min_row=2, values_only=True):
            if row[3].strip() == responsible_person:
                location_match = row
                break

        if not location_match:
            # Responsible Person does not exist, insert new row
            new_operator_id = max([row[0] for row in locations_sheet.iter_rows(min_row=2, values_only=True)] or [0]) + 1
            if responsible_person in final_extracted_info["Issued To"]:
                company_id = "INDIVIDUAL"
            else:
                company_ids = [int(row[1][1:]) for row in locations_sheet.iter_rows(min_row=2, values_only=True) if row[1].startswith('C')]
                new_company_id = max(company_ids or [0]) + 1
                company_id = f"C{new_company_id}"
            full_operator_id = f"{new_operator_id}-{company_id}"

            new_location = [
                new_operator_id, company_id, full_operator_id, responsible_person,
                address_street, address_city, address_state, address_zip,
                "", "", "", "" if company_id == "INDIVIDUAL" else final_extracted_info["Issued To"]
            ]
            locations_sheet.append(new_location)
        else:
            # Responsible Person exists, check if the address matches
            if location_match[4].strip() != address_street:
                # Addresses are different, update the location
                if location_match[11] == final_extracted_info["Issued To"]:
                    # Same company name
                    updated_location = [
                        location_match[0], location_match[1], f"{location_match[0]}-{location_match[1]}",
                        responsible_person, address_street, address_city, address_state, address_zip,
                        "", "", "", location_match[11]
                    ]
                else:
                    # Different company name
                    company_match = None
                    for row in locations_sheet.iter_rows(min_row=2, values_only=True):
                        if row[11] == final_extracted_info["Issued To"]:
                            company_match = row
                            break
                    if company_match:
                        company_id = company_match[1]
                    else:
                        company_ids = [int(row[1][1:]) for row in locations_sheet.iter_rows(min_row=2, values_only=True) if row[1].startswith('C')]
                        new_company_id = max(company_ids or [0]) + 1
                        company_id = f"C{new_company_id}"
                    updated_location = [
                        location_match[0], company_id, f"{location_match[0]}-{company_id}",
                        responsible_person, address_street, address_city, address_state, address_zip,
                        "", "", "", final_extracted_info["Issued To"]
                    ]
                for i, value in enumerate(updated_location):
                    locations_sheet.cell(row=location_match[0]+1, column=i+1, value=value)

        # Store the Operator ID, Company ID, and Full Operator ID for Waiver Data
        operator_id = new_operator_id
        company_id = new_location[1]
        full_operator_id = new_location[2]

        # Add entry to Waiver Data sheet
        effective_date = final_extracted_info["Effective Date"]
        expire_date = final_extracted_info["Expire Date"]

        waiver_url = final_extracted_info["Waiver URL"]

        waived_regulations = obtain_code_entries(final_extracted_info["List of Waived Regulations"])

        new_waiver_data = [
            operator_id, company_id, full_operator_id, effective_date,
            expire_date, final_extracted_info["Waiver Number"],
            waiver_url,
            waived_regulations["Daylight Operations"],
            waived_regulations["VLOS Operations"],
            waived_regulations["Visual Observer"],
            waived_regulations["Multiple UAS"],
            waived_regulations["Over People"],
            waived_regulations["Operation in Certain Airspace"],
            waived_regulations["Operating Limitations (a)"],
            waived_regulations["Operating Limitations (b, c, d)"],
            waived_regulations["Moving Vehicle or Aircraft"],
            waived_regulations["Over Moving Vehicles"],
            final_extracted_info["Operations Authorized"]
        ]
        waiver_data_sheet.append(new_waiver_data)

# Save the new Excel file locally
output_file_path = 'new_outputs2.xlsx'
wb.save(output_file_path)
print(f"Data successfully written to {output_file_path}")
