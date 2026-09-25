import logging

from pystac import Provider, ProviderRole

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
        keyword_set = Utils.check_key(Soilgrids_Constants.keyword_set_key, dataset)

    def extract_providers(self, dataset: dict) -> list[Provider]:
        logger.info("extract providers")
        providers = list()
        # multiple entries
        creators = Utils.check_key(Soilgrids_Constants.creator_key, dataset)
        # single entry
        contact = Utils.check_key(Soilgrids_Constants.contact_key, dataset)
        # single entry
        metadata_provider = Utils.check_key(Soilgrids_Constants.metadata_provider_key, dataset)

        # creators
        creator_roles = [ProviderRole.PRODUCER]
        for creator in creators:
            provider = self.extract_person(creator, creator_roles)
            providers.append(provider)

        # soilgrids
        contact_roles = [ProviderRole.PRODUCER,
                         ProviderRole.LICENSOR,
                         ProviderRole.HOST]
        provider_name = contact[Soilgrids_Constants.organization_name_key]
        provider_email = contact[Soilgrids_Constants.electronic_email_address_key]
        provider = Utils.create_provider(name=provider_name, roles=contact_roles, email=provider_email)
        providers.append(provider)

        # BMD TODO

        # LWE catalog TODO

        # chiara

        # SIB

        # raise Exception("unimplemented")

        return providers

    def extract_person(self, person: dict, roles: list | None = None) -> Provider:
        """helper method"""
        logger.info("extract from person")
        name = Utils.check_key(Soilgrids_Constants.individual_name_key, person)
        provider_givenname = Utils.check_key(Soilgrids_Constants.given_name_key, name)
        provider_surname = Utils.check_key(Soilgrids_Constants.surname_key, name)
        provider_name = super().build_name(provider_surname, provider_givenname)
        provider_email = Utils.check_key(Soilgrids_Constants.electronic_email_address_key, person)
        provider_url = Utils.check_key(Soilgrids_Constants.user_id_key, person)
        provider = Utils.create_provider(name=provider_name,
                                         roles=roles,
                                         email=provider_email,
                                         url=provider_url)

        return provider

    def extract_citation(self, methods: dict) -> str:
        logger.info("extract citations")
        steps = Utils.check_key(key=Soilgrids_Constants.keyword_set_key, wrapper=methods)
        citation = Utils.check_key(key=Soilgrids_Constants.citation_key, wrapper=steps)

        return citation

    def extract_keywords(self, dataset: dict) -> list[str]:
        logger.info("extract keywords")
        keywords = list()
        keyword_set = Utils.check_key(key=Soilgrids_Constants.keyword_set_key, wrapper=dataset)

        for wrapper in keyword_set:
            keyword = Utils.check_key(key=Soilgrids_Constants.keyword_key, wrapper=wrapper)
            keywords.append(keyword)

        return keywords

    # def extract_description(self, dataset: dict) -> str:
    #     logger.info("extract description")
    #     abstract = Utils.check_key(Soilgrids_Constants.abstract_key, dataset)
    #
    #     return abstract
    #
    # def extract_title(self, dataset: dict) -> str:
    #     logger.info("extract title")
    #     Utils.check_key(Soilgrids_Constants)
    #     raise Exception("unimplemented")

    def extract_title_description(self, project: dict) -> list[str]:
        logger.info("extract title and description")
        collection_title = Utils.check_key(Soilgrids_Constants.title_key, project)
        collection_description = Utils.check_key(Soilgrids_Constants.abstract_key, project)[0]

        return [collection_title, collection_description]
