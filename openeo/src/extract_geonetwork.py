import logging
import requests
from src.misc.soilgrids.constants import Constants as Soilgrids_Constants
from src.misc.utils import Utils

logger = logging.getLogger(__name__)


class SoilGrids:
    @staticmethod
    def query_dataset(uuid: str):
        logger.info(f"query dataset {uuid}")

        # Set up your server and the query URL:
        query_url = Soilgrids_Constants.geonetwork_base_url + Soilgrids_Constants.geonetwork_query_path + uuid
        logger.info(f"query url: {query_url}")

        # Send a get request to the endpoint
        response = requests.get(query_url)
        dataset = SoilGrids.check_response(response)

        return dataset

    @staticmethod
    def check_response(geonetwork_response):
        """checks elasticsearch response, looking for original object"""
        logger.info("parse geonetwork response")

        # check http code
        if geonetwork_response.status_code != 200:
            raise Exception("response is not 200")

        json = geonetwork_response.json()
        # verify content
        tmp = Utils.check_key(Soilgrids_Constants.hits_key, json)
        tmp = Utils.check_key(Soilgrids_Constants.hits_key, tmp)

        if len(tmp) != 1:
            raise Exception("incorrect number of hits")

        hit = tmp[0]
        result = Utils.check_key(Soilgrids_Constants.source_key, hit)
        SoilGrids.check_dataset(result)

        return result

    @staticmethod
    def check_dataset(dataset: dict):
        logger.info("check dataset content")

        project = Utils.check_key(Soilgrids_Constants.project_key, dataset)
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
        logger.info("parse data tables")
        attributes = Utils.check_key(Soilgrids_Constants.attribute_list_key, data_tables)
        variables = SoilGrids.extract_variable_names(attributes)

        return variables

    @staticmethod
    def extract_variable_names(attributes: dict):
        logger.info("extract variable names")
        variables = []

        for attribute in attributes:
            name = Utils.check_key(Soilgrids_Constants.attribute_name_key, attribute)
            variables.append(name)

        return variables

    @staticmethod
    def parse_methods(methods: dict):
        logger.info("parse methods")
        steps = Utils.check_key(Soilgrids_Constants.method_steps_key, methods)
        citations = SoilGrids.extract_citations(steps)

        return citations

    @staticmethod
    def extract_citations(method_steps: dict):
        logger.info("extract citations")
        citations = []

        for step in method_steps:
            citations.append(Utils.check_key(Soilgrids_Constants.citation_key, step))

        return citations
