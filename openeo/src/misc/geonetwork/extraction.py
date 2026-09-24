import logging

logger = logging.getLogger(__name__)


class Extraction:
    """base class for geonetwork stuff"""

    def __init__(self):
        pass

    @staticmethod
    def check_http_response(geonetwork_response):
        """basic http check, convert to json"""
        logger.info("parse geonetwork http response")

        # check http code
        status_code = geonetwork_response.status_code
        if status_code != 200:
            raise Exception(f"response is not 200: {status_code}")

        json = geonetwork_response.json()

        return json

    def check_dataset_content(self):
        pass
