from hda import Client
from pathlib import Path

# Configure user's credentials without a .hdarc
hdarc = Path(Path.home() / '.hdarc')

hda_client = Client()

# The JSON query loaded in the "query" variable
query = {
    "dataset_id": "EO:CRYO:DAT:HRSI:FSC",
    "productType": "TPROD",
    "productGroupId": "s1",
    "bbox": [
        -9.53592042,
        42.46825465,
        -7.0363102799999995,
        43.99700636
    ],
    "startdate": "2020-01-01T00:00:00.000Z",
    "enddate": "2021-01-01T23:59:59.999Z",
    "itemsPerPage": 200,
    "startIndex": 0
}

# Ask the result for the query passed in parameter
matches = hda_client.search(query)

# List the results
print(matches)
