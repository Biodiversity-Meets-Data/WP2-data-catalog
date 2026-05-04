import os
import logging
from urllib.parse import urlparse
import pystac
from pystac.extensions.eo import EOExtension
from datetime import datetime
import rasterio
import rasterio.warp
from shapely.geometry import box, mapping
from shapely.ops import unary_union
from src.misc.soilgrids.constants import Constants as Soilgrids_Constants
from src.misc.soilgrids.utils import Utils as Soilgrids_Utils
from src.misc.utils import Utils
from src.stac_interface import STACInterface

logger = logging.getLogger(__name__)


class ConvertMultipleAssets(STACInterface):
    def __init__(self, arguments):
        super().__init__(arguments)
        self.date_time = datetime.fromisoformat(arguments.datetime)
        self.start_datetime = datetime.fromisoformat(arguments.start_datetime)
        self.end_datetime = datetime.fromisoformat(arguments.end_datetime)
        self.projection = Soilgrids_Constants.DEFAULT_PROJECTION
        self.output_path = arguments.output_path

    def convert(self):
        items = list()
        entries = ConvertMultipleAssets.generate_entries()
        item = self.create_item_from_rasters("item_with_multiple_assets", entries, self.projection)
        items.append(item)
        spatial_extent, temporal_extent = Utils.infer_extents_from(items)
        collection_extent = pystac.Extent(spatial=spatial_extent, temporal=temporal_extent)

        # create top to bottom
        top_catalog = Utils.create_catalog("top_catalog", description="at the top")
        soilgrids_catalog = Utils.create_catalog("soilgrids_catalog", "below top")
        soilgrids_collection = Utils.create_collection("soilgrids_collection", "below catalog",
                                                       extent=collection_extent, license="CC BY 4.0")

        # add bottom to top
        soilgrids_collection.add_items(items)
        soilgrids_catalog.add_child(soilgrids_collection)
        top_catalog.add_child(soilgrids_catalog)

        # top_catalog.describe()
        top_catalog.normalize_and_save(root_href=self.output_path, catalog_type=pystac.CatalogType.SELF_CONTAINED)

    def create_item_from_rasters(self, item_id: str, entries: list, projection: str):
        logger.info("create item from rasters")
        hrefs = map(lambda entry: entry[Soilgrids_Constants.href_key], entries)
        geometry, bbox = ConvertMultipleAssets.extract_from_urls(hrefs, projection)
        item = Utils.create_simple_item(item_id=item_id, datetime=self.date_time, start_datetime=self.start_datetime,
                                        end_datetime=self.end_datetime, bbox=bbox, geometry=geometry, properties={})

        # assets must be added to item first
        for entry in entries:
            url = entry[Soilgrids_Constants.href_key]
            filename = os.path.basename(urlparse(url).path)
            band_name = Soilgrids_Utils.extract_band_from_name(file_name=filename, known_bands=Soilgrids_Constants.band_names)
            asset = ConvertMultipleAssets.create_asset(entry)
            item.add_asset(filename, asset)
            eo = EOExtension.ext(asset, add_if_missing=True)
            eo.apply(bands=Utils.create_bands([band_name]))

        item.validate()

        return item

    @staticmethod
    def generate_entries():
        logger.info("generate entries")
        entries = list()
        urls = Soilgrids_Utils.generate_urls([Soilgrids_Constants.BDOD_VALUE], Soilgrids_Constants.band_names,
                                             [Soilgrids_Constants.RESOLUTION_1000])
        for url in urls:
            entries.append({
                Soilgrids_Constants.href_key: url,
                Soilgrids_Constants.title_key: url
            })

        return entries

    @staticmethod
    def create_asset(entry):
        asset = Utils.create_asset(href=entry[Soilgrids_Constants.href_key],
                                   title=entry[Soilgrids_Constants.title_key],
                                   media_type=pystac.MediaType.GEOTIFF)

        return asset

    @staticmethod
    def create_assets(entries: list):
        logger.info(f"creating {str(len(entries))} assets")
        assets = list()

        for entry in entries:
            asset = ConvertMultipleAssets.create_asset(entry)
            assets.append(asset)

        return assets

    @staticmethod
    def extract_from_urls(urls, projection):
        logger.info("extracting from sources")
        geometries = []

        for url in urls:
            with rasterio.open(url) as src:
                left, bottom, right, top = rasterio.warp.transform_bounds(src.crs, projection, *src.bounds)
                geom = box(left, bottom, right, top)
                geometries.append(geom)

        merged_geom = unary_union(geometries)
        geometry = mapping(merged_geom)
        bbox = list(merged_geom.bounds)

        return geometry, bbox
