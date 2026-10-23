import logging

from pystac import CatalogType, Item

from src.parser_interface import ParserInterface
from src.misc.bio_oracle.constants import Constants as BioOracleConstants
from src.misc.utils import Utils

logger = logging.getLogger(__name__)


class Parser(ParserInterface):
    def __init__(self, arguments):
        super().__init__(arguments)
        self.output_path = arguments.output_path

    def manage_arguments(self, arguments):
        pass

    def convert(self):
        extractor = self.get_extractor()
        dataset = self.query_dataset(uuid=BioOracleConstants.dataset_id)
        catalog = Utils.create_catalog(BioOracleConstants.catalog_id, BioOracleConstants.catalog_id)
        # collection properties
        # TODO
        collection_id = self.create_collection_id({})
        collection_title, collection_description = self.get_collection_title(dataset)
        collection_providers = self.get_providers(dataset)
        collection_license_name, license_url = self.get_collection_license(dataset)
        collection_license_link = Utils.create_link(rel="license",
                                                    href=license_url,
                                                    type="text/html",
                                                    title=collection_license_name)
        attributes = extractor.extract_attributes(dataset)
        collection_keywords = self.get_keywords(dataset=dataset, keywords=attributes)
        extra_fields = self.get_extra_fields(dataset)
        items = list()

        for attribute in attributes:
            # TODO
            item = self.create_item(wrapper={})
            properties = extra_fields.copy()
            properties["soilgrids:variable"] = attribute
            items.append(item)

        collection_extent = self.get_extents(dataset=dataset)

        collection = self.create_collection(collection_id=collection_id,
                                               title=collection_title,
                                               description=collection_description,
                                               extent=collection_extent,
                                               license=collection_license_name,
                                               keywords=collection_keywords,
                                               providers=collection_providers,
                                               extra_fields=extra_fields)

        # add bottom to top
        collection.add_items(items)
        collection.add_link(collection_license_link)
        catalog.add_child(collection)

        catalog.normalize_and_save(root_href=self.output_path, catalog_type=CatalogType.SELF_CONTAINED)

    def create_item(self, wrapper: dict) -> Item | None:
        pass

    def create_collection_id(self, wrapper: dict) -> str:
        return BioOracleConstants.catalog_id
