import logging
from datetime import datetime

from pystac import CatalogType, Item

from src.parser_interface import ParserInterface
from src.misc.bio_oracle.constants import Constants as BioOracleConstants
from src.misc.utils import Utils
from src.misc.constants import Constants

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
        collection_id = self.create_collection_id({})
        collection_title, collection_description = self.get_collection_title(dataset)
        collection_providers = self.get_providers(dataset)
        collection_license_name, license_url = self.get_collection_license(dataset)
        collection_license_link = Utils.create_link(rel="license",
                                                    href=license_url,
                                                    type="text/html",
                                                    title=collection_license_name)
        attributes = extractor.extract_attributes(dataset)
        logger.info(attributes)
        collection_keywords = self.get_keywords(dataset=dataset, keywords=list(attributes.keys()))
        extra_fields = self.get_extra_fields(dataset=dataset, projection=Constants.WGS84_CODE)
        start_datetime, end_datetime, date_time = self.get_dates(dataset=dataset)
        bbox = self.get_bbox(dataset=dataset)
        geometry = self.get_geometry(dataset=dataset)
        items = list()

        for attribute in attributes:
            properties = extra_fields.copy()
            properties["soilgrids:variable"] = attribute
            item = self.create_item(wrapper={
                Constants.item_id_key: self.create_item_id({Constants.variable_name_key: attribute}),
                Constants.begin_date_key: datetime.fromisoformat(start_datetime),
                Constants.end_date_key: datetime.fromisoformat(end_datetime),
                Constants.datetime_key: datetime.fromisoformat(date_time),
                Constants.properties_key: properties,
                Constants.bbox_key: bbox,
                Constants.geometry_key: geometry
            })
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
        item_id = Utils.check_key(Constants.item_id_key, wrapper)
        date_time = Utils.check_key(Constants.datetime_key, wrapper)
        start_datetime = Utils.check_key(Constants.begin_date_key, wrapper)
        end_datetime = Utils.check_key(Constants.end_date_key, wrapper)
        bbox = Utils.check_key(Constants.bbox_key, wrapper)
        geometry = Utils.check_key(Constants.geometry_key, wrapper)
        properties = Utils.check_key(Constants.properties_key, wrapper)

        item = Utils.create_simple_item(item_id=item_id,
                                        date_time=date_time,
                                        start_datetime=start_datetime,
                                        end_datetime=end_datetime,
                                        bbox=bbox,
                                        geometry=geometry,
                                        properties=properties)

        return item

    def create_collection_id(self, wrapper: dict) -> str:
        return BioOracleConstants.collection_id

    def create_item_id(self, wrapper: dict) -> str:
        return Utils.check_key(Constants.variable_name_key, wrapper)
