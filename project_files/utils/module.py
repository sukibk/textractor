# import boto3
# import os
# from dotenv import load_dotenv
import re

# # Load environment variables from .env file
# load_dotenv()
# aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
# aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
# aws_region = os.getenv('AWS_REGION')
#
# # Initialize the Location Service client
# location_client = boto3.client('location',
#                                aws_access_key_id=aws_access_key_id,
#                                aws_secret_access_key=aws_secret_access_key,
#                                region_name=aws_region)
#
# # The place index resource you created in AWS Location Service
# # !!!REMOVE DASH FOR EXECUTION!!! place_index_v1 = 'AUVSIPlaceIndex'
#
# def parse_address(address):
#     response_v1 = location_client.search_place_index_for_text(
#         IndexName= place_index_v1,
#         Text=address,
#         MaxResults=1
#     )
#
#     if response_v1['Results']:
#         result = response_v1['Results'][0]['Place']
#         components = {
#             'Street Address': result.get('AddressNumber', '') + ' ' + result.get('Street', ''),
#             'City': result.get('Municipality', ''),
#             'State': result.get('Region', ''),
#             'ZIP Code': result.get('PostalCode', '').split(" ")[0]
#         }
#         return components
#     else:
#         return None


# Define the waiver codes and corresponding column names
waiver_codes = {
    "107.29": "Daylight Operations",
    "107.31": "VLOS Operations",
    "107.33": "Visual Observer",
    "107.35": "Multiple UAS",
    "107.39": "Over People",
    "107.41": "Operation in Certain Airspace",
    "107.51(a)": "Operating Limitations (a)",
    "107.51": "Operating Limitations (b, c, d)",
    "107.25(b)": "Moving Vehicle or Aircraft",
    "107.145": "Over Moving Vehicles"
}

# Function to check for waiver codes in a string
def check_waiver_codes(entry):
    result = {name: '' for name in waiver_codes.values()}
    for code, name in waiver_codes.items():
        if code == "107.51":
            pattern = re.compile(r'(107|07)\.51\((b|c|d)\)')
        else:
            pattern = re.compile(r'(?<!\d)(107|07)\.' + re.escape(code[4:]).replace(r'\.', r'\.') + r'(?!\d)')
        if pattern.search(entry):
            result[name] = '+'
    return result

state_mapping = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"
}

# Function to convert state code to state name
def convert_state_code_to_name(state_code):
    return state_mapping.get(state_code.upper(), "Invalid state code")