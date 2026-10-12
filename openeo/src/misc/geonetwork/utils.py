import logging

from src.misc.geonetwork.constants import Constants as Geonetwork_Constants
from src.misc.query_types import QueryTypes

logger = logging.getLogger(__name__)


class Utils:
    @staticmethod
    def get_extraction_instance(query_type: QueryTypes):
        """get specific instance based on argument"""
        logging.info(f"get extraction instance for {query_type}")
        from src.misc.geonetwork.extraction_elasticsearch import ExtractionElasticsearch
        from src.misc.geonetwork.extraction_eml import ExtractionEML

        if query_type == QueryTypes.ELASTIC:
            return ExtractionElasticsearch()
        elif query_type == QueryTypes.EML:
            return ExtractionEML()
        else:
            raise Exception(f"incorrect type {query_type}")

    @staticmethod
    def build_catalog_url(uuid: str, query_type: QueryTypes):
        """builds url for geonetwork dataset, determined by its uuid"""
        if query_type == QueryTypes.ELASTIC:
            return Geonetwork_Constants.geonetwork_base_url + Geonetwork_Constants.geonetwork_query_path_old + uuid
        elif query_type == QueryTypes.EML:
            return Geonetwork_Constants.geonetwork_base_url + Geonetwork_Constants.geonetwork_query_path + uuid + Geonetwork_Constants.geonetwork_query_path_format
        else:
            raise Exception(f"unknown action {query_type}")
