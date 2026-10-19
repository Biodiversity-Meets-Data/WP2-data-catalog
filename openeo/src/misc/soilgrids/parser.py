import logging
from datetime import datetime

from pystac import RelType, Extent, CatalogType, Item, Collection

from src.parser_interface import ParserInterface
from src.misc.constants import Constants
from src.misc.soilgrids.constants import Constants as SoilgridsConstants
from src.misc.soilgrids.utils import Utils as SoilgridsUtils
from src.misc.utils import Utils
from src.misc.query_types import QueryTypes

logger = logging.getLogger(__name__)


class Parser(ParserInterface):
    def __init__(self, arguments):
        super().__init__(arguments)
        self.projection = Constants.DEFAULT_PROJECTION
        self.output_path = arguments.output_path
        self.query_type = QueryTypes.EML

    def manage_arguments(self, arguments):
        pass

    def convert(self):
        """
        main function with the top-level steps:
        - Catalog/Collections/Items creation
        - associate Items and Collection, Collection and Catalog,
        - normalize and save
        """
        # TODO: add geometry
        extractor = super().get_extractor()
        soilgrids_dataset = super().query_dataset(uuid=SoilgridsConstants.soilgrids_dataset_uuid)

        # create top to bottom
        top_catalog = Utils.create_catalog("top_catalog", description="at the top")
        soilgrids_catalog = Utils.create_catalog(SoilgridsConstants.catalog_id, "below top")

        # resolutions = [Soilgrids_Constants.RESOLUTION_1000]
        resolutions = SoilgridsConstants.RESOLUTIONS
        # variable_names = [Soilgrids_Constants.BDOD_VALUE, Soilgrids_Constants.SAND_VALUE]
        variable_names = SoilgridsConstants.VARIABLE_NAMES
        attributes = extractor.extract_attributes(soilgrids_dataset)
        start_datetime, end_datetime, datetime = self.get_dates(soilgrids_dataset)

        for resolution in resolutions:
            items = list()
            # collection id
            collection_id = self.create_collection_id({Constants.resolution_key: resolution})
            extra_fields = super().get_extra_fields(soilgrids_dataset)

            for variable_name in variable_names:
                entries = SoilgridsUtils.generate_entries(resolution=resolution, variable_names=[variable_name])
                item_id = SoilgridsUtils.create_item_id(collection_id=collection_id, variable_name=variable_name)
                properties = extra_fields.copy()
                properties["soilgrids:variable"] = variable_name
                item = self.create_item({
                    Constants.properties_key: properties,
                    Constants.attributes_key: attributes,
                    Constants.entries_key: entries,
                    Constants.item_id_key: item_id,
                    Constants.variable_name_key: variable_name,
                    Constants.begin_date_key: start_datetime,
                    Constants.end_date_key: end_datetime,
                    Constants.datetime_key: datetime
                })

                if item is not None:
                    items.append(item)

            # collection level
            added_keywords = list(("soilgrids", "aggregated", resolution)) + variable_names
            collection_keywords = super().get_keywords(dataset=soilgrids_dataset, keywords=added_keywords)
            # license name and url
            collection_license_name, license_url = super().get_collection_license(soilgrids_dataset)
            collection_license_link = Utils.create_link(rel="license",
                                                        href=license_url,
                                                        type="text/html",
                                                        title=collection_license_name)
            # many providers
            collection_providers = super().get_providers(soilgrids_dataset)
            # wrapper for title and description
            collection_title_description = super().get_collection_title(soilgrids_dataset)
            # gather extents
            collection_extent = self.get_extent({Constants.items_key: items})

            soilgrids_collection = super().create_collection(collection_id=collection_id,
                                                           title=collection_title_description[0],
                                                           description=collection_title_description[1],
                                                           extent=collection_extent,
                                                           license=collection_license_name,
                                                           keywords=collection_keywords,
                                                           providers=collection_providers,
                                                           extra_fields=extra_fields)

            # absolute links
            links = SoilgridsUtils.create_links(rel_type=RelType.VIA, action=self.query_type)
            soilgrids_collection.add_links(links)

            # add bottom to top
            soilgrids_collection.add_items(items)
            soilgrids_collection.add_link(collection_license_link)
            soilgrids_catalog.add_child(soilgrids_collection)

        top_catalog.add_child(soilgrids_catalog)
        # top_catalog.describe()
        top_catalog.normalize_and_save(root_href=self.output_path, catalog_type=CatalogType.SELF_CONTAINED)

    def create_collection_id(self, wrapper: dict) -> str:
        resolution = Utils.check_key(Constants.resolution_key, wrapper)

        return SoilgridsUtils.create_collection_id(resolution)

    def create_item(self, wrapper: dict) -> Item | None:
        variable_name = Utils.check_key(Constants.variable_name_key, wrapper)
        item_id = Utils.check_key(Constants.item_id_key, wrapper)
        entries = Utils.check_key(Constants.entries_key, wrapper)
        attributes = Utils.check_key(Constants.attributes_key, wrapper)
        properties = Utils.check_key(Constants.properties_key, wrapper)
        start_datetime = datetime.fromisoformat(Utils.check_key(Constants.begin_date_key, wrapper))
        end_datetime = datetime.fromisoformat(Utils.check_key(Constants.end_date_key, wrapper))
        date_time = datetime.fromisoformat(Utils.check_key(Constants.datetime_key, wrapper))

        item = SoilgridsUtils.create_item_from_rasters(variable_name,
                                                       item_id=item_id,
                                                       entries=entries,
                                                       projection=self.projection,
                                                       attributes=attributes,
                                                       properties=properties,
                                                       date_time=date_time,
                                                       start_datetime=start_datetime,
                                                       end_datetime=end_datetime)

        if item is None:
            logger.warning(f"no item for {variable_name}")
        else:
            links = SoilgridsUtils.create_links(rel_type=RelType.VIA, action=self.query_type)
            item.add_links(links)

        return item

    def get_extent(self, wrapper: dict) -> Extent:
        items = Utils.check_key(Constants.items_key, wrapper)
        spatial_extent, temporal_extent = Utils.infer_extents_from(items)

        return Extent(spatial=spatial_extent, temporal=temporal_extent)
