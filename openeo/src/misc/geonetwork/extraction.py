import logging
import requests

from abc import ABC, abstractmethod

from pystac import Provider, ProviderRole

from src.misc.soilgrids.utils import Utils as Soilgrids_Utils
from src.misc.soilgrids.constants import Constants as Soilgrids_Constants
from src.misc.utils import Utils

logger = logging.getLogger(__name__)


class Extraction(ABC):
    """base class for geonetwork stuff"""

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

    def build_name(self, surname: str, given_name: str):
        return surname + " " + given_name

    def generate_bmd_provider(self):
        bmd_roles = [ProviderRole.PROCESSOR,
                     ProviderRole.HOST]
        bmd_provider = Utils.create_provider(name=Soilgrids_Constants.BMD_PROJECT,
                                             roles=bmd_roles,
                                             url=Soilgrids_Constants.BMD_DOI)

        return bmd_provider

    def generate_lwe_provider(self):
        lwe_roles = [ProviderRole.PROCESSOR,
                     ProviderRole.HOST]
        provider = Utils.create_provider(name=Soilgrids_Constants.geonetwork_name,
                                         roles=lwe_roles,
                                         url=Soilgrids_Constants.geonetwork_base_url)

        return provider

    def generate_metadata_providers(self, metadata_providers: list):
        providers = list()
        metadata_roles = [ProviderRole.PROCESSOR]
        for metadata_provider in metadata_providers:
            provider = self.extract_person(metadata_provider, roles=metadata_roles)
            providers.append(provider)

        return providers

    @abstractmethod
    def check_response(self, geonetwork_response) -> dict:
        """basic check for a specific endpoint"""
        pass

    @abstractmethod
    def check_dataset(self, dataset: dict):
        """basic dataset check for required properties"""
        pass

    @abstractmethod
    def extract_providers(self, dataset: dict) -> list[Provider]:
        """get anybody involved"""
        pass

    @abstractmethod
    def extract_person(self, person: dict, roles: list | None = None) -> Provider:
        """name, surname, etc..."""
        pass

    @abstractmethod
    def extract_citation(self, methods: dict) -> str:
        """often a publication"""
        pass

    def extract_doi(self, citation) -> str:
        """should be in the citation"""
        pass

    def extract_keywords(self, dataset: dict) -> list[str]:
        """specific keywords found in the payload"""
        pass

    def extract_title_description(self, project: dict) -> str:
        """title and description are often found together"""
        pass

    def extract_license(self, dataset: dict) -> list[str]:
        pass

    def extract_attributes(self, dataset: dict) -> dict:
        """what was measured in this dataset"""
        pass

    def parse_attributes(self, attributes: list) -> dict:
        result = {}

        for attribute in attributes:
            name = Utils.check_key(Soilgrids_Constants.attribute_name_key, attribute)

            if name in result:
                raise Exception(f"attribute {name} already exists")

            result[name] = attribute

        return result
