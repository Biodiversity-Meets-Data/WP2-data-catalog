import logging
import requests

from abc import ABCMeta, abstractmethod, ABC
from datetime import datetime

# from pystac import Catalog, Item, Collection, CatalogType

from src.misc.query_types import QueryTypes
from src.misc.geonetwork.utils import Utils as Geonetwork_Utils

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
        self.query_type = QueryTypes.EML

    @abstractmethod
    def manage_arguments(self, arguments): raise NotImplementedError

    def get_extractor(self):
        return Geonetwork_Utils.get_extraction_instance(self.query_type)

    def query_dataset(self, uuid: str) -> dict:
        # get geonetwork dataset
        dataset = self.get_extractor().query_dataset(uuid=uuid, query_type=self.query_type)

        return dataset

    # @abstractmethod
    # def create_items(self) -> list[Item]: raise NotImplementedError
    #
    # @abstractmethod
    # def create_collection(self) -> Collection: raise NotImplementedError
    #
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
