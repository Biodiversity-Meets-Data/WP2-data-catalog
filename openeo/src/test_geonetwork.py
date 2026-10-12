# soilgrids has an uuid of 8315df49-bde3-4138-8f71-9b722f3afd06
import argparse
import logging
import requests
import json

from src.misc.constants import Constants
from src.misc.query_types import QueryTypes
from src.misc.geonetwork.utils import Utils as Geonetwork_Utils

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
query_value = QueryTypes.ELASTIC
query_url = Geonetwork_Utils.build_catalog_url(uuid=args.uuid, query_type=query_value)
logger.info(f"query url: {query_url}")

# Send a put request to the endpoint
response = requests.get(query_url, timeout=Constants.NETWORK_TIMEOUT)

try:
    extractor = Geonetwork_Utils.get_extraction_instance(query_type=query_value)
    extractor.query_dataset(uuid=args.uuid, query_type=query_value)
    dataset = extractor.check_response(response)
    print(json.dumps(dataset))
except Exception as e:
    logger.exception(f"global exception: {str(e)}")
