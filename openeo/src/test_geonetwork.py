# soilgrids has an uuid of 8315df49-bde3-4138-8f71-9b722f3afd06
import argparse
import logging
import requests
import json
from src.extract_geonetwork import SoilGrids

# setup logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# parser for arguments
parser = argparse.ArgumentParser(
    prog='geonetwork query',
    description='extract relevant data from a geonetwork catalogue')
# setup arguments
parser.add_argument('-d', '--uuid', required=True, help="uuid for dataset")
# parse arguments
args = parser.parse_args()

# Set up your server and the query URL:
server = "https://metadatacatalogue.lifewatch.eu"
query_url = server + f"/srv/api/records?uuid={args.uuid}"
logger.info(f"query url: {query_url}")

# Send a put request to the endpoint
response = requests.get(query_url)

try:
    soilgrids = SoilGrids()
    dataset = soilgrids.check_response(response)
    print(json.dumps(dataset))
except Exception as e:
    logger.error(f"global exception: {str(e)}")

