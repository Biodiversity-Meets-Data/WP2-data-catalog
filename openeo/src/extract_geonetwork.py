import logging
from src.misc.soilgrids.constants import Constants as Soilgrids_Constants
from src.misc.utils import Utils

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
    def parse_dataset(dataset: dict):
        logger.info("extract from response")

        creators = Utils.check_key(Soilgrids_Constants.creators_key, dataset)
        contacts = Utils.check_key(Soilgrids_Constants.contacts_key, dataset)
        datatables = Utils.check_key(Soilgrids_Constants.datatables_key, dataset)
        license_url = Utils.check_key(Soilgrids_Constants.license_url_key, dataset)
        license_name = Utils.check_key(Soilgrids_Constants.license_name_key, dataset)
        intellectual_rights = Utils.check_key(Soilgrids_Constants.intellectual_rights_key, dataset)
        methods = Utils.check_key(Soilgrids_Constants.methods_key, dataset)

        return True

    @staticmethod
    def parse_data_tables(data_tables: dict):
        logger.info("extract from data tables")

        variables = []
        attributes = Utils.check_key(Soilgrids_Constants.attribute_list_key, data_tables)

        for attribute in attributes:
            name = Utils.check_key(Soilgrids_Constants.attribute_name_key, attribute)
            variables.append(name)

        return variables

    @staticmethod
    def parse_methods(methods: dict):
        logger.info("extract from methods")

        steps = Utils.check_key(Soilgrids_Constants.method_steps_key, methods)

        for step in steps:
            citation = Utils.check_key(Soilgrids_Constants.citation_key, step)
