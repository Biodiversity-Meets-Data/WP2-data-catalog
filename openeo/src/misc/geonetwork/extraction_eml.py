import logging

from pystac import Provider

from src.misc.utils import Utils
from src.misc.geonetwork.extraction import Extraction
from src.misc.soilgrids.constants import Constants as Soilgrids_Constants

logger = logging.getLogger(__name__)


class ExtractionEML(Extraction):
    def check_response(self, geonetwork_response: dict) -> dict:
        """check response, contains the original dataset"""
        logger.info("parse geonetwork response")

        json = super().check_http_response(geonetwork_response=geonetwork_response)
        result = Utils.check_key(Soilgrids_Constants.dataset_key, json)
        self.check_dataset(result)

        return result

    def check_dataset(self, dataset: dict):
        """check for presence of important keys"""
        logger.info("check dataset content (eml format)")
        project = Utils.check_key(Soilgrids_Constants.project_key, dataset)
        # singular in dataset
        creators = Utils.check_key(Soilgrids_Constants.creator_key, dataset)
        # singular in dataset
        contacts = Utils.check_key(Soilgrids_Constants.contact_key, dataset)
        metadata_provider = Utils.check_key(Soilgrids_Constants.metadata_provider_key, dataset)
        methods = Utils.check_key(Soilgrids_Constants.methods_key, dataset)
        keyword_set = Utils.check_key(Soilgrids_Constants.keyword_set, dataset)

    def extract_providers(self, dataset: dict) -> list[Provider]:
        raise Exception("unimplemented")

    def extract_person(self, person: dict, roles: list | None = None) -> Provider:
        raise Exception("unimplemented")

    def extract_citations(self, method_steps: dict) -> list[dict]:
        raise Exception("unimplemented")
