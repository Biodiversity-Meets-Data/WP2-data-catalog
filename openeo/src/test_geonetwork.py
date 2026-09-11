# soilgrids has an uuid of 8315df49-bde3-4138-8f71-9b722f3afd06
import argparse
import logging
import requests
import json
from src.misc.soilgrids.constants import Constants as Soilgrids_Constants
from src.misc.utils import Utils

# setup logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SoilGrids:
    @staticmethod
    def check_response(geonetwork_response):
        """checks elasticsearch response"""
        logger.info("parse geonetwork response")

        if geonetwork_response.status_code != 200:
            raise Exception("response is not 200")

        json = geonetwork_response.json()
        tmp = Utils.check_key(Soilgrids_Constants.hits_key, json)
        tmp = Utils.check_key(Soilgrids_Constants.hits_key, tmp)

        if len(tmp) != 1:
            raise Exception("incorrect number of hits")

        hit = tmp[0]
        result = Utils.check_key(Soilgrids_Constants.source_key, hit)

        return result

    @staticmethod
    def parse_dataset(dataset: json):
        logger.info("extract from response")

        creators = Utils.check_key(Soilgrids_Constants.creators_key, dataset)
        contacts = Utils.check_key(Soilgrids_Constants.contacts_key, dataset)
        datatables = Utils.check_key(Soilgrids_Constants.datatables_key, dataset)
        license_url = Utils.check_key(Soilgrids_Constants.license_url_key, dataset)
        license_name = Utils.check_key(Soilgrids_Constants.license_name_key, dataset)
        intellectual_rights = Utils.check_key(Soilgrids_Constants.intellectual_rights_key, dataset)

        return True


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

