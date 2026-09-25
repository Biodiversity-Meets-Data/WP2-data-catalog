import logging
import requests

from abc import ABC, abstractmethod

from pystac import Provider

from src.misc.geonetwork.extraction_elasticsearch import ExtractionElasticsearch
from src.misc.geonetwork.extraction_eml import ExtractionEML
from src.misc.soilgrids.utils import Utils as Soilgrids_Utils
from src.misc.soilgrids.constants import Constants as Soilgrids_Constants

logger = logging.getLogger(__name__)


class Extraction(ABC):
    """base class for geonetwork stuff"""

    @staticmethod
    def get_instance(query_type: str):
        if query_type == Soilgrids_Constants.elastic_value:
            return ExtractionElasticsearch()
        elif query_type == Soilgrids_Constants.eml_value:
            return ExtractionEML()
        else:
            raise Exception(f"incorrect type {query_type}")

    def check_http_response(self, geonetwork_response):
        """basic http check, convert to json"""
        logger.info("parse geonetwork http response")

        # check http code
        status_code = geonetwork_response.status_code
        if status_code != 200:
            raise Exception(f"response is not 200: {status_code}")

        json = geonetwork_response.json()

        return json

    def query_dataset(self, uuid: str, query_type: str) -> dict:
        """entry point, main query"""
        logger.info(f"query dataset {uuid}")

        # Set up your server and the query URL:
        query_url = Soilgrids_Utils.build_catalog_url(uuid=uuid, query_type=query_type)
        logger.info(f"query url: {query_url}")

        # Send a get request to the endpoint
        headers = {
            "Accept": "application/json"
        }
        response = requests.get(query_url, headers=headers, timeout=Soilgrids_Constants.timeout)
        dataset = self.check_response(response)

        return dataset

    @abstractmethod
    def check_response(self, geonetwork_response) -> dict:
        pass

    @abstractmethod
    def check_dataset(self, dataset: dict):
        pass

    @abstractmethod
    def extract_providers(self, dataset: dict) -> list[Provider]:
        pass

    @abstractmethod
    def extract_person(self, person: dict, roles: list | None = None) -> Provider:
        pass

    @abstractmethod
    def extract_citations(self, method_steps: dict) -> list[dict]:
        pass
