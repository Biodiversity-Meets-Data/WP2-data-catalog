import logging

from pystac import Provider, ProviderRole

from src.misc.utils import Utils
from src.misc.geonetwork.extraction import Extraction
from src.misc.soilgrids.constants import Constants as Soilgrids_Constants

logger = logging.getLogger(__name__)


class ExtractionElasticsearch(Extraction):
    def check_response(self, geonetwork_response: dict) -> dict:
        """checks elasticsearch response, contains the original dataset"""
        logger.info("parse geonetwork elasticsearch response")

        json = super().check_http_response(geonetwork_response=geonetwork_response)
        # verify content
        tmp = Utils.check_key(Soilgrids_Constants.hits_key, json)
        tmp = Utils.check_key(Soilgrids_Constants.hits_key, tmp)

        if len(tmp) != 1:
            raise Exception("incorrect number of hits")

        hit = tmp[0]
        result = Utils.check_key(Soilgrids_Constants.source_key, hit)
        self.check_dataset(result)

        return result

    def check_dataset(self, dataset: dict):
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

    def extract_providers(self, dataset: dict) -> list[Provider]:
        """data provider, multiple sources/status"""
        logger.info("extract providers")
        providers = list()
        creators = Utils.check_key(Soilgrids_Constants.creators_key, dataset)
        contacts = Utils.check_key(Soilgrids_Constants.contacts_key, dataset)
        metadata_providers = Utils.check_key(Soilgrids_Constants.metadata_provider_key, dataset)

        # people as producer ?
        creator_roles = [ProviderRole.PRODUCER]
        for creator in creators:
            provider = self.extract_person(creator, creator_roles)
            providers.append(provider)

        # soilgrids as producer, licensor, host (currently)
        contact_roles = [ProviderRole.PRODUCER,
                         ProviderRole.LICENSOR,
                         ProviderRole.HOST]
        for contact in contacts:
            provider = self.extract_person(contact, contact_roles)
            providers.append(provider)

        # BMD as processor, host
        bmd_provider = super().generate_bmd_provider()
        providers.append(bmd_provider)

        # LWE catalog
        provider = super().generate_lwe_provider()
        providers.append(provider)

        # chiara
        metadata_roles = [ProviderRole.PROCESSOR]
        tmp = super().generate_metadata_providers(metadata_providers)
        providers.extend(tmp)

        # SIB
        provider = Utils.create_provider(name=Soilgrids_Constants.SIB_NAME,
                                         roles=metadata_roles,
                                         url=Soilgrids_Constants.SIB_URL)
        providers.append(provider)

        return providers

    def extract_person(self, person: dict, roles: list | None = None) -> Provider:
        """helper method"""
        logger.info("extract from person")
        provider_name = super().build_name(person[Soilgrids_Constants.individual_name_surname_key],
                                           person[Soilgrids_Constants.individual_name_given_name_key])
        provider_email = person[Soilgrids_Constants.electronic_email_address_key]
        provider_url = person[Soilgrids_Constants.user_id_key]
        provider = Utils.create_provider(name=provider_name,
                                         roles=roles,
                                         email=provider_email,
                                         url=provider_url)

        return provider

    def extract_citation(self, methods: dict) -> str:
        """should only contain a single citation"""
        logger.info("extract citations")
        method_steps = Utils.check_key(Soilgrids_Constants.method_steps_key, methods)
        citations = []

        for step in method_steps:
            citations.append(Utils.check_key(Soilgrids_Constants.citation_key, step))

        if len(citations) != 1:
            raise Exception("incorrect number of citations")

        return citations[0]

    def parse_data_tables(self, data_tables: dict):
        logger.info("parse data tables")
        attributes = Utils.check_key(Soilgrids_Constants.attribute_list_key, data_tables)
        variables = self.extract_attributes(attributes)

        return variables

    def extract_keywords(self, dataset: dict) -> list[str]:
        logger.info("extract keywords")
        keywords_kpi = Utils.check_key(Soilgrids_Constants.keywords_kpi, dataset)

        return keywords_kpi

    def extract_attributes(self, dataset: list) -> dict:
        logger.info("extract attributes")
        datatables = Utils.check_key(Soilgrids_Constants.datatables_key, dataset)
        attributes = Utils.check_key(Soilgrids_Constants.attribute_list_key, datatables[0])
        """to be compared with the hardcoded attributes ?"""
        result = {}

        for attribute in attributes:
            name = Utils.check_key(Soilgrids_Constants.attribute_name_key, attribute)
            # unit = Utils.check_key(Soilgrids_Constants.attribute_standard_unit_key, attribute)
            # description = Utils.check_key(Soilgrids_Constants.description_key, attribute)

            if name in result:
                raise Exception(f"attribute {name} already exists")

            result[name] = attribute

        return result

    def extract_title_description(self, project: dict) -> list[str]:
        logger.info("extract title and description")
        collection_title = Utils.check_key(Soilgrids_Constants.title_key, project)
        collection_description = Utils.check_key(Soilgrids_Constants.abstract_key, project)

        return [collection_title, collection_description]

    def extract_license(self, dataset: dict):
        raise Exception("not implemented")
