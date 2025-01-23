import json
import boto3
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
import os
from openpyxl import load_workbook

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

# Helper functions for state conversion and cleaning address
def convert_state_acronym_to_full(state_acronym):
    states = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
        "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
        "WI": "Wisconsin", "WY": "Wyoming"
    }
    return states.get(state_acronym, state_acronym)

def extract_address_parts(address):
    parts = address.split(',')
    street = parts[0].strip()
    city = parts[1].strip() if len(parts) > 1 else ""
    state_zip = parts[2].strip() if len(parts) > 2 else ""
    state, zip_code = state_zip.split() if len(state_zip.split()) == 2 else ("", "")
    state = convert_state_acronym_to_full(state)
    return street, city, state, zip_code

# S3 storage values
bucket_name = 'uav-waivers'
input_prefix = 'waivers-json/'
output_file_key = 'waivers_data.xlsx'

# Download the existing Excel file from S3
existing_file = s3.get_object(Bucket=bucket_name, Key=output_file_key)
excel_file = BytesIO(existing_file['Body'].read())
wb = load_workbook(excel_file)
sheet_names = wb.sheetnames

print("Sheet names in the Excel file:")
for sheet_name in sheet_names:
    print(sheet_name)

# Ensure the required sheets exist
if 'Waiver Data' not in sheet_names or 'Locations' not in sheet_names:
    raise ValueError("The required sheets 'Waiver Data' and 'Locations' are not found in the Excel file.")

# Load tables
excel_file.seek(0)  # Reset the pointer to the beginning of the BytesIO object
waiver_data_df = pd.read_excel(excel_file, sheet_name='Waiver Data')
excel_file.seek(0)  # Reset the pointer again
locations_df = pd.read_excel(excel_file, sheet_name='Locations')

# List objects in the specified S3 bucket and prefix
response = s3.list_objects_v2(Bucket=bucket_name, Prefix=input_prefix)
output_data = []

# Iterate through the files in the bucket
for obj in response.get('Contents', []):
    if obj['Key'].endswith('.json'):
        # Read the JSON file from S3
        json_file = s3.get_object(Bucket=bucket_name, Key=obj['Key'])
        textract_response = json.loads(json_file['Body'].read())
        final_extracted_info = extract_final_info(textract_response['Blocks'])
        output_data.append(final_extracted_info)

        responsible_person = final_extracted_info["Responsible Person"].strip()
        address_street, address_city, address_state, address_zip = extract_address_parts(final_extracted_info["Address"])

        # Check if Responsible Person exists in Locations table
        location_match = locations_df[locations_df['Responsible Person'].str.strip() == responsible_person]

        company_ids = locations_df['Company ID'].str.extract(r'(\d+)$').dropna().astype(int)

        if location_match.empty:
            # Responsible Person does not exist, insert new row
            new_operator_id = locations_df['Operator ID'].max() + 1
            if responsible_person in final_extracted_info["Issued To"]:
                company_id = "INDIVIDUAL"
            else:
                new_company_id = company_ids.max().values[0] + 1 if not company_ids.empty else 1
                company_id = f"C{new_company_id}"
            full_operator_id = f"{new_operator_id}-{company_id}"

            new_location = {
                "Operator ID": new_operator_id,
                "Company ID": company_id,
                "Full Operator ID": full_operator_id,
                "Responsible Person": responsible_person,
                "Address": address_street,
                "City": address_city,
                "State": address_state,
                "ZIP": address_zip,
                "Email": "",
                "Other Company": "",
                "Website": "",
                "Company": "" if company_id == "INDIVIDUAL" else final_extracted_info["Issued To"]
            }
            locations_df = pd.concat([locations_df, pd.DataFrame([new_location])], ignore_index=True)
        else:
            # Responsible Person exists, check if the address matches
            location_match = location_match.iloc[0]
            if location_match["Address"].strip() != address_street:
                # Addresses are different, update the location
                location_match["Address"] = address_street
                location_match["City"] = address_city
                location_match["State"] = address_state
                location_match["ZIP"] = address_zip
                if location_match["Company"] == final_extracted_info["Issued To"]:
                    # Same company name
                    location_match["Full Operator ID"] = f"{location_match['Operator ID']}-{location_match['Company ID']}"
                else:
                    # Different company name
                    company_match = locations_df[locations_df["Company"] == final_extracted_info["Issued To"]]
                    if not company_match.empty:
                        location_match["Company ID"] = company_match.iloc[0]["Company ID"]
                    else:
                        new_company_id = company_ids.max().values[0] + 1 if not company_ids.empty else 1
                        location_match["Company ID"] = f"C{new_company_id}"
                    location_match["Full Operator ID"] = f"{location_match['Operator ID']}-{location_match['Company ID']}"
                locations_df.update(location_match)

# Create a DataFrame from the output data
waiver_data_df = pd.concat([waiver_data_df, pd.DataFrame(output_data)], ignore_index=True)

# Update the existing workbook with the new data
waiver_data_sheet = wb["Waiver Data"]
locations_sheet = wb["Locations"]

# Clear the existing data in the sheets
for row in waiver_data_sheet.iter_rows(min_row=2, max_row=waiver_data_sheet.max_row):
    for cell in row:
        cell.value = None

for row in locations_sheet.iter_rows(min_row=2, max_row=locations_sheet.max_row):
    for cell in row:
        cell.value = None

# Write the updated data back to the sheets
for row_idx, row in waiver_data_df.iterrows():
    for col_idx, value in enumerate(row):
        waiver_data_sheet.cell(row=row_idx + 2, column=col_idx + 1, value=value)

for row_idx, row in locations_df.iterrows():
    for col_idx, value in enumerate(row):
        locations_sheet.cell(row=row_idx + 2, column=col_idx + 1, value=value)

# Save the updated workbook to a BytesIO object
excel_buffer = BytesIO()
wb.save(excel_buffer)
excel_buffer.seek(0)

# Upload the updated Excel file to S3
s3.put_object(Bucket=bucket_name, Key=output_file_key, Body=excel_buffer.getvalue())

print(f"Data successfully written to s3://{bucket_name}/{output_file_key}")
