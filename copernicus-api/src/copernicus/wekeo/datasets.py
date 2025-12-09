from hda import Client, Configuration
from pathlib import Path

import json

# Default location expected by hda package
hdarc = Path(Path.home() / '.hdarc')

hda_client = Client()

# Ask the result for the query passed in parameter
matches = hda_client.datasets()

with open('datasets.json', 'w') as f:
    json.dump(matches, f, indent=4)

# List the results
print(matches)