from hda import Client
from pathlib import Path

# Configure user's credentials without a .hdarc
hdarc = Path(Path.home() / '.hdarc')

hda_client = Client()

metadata = hda_client.metadata("EO:MO:DAT:WIND_MED_PHY_HR_L3_NRT_012_104")

print(metadata)
