import boto3
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')

# Initialize the Location Service client
location_client = boto3.client('location',
                               aws_access_key_id=aws_access_key_id,
                               aws_secret_access_key=aws_secret_access_key,
                               region_name=aws_region)

# The place index resource you created in AWS Location Service
# !!!REMOVE DASH FOR EXECUTION!!! place_index_v1 = 'AUVSIPlaceIndex'

def parse_address(address):
    response_v1 = location_client.search_place_index_for_text(
        IndexName= place_index_v1,
        Text=address,
        MaxResults=1
    )

    if response_v1['Results']:
        result = response_v1['Results'][0]['Place']
        components = {
            'Street Address': result.get('AddressNumber', '') + ' ' + result.get('Street', ''),
            'City': result.get('Municipality', ''),
            'State': result.get('Region', ''),
            'ZIP Code': result.get('PostalCode', '').split(" ")[0]
        }
        return components
    else:
        return None

