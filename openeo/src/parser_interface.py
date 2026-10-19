import logging
from typing import Any

import requests

from abc import ABCMeta, abstractmethod, ABC
from datetime import datetime

from pystac import Collection, Item, Extent, Provider

from src.misc.constants import Constants
from src.misc.query_types import QueryTypes
from src.misc.geonetwork.utils import Utils as GeonetworkUtils
from src.misc.utils import Utils

logger = logging.getLogger(__name__)


class ParserInterface(ABC):
    """
    - behavior shared by subclasses: manage commandline arguments -> log -> convert
    - one child class per datasource
    """
    __metaclass__ = ABCMeta

    def __init__(self, args):
        # check with some logic ?
        self.manage_arguments(args)
        self.output_path = args.output_path
        # only EML, elasticsearch support removed
        self.query_type = QueryTypes.EML

    @abstractmethod
    def manage_arguments(self, arguments): raise NotImplementedError

    def get_extractor(self):
        return GeonetworkUtils.get_extraction_instance(self.query_type)

    def query_dataset(self, uuid: str) -> dict:
        # get geonetwork dataset
        dataset = self.get_extractor().query_dataset(uuid=uuid, query_type=self.query_type)

        return dataset

    @abstractmethod
    def create_item(self, wrapper: dict) -> Item | None: raise NotImplementedError

    @abstractmethod
    def create_collection_id(self, wrapper: dict) -> str: raise NotImplementedError

    def get_collection_title(self, dataset) -> list[str]:
        project = Utils.check_key(Constants.project_key, dataset)

        return self.get_extractor().extract_title_description(project=project)

    def get_collection_license(self, dataset) -> list[str]:
        return self.get_extractor().extract_license(dataset=dataset)

    def get_keywords(self, dataset, keywords: list[str]) -> list[str]:
        extracted_keywords = self.get_extractor().extract_keywords(dataset=dataset)
        # make it unique with set()
        collection_keywords = list(set(extracted_keywords + keywords))

        return collection_keywords

    def get_providers(self, dataset) -> list[Provider]:
        return self.get_extractor().extract_providers(dataset=dataset)

    def get_extra_fields(self, dataset):
        methods = Utils.check_key(Constants.methods_key, dataset)
        first_citation = self.get_extractor().extract_citation(methods=methods[0])
        doi = self.get_extractor().extract_doi(citation=first_citation)
        # extra fields
        return {
            "sci:citation": first_citation,
            "sci:doi": doi,
            "proj:code": Constants.HOMOLOSINE_CODE
        }

    def get_extent(self, wrapper) -> Extent: raise NotImplementedError

    def create_collection(self,
                          collection_id: str,
                          title: str,
                          description: str,
                          extent: Extent,
                          license: str,
                          keywords: list[str] | None = None,
                          providers: list[Provider] | None = None,
                          extra_fields: dict[str, Any] | None = None) -> Collection:
        return Utils.create_collection(collection_id=collection_id,
                                       title=title,
                                       description=description,
                                       extent=extent,
                                       license=license,
                                       keywords=keywords,
                                       providers=providers,
                                       extra_fields=extra_fields)

    # @abstractmethod
    # def create_catalog(self) -> Catalog: raise NotImplementedError
    #
    # def steps(self):
    #     """putative implementation"""
    #     dataset = self.query_dataset()
    #     catalog = self.create_catalog()
    #     collection = self.create_collection()
    #     items = self.create_items()
    #
    #     collection.add_items(items)
    #     catalog.add_child(collection)
    #     catalog.normalize_and_save(root_href=self.output_path, catalog_type=CatalogType.SELF_CONTAINED)

    @abstractmethod
    def convert(self): raise NotImplementedError

    def run(self):
        logger.info("start")
        start = datetime.now()
        self.convert()
        end = datetime.now()
        elapsed = end - start
        logger.info(f"end in {elapsed}")
