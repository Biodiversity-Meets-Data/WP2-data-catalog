"""
    - deprecated
    - process and convert a single dataset
"""

import constants
from convert_collection import convert_collection
from pystac_client import Client
import metapype.eml.export

collection_id = "sentinel-5p-l2-o3-nrti"
print("processing {0}".format(collection_id))

client = Client.open(constants.COPERNICUS_STAC_URL)
collection = client.get_collection(collection_id)
# collection = collection.to_dict()
# print(json.dumps(collection, indent=4))
eml = convert_collection(collection)

xml_str = metapype.eml.export.to_xml(eml)
file_path = "stac_converted.xml"
with open(file_path, 'w') as f:
    f.write(xml_str)
    print("eml saved {0}".format(file_path))

print("collection processed")