# soilgrids has an uuid of 8315df49-bde3-4138-8f71-9b722f3afd06
import argparse
import logging
import requests
import json

# setup logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_response(geonetwork_response):
    logger.info("parse geonetwork response")

    if geonetwork_response.status_code is not 200:
        raise Exception("response is not 200")

    json = geonetwork_response.json()
    hits_key = "hits"

    if hits_key not in json:
        raise Exception("missing key in response")

    if hits_key not in json[hits_key]:
        raise Exception("missing internal key in response")

    if len(json[hits_key][hits_key]) != 1:
        raise Exception("incorrect number of hits")

    return json[hits_key][hits_key][0]


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
    hit = parse_response(response)
    print(json.dumps(hit))
except Exception as e:
    logger.error(f"global exception: {str(e)}")
