from hda import Client
from pathlib import Path
import json

# Configure user's credentials without a .hdarc
hdarc = Path(Path.home() / '.hdarc')

hda_client = Client()

response = hda_client.get("datasets?q=burned")

with open('rest_query.json', 'w') as f:
    json.dump(response, f, indent=4)

# List the results
print(response)