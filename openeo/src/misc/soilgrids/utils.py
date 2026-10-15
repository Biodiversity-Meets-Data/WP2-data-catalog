import logging
import os
import time
from pathlib import Path
from urllib.parse import urlparse

from pystac import RelType, Link, MediaType
import rasterio.warp
from rasterio import RasterioIOError
from shapely.geometry import Polygon, box, mapping
from shapely.ops import unary_union
from pystac.extensions.eo import EOExtension
from pystac.extensions.raster import RasterExtension

from src.misc.soilgrids.constants import Constants as Soilgrids_Constants
from src.misc.geonetwork.utils import Utils as Geonetwork_Utils
from src.misc.utils import Utils as Global_Utils
from src.misc.constants import Constants
from src.misc.query_types import QueryTypes

logger = logging.getLogger(__name__)


class Utils:
    """shared code, specific to soilgrids"""
    @staticmethod
    def extract_band_from_name(file_name: str, known_bands: list):
        """some file name management to extract band name"""
        tokens = file_name.split(Soilgrids_Constants.token_separator)
        nbr_tokens = len(tokens)

        if nbr_tokens != Soilgrids_Constants.max_nbr_tokens:
            raise Exception(f"incorrect number of tokens: {nbr_tokens}")

        band = tokens[1]

        if band not in known_bands:
            raise Exception(f"band {band}: is unknown")

        return band

    @staticmethod
    def generate_file_name(variable_name: str, band_name: str, resolution: str):
        return Soilgrids_Constants.token_separator.join([variable_name, band_name, "mean", resolution])

    @staticmethod
    def generate_file_names():
        file_names = Utils.generate_file_names_for(Soilgrids_Constants.VARIABLE_NAMES, Soilgrids_Constants.band_names, Soilgrids_Constants.RESOLUTIONS)

        return file_names

    @staticmethod
    def generate_file_names_for(variable_names: list, band_names: list, resolutions: list):
        """failing to produce a valid file name will throw en exception at some point"""
        file_names = list()

        for variable_name in variable_names:
            for band_name in band_names:
                for resolution in resolutions:
                    file_name = Utils.generate_file_name(variable_name, band_name, resolution)
                    file_names.append(file_name + ".tif")

        return file_names

    @staticmethod
    def generate_urls(variable_names: list, band_names: list, resolutions: list):
        """failing to produce a valid url will throw en exception at some point"""
        urls = list()

        for resolution in resolutions:
            for variables_name in variable_names:
                for band_name in band_names:
                    urls.append(Utils.generate_url(variables_name, band_name, resolution))

        return urls

    @staticmethod
    def generate_url(variable_name: str, band_name: str, resolution: str):
        """builds an url based on available elements"""
        filename = Utils.generate_file_name(variable_name=variable_name, resolution=resolution, band_name=band_name)
        url = f"{Soilgrids_Constants.soilgrids_base_url}/{resolution}m/{variable_name}/{filename}.{Constants.TIF_EXTENSION}"

        return url

    @staticmethod
    def extract_meta_data_from_raster(src, projection):
        """reads raster and extract metadata"""
        proj_bounds = list(src.bounds)
        left, bottom, right, top = rasterio.warp.transform_bounds(src.crs, projection, *src.bounds)
        bbox = [left, bottom, right, top]
        polygon = mapping(Polygon([
            [left, bottom],
            [right, bottom],
            [right, top],
            [left, top],
            [left, bottom]
        ]))

        return proj_bounds, bbox, polygon

    @staticmethod
    def create_links(rel_type: RelType, action: QueryTypes) -> list[Link]:
        """absolute links, unlike internal relative links"""
        logger.info("extract links")
        links = list()
        # isric
        url = Soilgrids_Constants.isric_base_url
        link = Link(rel=rel_type, target=url, media_type=MediaType.HTML)
        links.append(link)
        # soilgrids
        url = Soilgrids_Constants.soilgrids_base_url
        link = Link(rel=rel_type, target=url, media_type=MediaType.HTML)
        links.append(link)
        # catalog
        url = Geonetwork_Utils.build_catalog_url(uuid=Soilgrids_Constants.soilgrids_dataset_uuid, query_type=action)
        link = Link(rel=rel_type, target=url, media_type=MediaType.HTML)
        links.append(link)

        return links

    @staticmethod
    def create_item_id(collection_id: str, variable_name: str):
        """create soilgrids item identifier"""
        return f"{collection_id}_item_{variable_name}"

    @staticmethod
    def create_collection_id(resolution: int):
        """create soilgrids collection identifier"""
        return f"soilgrids_collection_{resolution}m"

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
                    src_crs = src.crs
                    left, bottom, right, top = rasterio.warp.transform_bounds(src_crs, projection, *src.bounds)
                    geom = box(left, bottom, right, top)
                    geometries.append(geom)
                    # required otherwise most queries will fail due to rate limitation
                    time.sleep(2)
            except RasterioIOError:
                logger.error(f"CANNOT OPEN {url}")
                missing.append(url)

        merged_geom = unary_union(geometries)
        geometry = mapping(merged_geom)
        bbox = list(merged_geom.bounds)

        return geometry, bbox, missing

    @staticmethod
    def generate_entries(resolution: str, variable_names: list[str]):
        """generates a wrapper for later use, contains url and other metadata"""
        logger.info(f"generate entries for resolution {resolution}")
        entries = list()
        urls = Utils.generate_urls(variable_names, Soilgrids_Constants.band_names, [resolution])

        for url in urls:
            entries.append({
                Constants.href_key: url,
                Constants.title_key: Path(os.path.basename(urlparse(url).path)).stem,
                Constants.resolution_key: resolution
            })

        return entries

    @staticmethod
    def create_item_from_rasters(variable_name: str, item_id: str, entries: list, projection: str,
                                 attributes: dict, properties: dict, date_time, start_datetime, end_datetime):
        """
        - reads multiple urls (if they exist), each associated with a variable
        - create a single Item
        - create one Asset per url
        - associate Assets and Item
        """
        logger.info("create item from rasters")
        hrefs = map(lambda entry: entry[Constants.href_key], entries)
        geometry, bbox, missing_urls = Utils.extract_from_urls(hrefs, projection)

        if len(missing_urls) == len(entries):
            logger.warning(f"nothing to be done for {item_id}")
            return None
        else:
            item = Global_Utils.create_simple_item(item_id=item_id,
                                                   datetime=date_time,
                                                   start_datetime=start_datetime,
                                                   end_datetime=end_datetime,
                                                   bbox=bbox,
                                                   geometry=geometry,
                                                   properties=properties)

            # assets must be added to item first
            for entry in entries:
                url = entry[Constants.href_key]

                if url in missing_urls:
                    logger.warning(f"skipping {url}")
                else:
                    title = entry[Constants.title_key]
                    # filename = os.path.basename(urlparse(url).path)
                    band_name = Utils.extract_band_from_name(file_name=title,
                                                             known_bands=Soilgrids_Constants.band_names)
                    asset = Global_Utils.create_asset_from(entry)
                    item.add_asset(title, asset)

                    eo = EOExtension.ext(asset, add_if_missing=True)
                    eo.apply(bands=Global_Utils.create_bands([band_name]))

                    # reuse attribute data read from the datasource (catalog)
                    if variable_name in attributes:
                        logger.info("there are attributes to add")
                        raster_band = Global_Utils.create_raster_band(attributes[variable_name])
                        raster_ext = RasterExtension.ext(asset, add_if_missing=True)
                        raster_ext.apply(bands=[raster_band])

            item.validate()

        return item
