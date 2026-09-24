# soilgrids has an uuid of 8315df49-bde3-4138-8f71-9b722f3afd06
import argparse
import logging
import requests
import json
from src.misc.geonetwork.geonetwork import Geonetwork
from src.misc.soilgrids.constants import Constants as Soilgrids_Constants
from src.misc.soilgrids.utils import Utils as Soilgrids_Utils

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
query_url = Soilgrids_Utils.build_catalog_url(uuid=args.uuid, query_type=Soilgrids_Constants.elastic_value)
logger.info(f"query url: {query_url}")

# Send a put request to the endpoint
response = requests.get(query_url, timeout=Soilgrids_Constants.timeout)

try:
    Geonetwork.query_dataset(uuid=args.uuid, query_type=Soilgrids_Constants.elastic_value)
    dataset = Geonetwork.check_elasticsearch_response(response)
    print(json.dumps(dataset))
except Exception as e:
    logger.exception(f"global exception: {str(e)}")

