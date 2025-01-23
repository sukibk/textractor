import re

address_line = "1722 N College Avenue/Suite C-243/Fayetteville, AR 72703"

info = {}

if len(address_line.split('/')) > 2:  # Case when we have three-row address
    address_components = address_line.split('/', 2)
    info["Street Name and Number"] = address_components[0] + '/' + address_components[1]
    city_state_zip = address_components[2]

    info["City"], rest = city_state_zip.split(",", 1)
    state_zip = re.search(r'([A-Z]{2}) (\d{5})', rest.strip())
    if state_zip:
        info["State"] = state_zip.group(1)
        info["Zip Code"] = state_zip.group(2)
    else:
        info["State"] = None
        info["Zip Code"] = None

print(info)