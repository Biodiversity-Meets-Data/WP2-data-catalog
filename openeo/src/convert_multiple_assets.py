import os
import logging
from urllib.parse import urlparse
from pathlib import Path
import pystac
from datetime import datetime
from pystac.extensions.eo import EOExtension
import rasterio
import rasterio.warp
from rasterio import RasterioIOError
from shapely.geometry import box, mapping
from shapely.ops import unary_union
from src.misc.soilgrids.constants import Constants as Soilgrids_Constants
from src.misc.soilgrids.utils import Utils as Soilgrids_Utils
from src.misc.utils import Utils
from src.stac_interface import STACInterface

logger = logging.getLogger(__name__)


class ConvertMultipleAssets(STACInterface):
    """the strategy is to group multiple Assets (soil depths) into a single Item (variable)"""
    def __init__(self, arguments):
        """keep command line arguments"""
        super().__init__(arguments)
        self.date_time = datetime.fromisoformat(arguments.datetime)
        self.start_datetime = datetime.fromisoformat(arguments.start_datetime)
        self.end_datetime = datetime.fromisoformat(arguments.end_datetime)
        self.projection = Soilgrids_Constants.DEFAULT_PROJECTION
        self.output_path = arguments.output_path

    def convert(self):
        """
        main function with the top-level steps:
        - Catalog/Collections/Items creation
        - associate Items and Collection, Collection and Catalog,
        - normalize and save
        """
        # create top to bottom
        top_catalog = Utils.create_catalog("top_catalog", description="at the top")
        soilgrids_catalog = Utils.create_catalog("soilgrids_catalog", "below top")

        # resolutions = [Soilgrids_Constants.RESOLUTION_1000]
        resolutions = Soilgrids_Constants.RESOLUTIONS
        # variable_names = [Soilgrids_Constants.BDOD_VALUE, Soilgrids_Constants.SAND_VALUE]
        variable_names = Soilgrids_Constants.VARIABLE_NAMES

        for resolution in resolutions:
            items = list()

            for variable_name in variable_names:
                entries = ConvertMultipleAssets.generate_entries(resolution=resolution, variable_names=[variable_name])
                item = self.create_item_from_rasters(f"item_{variable_name}_{resolution}m", entries, self.projection)

                if item is None:
                    logger.warning(f"no item for {variable_name}")
                else:
                    items.append(item)

            # gather extents
            spatial_extent, temporal_extent = Utils.infer_extents_from(items)
            collection_extent = pystac.Extent(spatial=spatial_extent, temporal=temporal_extent)

            # collection level
            collection_keywords = list(("soilgrids", "aggregated", resolution)) + variable_names
            collection_license="CC BY 4.0"

            soilgrids_collection = Utils.create_collection(f"soilgrids_collection_{resolution}m",
                                                           f"Soilgrids collection at resolution ({resolution}m)",
                                                           f"this a soilgrids collection at a specific resolution ({resolution}m)",
                                                           extent=collection_extent, license=collection_license,
                                                           keywords=collection_keywords)

            # add bottom to top
            soilgrids_collection.add_items(items)
            soilgrids_catalog.add_child(soilgrids_collection)

        top_catalog.add_child(soilgrids_catalog)
        # top_catalog.describe()
        top_catalog.normalize_and_save(root_href=self.output_path, catalog_type=pystac.CatalogType.SELF_CONTAINED)

    def create_item_from_rasters(self, item_id: str, entries: list, projection: str):
        """
        - reads multiple urls (if they exist), each associated with a variable
        - create a single Item
        - create one Asset per url
        - associate Assets and Item
        """
        logger.info("create item from rasters")
        hrefs = map(lambda entry: entry[Soilgrids_Constants.href_key], entries)
        geometry, bbox, missing_urls = ConvertMultipleAssets.extract_from_urls(hrefs, projection)

        if len(missing_urls) == len(entries):
            logger.warning(f"nothing to be done for {item_id}")
            return None
        else:
            item = Utils.create_simple_item(item_id=item_id, datetime=self.date_time, start_datetime=self.start_datetime,
                                            end_datetime=self.end_datetime, bbox=bbox, geometry=geometry, properties={})

            # assets must be added to item first
            for entry in entries:
                url = entry[Soilgrids_Constants.href_key]

                if url in missing_urls:
                    logger.warning(f"skipping {url}")
                else:
                    title = entry[Soilgrids_Constants.title_key]
                    # filename = os.path.basename(urlparse(url).path)
                    band_name = Soilgrids_Utils.extract_band_from_name(file_name=title,
                                                                       known_bands=Soilgrids_Constants.band_names)
                    asset = ConvertMultipleAssets.create_asset(entry)
                    item.add_asset(title, asset)

                    eo = EOExtension.ext(asset, add_if_missing=True)
                    eo.apply(bands=Utils.create_bands([band_name]))

            item.validate()
            return item

    @staticmethod
    def generate_entries(resolution: str, variable_names: list[str]):
        """generates a wrapper for later use, contains url and other metadata"""
        logger.info(f"generate entries for resolution {resolution}")
        entries = list()
        urls = Soilgrids_Utils.generate_urls(variable_names, Soilgrids_Constants.band_names, [resolution])

        for url in urls:
            entries.append({
                Soilgrids_Constants.href_key: url,
                Soilgrids_Constants.title_key: Path(os.path.basename(urlparse(url).path)).stem,
                Soilgrids_Constants.resolution_key: resolution
            })

        return entries

    @staticmethod
    def create_asset(entry):
        """simple wrapper around Asset creation"""
        asset = Utils.create_asset(href=entry[Soilgrids_Constants.href_key],
                                   title=entry[Soilgrids_Constants.title_key],
                                   media_type=pystac.MediaType.GEOTIFF)

        return asset

    @staticmethod
    def create_assets(entries: list):
        """simple wrapper around multiple Assets creation"""
        logger.info(f"creating {str(len(entries))} assets")
        assets = list()

        for entry in entries:
            asset = ConvertMultipleAssets.create_asset(entry)
            assets.append(asset)

        return assets

    @staticmethod
    def extract_from_urls(urls, projection):
        """extract geometry and bbox from multiple urls, keeping track of unreachable urls"""
        logger.info("extracting from sources")
        geometries = []
        missing = []

        for url in urls:
            logger.info(f"extracting from {url}")
            try:
                with rasterio.open(url) as src:
                    left, bottom, right, top = rasterio.warp.transform_bounds(src.crs, projection, *src.bounds)
                    geom = box(left, bottom, right, top)
                    geometries.append(geom)
            except RasterioIOError:
                logger.error(f"CANNOT OPEN {url}")
                missing.append(url)

        merged_geom = unary_union(geometries)
        geometry = mapping(merged_geom)
        bbox = list(merged_geom.bounds)

        return geometry, bbox, missing
