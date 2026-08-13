# see https://docs.geonetwork-opensource.org/4.2/api/the-geonetwork-api/#connecting-to-the-api-with-python
import argparse
import logging
import requests

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# parser for arguments
parser = argparse.ArgumentParser(
    prog='geonetwork query',
    description='extract relevant data from a geonetwork catalogue')
# setup arguments
parser.add_argument('-d', '--dataset', required=True, help="uuid for dataset")
parser.add_argument('-p', '--password', required=True, help="password for geonetwork catalogue")
parser.add_argument('-u', '--username', required=True, help="username for geonetwork catalogue")
# parse
args = parser.parse_args()
username = args.username
password = args.password

# Set up your server and the authentication URL:
server = "https://metadatacatalogue.lifewatch.dev"
authenticate_url = server + "/srv/api/me"
# authenticate_url = server + "/srv/eng/info?type=me"
logger.info(f"query url: {authenticate_url}")

# To generate the XRSF token, send a post request to the following URL: <server><authenticate_url>
session = requests.Session()
response = session.get(authenticate_url, auth=(username, password))
# response = session.post(authenticate_url)

response.raise_for_status()
xsrf_token = session.cookies.get("XSRF-TOKEN")

# Extract XRSF token
# xsrf_token = response.cookies.get("XSRF-TOKEN")
if xsrf_token:
    logger.info(f"The XSRF Token is: {xsrf_token}")
else:
    logger.info("Unable to find the XSRF token")

# Set header for connection
headers = {
    'Accept': 'application/json',
    'X-XSRF-TOKEN': xsrf_token
}

query_url = server + f"/srv/api/records/{args.dataset}/formatters/json"

# Send a put request to the endpoint
response = session.get(query_url,
                       auth=(username, password),
                       headers=headers)

logger.info(response)
