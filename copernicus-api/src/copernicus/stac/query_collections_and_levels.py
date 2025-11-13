"""
    - trying to use pystac to better filter
    - does not work
"""

import src.copernicus.stac.constants as constants
from pystac_client import Client

client = Client.open(constants.COPERNICUS_STAC_URL)
# collection_search = client.collection_search(q='"sentinel-2" OR "sentinel-3" OR "sentinel-5p"')
collection_search = client.collection_search(q='"sentinel-5p" AND "L2"')
# collection_search = client.collection_search(
#     filter={
#         "op": "=",
#         "args": [
#             {
#                 "property": "platform"
#             },
#             "sentinel-2"
#         ]
#     }
# )

result = list(collection_search.collections_as_dicts())
print(len(result))
