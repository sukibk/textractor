import re

# Define the waiver codes and corresponding column names
waiver_codes = {
    "107.29": "Daylight Operations (14 CFR § 107.29 Daylight operation)",
    "107.31": "VLOS Operations (14 CFR §107.31 Visual line of sight aircraft operation)",
    "107.33": "Visual Observer (14 CFR § 107.33 Visual observer)",
    "107.35": "Multiple UAS (14 CFR § 107.35 Operation of multiple small unmanned aircraft)",
    "107.39": "Over People (14 CFR § 107.39 Operation over human beings)",
    "107.41": "Operation in Certain Airspace (14 CFR §107.41)",
    "107.51(a)": "Operating Limitations (14 CFR § 107.51 (a) for small unmanned aircraft)",
    "107.51": "Operating Limitations (14 CFR §107.51 (b), (c) and (d) Operating limitations for small unmanned aircraft)",
    "107.25(b)": "Moving Vehicle or Aircraft (14 CFR § 107.25(b) Operation from a moving vehicle or aircraft)",
    "107.145": "Over Moving Vehicles (14 CFR §107.145—Operation over Moving Vehicles)"
}

# Sample data
data = [
    "14 CFR § 107.39-Operation over human beings 14 CFR § 07.145-Operations over moving vehicles",
    "14 CFR § 107.39-Operation over human beings 14 CFR § 107.145-Operations over moving vehicles",
    "14 CFR § 107.39-Operation over human beings 14 CFR § 107.145-Operations over moving vehicles",
    "14 CFR § 107.39-Operation over human beings 14 CFR § 07.145-Operations over moving vehicles",
    "14 CFR § 107.39-Operation over human beings 14 CFR § 107.145-Operations over moving vehicles",
    "14 CFR § 107.39-Operation over human beings 14 CFR § 107.145-Operations over moving vehicles",
    "14 CFR § 07.39-Operation over human beings",
    "14 CFR § 107.39-Operation over human beings 14 CFR § 107.145-Operations over moving vehicles",
    "14 CFR § 107.51(b)-Operating limitations for small unmanned aircraft - Altitude",
    "14 CFR § 107.51(b)-Operating limitations for small unmanned aircraft - Altitude",
    "14 CFR § 107.39-Operation over human beings",
    "14 CFR § 107.31-Visual line of sight aircraft operation",
    "14 CFR § 107.51(b)-Operating limitations for small unmanned aircraft - Altitude",
    "14 CFR § 107.51(b)-Operating limitations for small unmanned aircraft - Altitude",
    "14 CFR § 107.39-Operation over human beings",
    "14 CFR § 107.39-Operation over human beings 14 CFR § 107.145-Operations over moving vehicles",
    "14 CFR §§ 107.29(a)(2) & (b)-Anti-collision light requirement for operations at night and during periods of civil twilight, and 107.35-Operation of multiple small unmanned aircraft systems",
    "14 CFR §§ 107.31-Visual line of sight aircraft operation, and 107.33(b) & (c)(2)-Visual observer",
    "14 CFR §§ 107.39-Operation over human beings, and 107.145-Operations over moving vehicles",
    "14 CFR § 107.31-Visual line of sight aircraft operation",
    "14 CFR § 107.31-Visual line of sight aircraft operation",
    "14 CFR § 107.35-Operation of multiple small unmanned aircraft systems",
    "14 CFR § 107.31-Visual line of sight aircraft operation",
    "14 CFR §§ 107.29(a)(2) & (b)-Anti-collision light requirement for operations at night and during periods of civil twilight, and 107.35-Operation of multiple small unmanned aircraft systems",
    "14 CFR § 107.31-Visual line of sight aircraft operation"
]

# Function to check for waiver codes in a string
def check_waiver_codes(entry, codes):
    result = {name: '' for name in codes.values()}
    for code, name in codes.items():
        if code == "107.51":
            pattern = re.compile(r'(107|07)\.51\((b|c|d)\)')
        else:
            pattern = re.compile(r'(?<!\d)(107|07)\.' + re.escape(code[4:]).replace(r'\.', r'\.') + r'(?!\d)')
        if pattern.search(entry):
            result[name] = '+'
    return result

# Process each entry and store the results in local variables
for i, entry in enumerate(data):
    results = check_waiver_codes(entry, waiver_codes)
    print(f"Entry {i+1}:")
    for name, value in results.items():
        print(f"{name}: {value}")
    print()

