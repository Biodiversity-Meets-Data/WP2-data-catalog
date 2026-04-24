import os
import glob
import logging
from urllib.parse import urlparse
from datetime import datetime
import pystac
from pystac.extensions.eo import EOExtension
import rasterio
import rasterio.warp
from shapely.geometry import Polygon, mapping
from concurrent.futures import ProcessPoolExecutor
from src.misc.utils import Utils
from src.misc.soilgrids.utils import Utils as Soilgrids_Utils

logger = logging.getLogger(__name__)


class Convert:
    asset_key = "image"
    parallelize = False
    catalog_name = "Soilgrids_catalog"

    def __init__(self, arguments):
        self.bands_path = arguments.bands_path
        self.collection_id = arguments.collection_id
        self.date_time = datetime.fromisoformat(arguments.datetime)
        self.start_datetime = datetime.fromisoformat(arguments.start_datetime)
        self.end_datetime = datetime.fromisoformat(arguments.end_datetime)
        self.projection = arguments.projection
        self.input_path = arguments.input_path
        self.output_path = arguments.output_path
        self.title = arguments.title
        self.known_bands = Utils.parse_bands(self.bands_path)
        Convert.parallelize = arguments.multiprocess

    def convert(self, urls):
        if self.input_path and os.path.isdir(self.input_path):
            items = self.create_from_directory(self.input_path)
        else:
            items = self.create_items_from_urls(urls)

        spatial_extent, temporal_extent = Utils.infer_extents_from(items)
        collection_extent = pystac.Extent(spatial=spatial_extent, temporal=temporal_extent)
        collection = Utils.create_collection(self.collection_id, self.collection_id, extent=collection_extent)
        collection.add_items(items)

        catalog = Utils.create_catalog(self.catalog_name, self.catalog_name)
        catalog.add_child(collection)
        # catalog.describe()
        # catalog.normalize_and_save(root_href=os.path.join(tmp_dir.name, 'stac-collection'),
        #                            catalog_type=pystac.CatalogType.SELF_CONTAINED)
        catalog.normalize_and_save(root_href=self.output_path, catalog_type=pystac.CatalogType.SELF_CONTAINED)

    def create_from_directory(self, directory_path):
        logger.info(f"creating items for directory {directory_path}")
        items = list()

        if not os.path.isdir(directory_path):
            raise Exception(f"{directory_path} is not a directory")

        files = glob.glob(f"{directory_path}/*.tif")
        logger.info(f"found " + str(len(files)) + " files")

        if Convert.parallelize is True:
            logger.info("use parallelization")
            if __name__ == 'convert':
                items = self.parallel_execution(files)
        else:
            logger.info("no parallelization")
            for file in files:
                items.append(self.create_item_from_file(file))

        return items

    def parallel_execution(self, files: list):
        logger.info("parallel execution")
        with ProcessPoolExecutor() as executor:
            items = list(executor.map(self.create_item_from_file, files))

            return items

    def create_item_from_file(self, file_path):
        logger.info(f"creating item for file {file_path}")
        logger.info("currently running on " + str(os.getpid()))

        if not os.path.isfile(file_path):
            raise Exception(f"{file_path} is not a file")

        with rasterio.open(file_path) as src:
            filename = os.path.basename(file_path)
            return self.create_item_from_raster(src=src, filename=filename, href=file_path, title=self.title)

    def create_items_from_urls(self, urls):
        logger.info("creating items for " + str(len(urls)) + " urls")
        items = list()

        for url in urls:
            logger.debug(f"url {url}")
            item = self.create_item_from_url(url)
            items.append(item)

        return items

    def create_item_from_url(self, url):
        with rasterio.open(url) as src:
            filename = os.path.basename(urlparse(url).path)
            return self.create_item_from_raster(src=src, filename=filename, href=url, title=self.title)

    def create_item_from_raster(self, src, filename, href, title):
        proj_bounds = list(src.bounds)
        left, bottom, right, top = rasterio.warp.transform_bounds(src.crs, self.projection, *src.bounds)
        polygon = mapping(Polygon([
            [left, bottom],
            [right, bottom],
            [right, top],
            [left, top],
            [left, bottom]
        ]))
        band_name = Soilgrids_Utils.extract_band_from_name(file_name=filename, known_bands=self.known_bands)

        item = Utils.create_item(item_id=filename, polygon=polygon, bbox=[left, bottom, right, top],
                                 datetime=self.date_time, start_datetime=self.start_datetime,
                                 end_datetime=self.end_datetime, src=src, proj_bounds=proj_bounds)

        asset = Utils.create_asset(href=href, title=title, media_type=pystac.MediaType.GEOTIFF)
        # asset must be added to item first
        item.add_asset(Convert.asset_key, asset)
        # then add band
        eo = EOExtension.ext(asset, add_if_missing=True)
        eo.apply(Utils.create_bands([band_name]))
        item.validate()

        return item
