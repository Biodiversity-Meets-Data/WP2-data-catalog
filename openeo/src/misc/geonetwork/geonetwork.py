import logging

import requests
from pystac import ProviderRole, Provider

from src.misc.soilgrids.constants import Constants as Soilgrids_Constants
from src.misc.soilgrids.utils import Utils as Soilgrids_Utils
from src.misc.utils import Utils

logger = logging.getLogger(__name__)


class Geonetwork:
    @staticmethod
    def query_dataset(uuid: str, query_type: str):
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

        if query_type == Soilgrids_Constants.elastic_value:
            dataset = Geonetwork.check_elasticsearch_response(response)
        elif query_type == Soilgrids_Constants.eml_value:
            dataset = Geonetwork.check_response(response)
        else:
            raise Exception(f"incorrect query type {query_type}")

        return dataset

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

    @staticmethod
    def check_response(geonetwork_response):
        """check response, contains the original dataset"""
        logger.info("parse geonetwork response")

        json = Geonetwork.check_http_response(geonetwork_response=geonetwork_response)
        result = Utils.check_key(Soilgrids_Constants.dataset_key, json)
        Geonetwork.check_eml_dataset_content(result)

        return result

    @staticmethod
    def check_elasticsearch_response(geonetwork_response):
        """checks elasticsearch response, contains the original dataset"""
        logger.info("parse geonetwork elasticsearch response")

        json = Geonetwork.check_http_response(geonetwork_response=geonetwork_response)
        # verify content
        tmp = Utils.check_key(Soilgrids_Constants.hits_key, json)
        tmp = Utils.check_key(Soilgrids_Constants.hits_key, tmp)

        if len(tmp) != 1:
            raise Exception("incorrect number of hits")

        hit = tmp[0]
        result = Utils.check_key(Soilgrids_Constants.source_key, hit)
        Geonetwork.check_elasticsearch_dataset_content(result)

        return result

    @staticmethod
    def check_eml_dataset_content(dataset: dict):
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

    @staticmethod
    def check_elasticsearch_dataset_content(dataset: dict):
        """check for presence of important keys"""
        logger.info("check elasticsearch dataset content")
        project = Utils.check_key(Soilgrids_Constants.project_key, dataset)
        creators = Utils.check_key(Soilgrids_Constants.creators_key, dataset)
        contacts = Utils.check_key(Soilgrids_Constants.contacts_key, dataset)
        metadata_provider = Utils.check_key(Soilgrids_Constants.metadata_provider_key, dataset)
        datatables = Utils.check_key(Soilgrids_Constants.datatables_key, dataset)
        license_url = Utils.check_key(Soilgrids_Constants.license_url_key, dataset)
        license_name = Utils.check_key(Soilgrids_Constants.license_name_key, dataset)
        intellectual_rights = Utils.check_key(Soilgrids_Constants.intellectual_rights_key, dataset)
        methods = Utils.check_key(Soilgrids_Constants.methods_key, dataset)
        keywords_kpi = Utils.check_key(Soilgrids_Constants.keywords_kpi, dataset)

    @staticmethod
    def parse_data_tables(data_tables: dict):
        logger.info("parse data tables")
        attributes = Utils.check_key(Soilgrids_Constants.attribute_list_key, data_tables)
        variables = Geonetwork.extract_variable_names(attributes)

        return variables

    @staticmethod
    def extract_variable_names(attributes: dict):
        logger.info("extract variable names")
        """to be compared with the hardcoded attributes"""
        variables = []

        for attribute in attributes:
            name = Utils.check_key(Soilgrids_Constants.attribute_name_key, attribute)
            variables.append(name)

        diff = set(variables).symmetric_difference(Soilgrids_Constants.VARIABLE_NAMES)

        if len(diff) != 0:
            raise Exception(f"comparing available attributes failed: %s", diff)

        return variables

    @staticmethod
    def parse_methods(methods: dict):
        logger.info("parse methods")
        steps = Utils.check_key(Soilgrids_Constants.method_steps_key, methods)
        citations = Geonetwork.extract_citations(steps)

        return citations

    @staticmethod
    def extract_citations(method_steps: dict) -> list[dict]:
        """should only contain a single citation"""
        logger.info("extract citations")
        citations = []

        for step in method_steps:
            citations.append(Utils.check_key(Soilgrids_Constants.citation_key, step))

        if len(citations) != 1:
            raise Exception("incorrect number of citations")

        return citations

    @staticmethod
    def extract_providers(dataset: dict) -> list[Provider]:
        """data provider, multiple sources/status"""
        logger.info("extract providers")
        providers = list()
        creators = Utils.check_key(Soilgrids_Constants.creators_key, dataset)
        contacts = Utils.check_key(Soilgrids_Constants.contacts_key, dataset)
        metadata_providers = Utils.check_key(Soilgrids_Constants.metadata_provider_key, dataset)

        # people as producer ?
        creator_roles = [ProviderRole.PRODUCER]
        for creator in creators:
            provider = Geonetwork.extract_person(creator, creator_roles)
            providers.append(provider)

        # soilgrids as producer, licensor, host (currently)
        contact_roles = [ProviderRole.PRODUCER,
                         ProviderRole.LICENSOR,
                         ProviderRole.HOST]
        for contact in contacts:
            provider_name = contact[Soilgrids_Constants.organization_name]
            provider_email = contact[Soilgrids_Constants.electronic_email_address]
            provider = Utils.create_provider(name=provider_name, roles=contact_roles, email=provider_email)
            providers.append(provider)

        # BMD as processor, host
        bmd_roles = [ProviderRole.PROCESSOR,
                     ProviderRole.HOST]
        bmd_provider = Utils.create_provider(name=Soilgrids_Constants.BMD_PROJECT,
                                             roles=bmd_roles,
                                             url=Soilgrids_Constants.BMD_DOI)
        providers.append(bmd_provider)

        # LWE catalog
        lwe_roles = [ProviderRole.PROCESSOR,
                     ProviderRole.HOST]
        provider = Utils.create_provider(name=Soilgrids_Constants.geonetwork_name,
                                         roles=lwe_roles,
                                         url=Soilgrids_Constants.geonetwork_base_url)
        providers.append(provider)

        # chiara
        metadata_roles = [ProviderRole.PROCESSOR]
        for metadata_provider in metadata_providers:
            provider = Geonetwork.extract_person(metadata_provider, roles=metadata_roles)
            providers.append(provider)

        # SIB
        provider = Utils.create_provider(name=Soilgrids_Constants.SIB_NAME,
                                         roles=metadata_roles,
                                         url=Soilgrids_Constants.SIB_URL)
        providers.append(provider)

        return providers

    @staticmethod
    def extract_person(person: dict, roles: list | None = None) -> Provider:
        """helper method"""
        logger.info("extract from person")
        provider_name = person[Soilgrids_Constants.individual_name_surname] + " " + person[Soilgrids_Constants.individual_name_given_name]
        provider_email = person[Soilgrids_Constants.electronic_email_address]
        provider_url = person[Soilgrids_Constants.user_id]
        provider = Utils.create_provider(name=provider_name,
                                         roles=roles,
                                         email=provider_email,
                                         url=provider_url)

        return provider
