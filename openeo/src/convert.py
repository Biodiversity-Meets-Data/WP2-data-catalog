import os
import glob
import json
import logging
from urllib.parse import urlparse
from datetime import datetime
import pystac
from pystac import Extent
from pystac.extensions.eo import Band, EOExtension
import rasterio
import rasterio.warp
import shapely
from shapely.geometry import Polygon, mapping, shape

logger = logging.getLogger(__name__)


class Convert:
    max_nbr_tokens = 4
    token_separator = "_"

    def __init__(self, arguments):
        self.bands_path = arguments.bands_path
        self.date_time = datetime.fromisoformat(arguments.datetime)
        self.start_datetime = datetime.fromisoformat(arguments.start_datetime)
        self.end_datetime = datetime.fromisoformat(arguments.end_datetime)
        self.projection = arguments.projection
        self.input_path = arguments.input_path
        self.output_path = arguments.output_path
        self.title = arguments.title
        self.known_bands = Convert.parse_bands(self.bands_path)

    def convert(self, urls):
        if self.input_path and os.path.isdir(self.input_path):
            items = self.create_from_directory(self.input_path)
        else:
            items = self.create_items_from_urls(urls)

        spatial_extent, temporal_extent = Convert.infer_extents_from(items)
        collection_extent = pystac.Extent(spatial=spatial_extent, temporal=temporal_extent)
        collection = Convert.create_collection("test_collection", "test collection", extent=collection_extent)
        collection.add_items(items)

        catalog = Convert.create_catalog("test_catalog", "test catalog")
        catalog.add_child(collection)
        #catalog.describe()
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

        for file in files:
            items.append(self.create_item_from_file(file))

        return items

    def create_item_from_file(self, file_path):
        logger.info(f"creating item for file {file_path}")

        if not os.path.isfile(file_path):
            raise Exception(f"{file_path} is not a file")

        with rasterio.open(file_path) as src:
            filename = os.path.basename(file_path)
            return self.create_item_from_raster(src=src, filename=filename, href=file_path, title=self.title)

    @staticmethod
    def create_catalog(catalog_id: str, description: str):
        logger.info(f"creating catalog {catalog_id}")
        catalog = pystac.Catalog(id=catalog_id, description=description)

        return catalog

    @staticmethod
    def create_collection(collection_id: str, description: str, extent: Extent):
        logger.info(f"creating collection {collection_id}")
        collection = pystac.Collection(id=collection_id, description=description, extent=extent)

        return collection

    def create_items_from_urls(self, urls):
        logger.info("creating items for " + str(len(urls)) + " urls")
        items = list()

        for url in urls:
            logger.debug(f"url {url}")
            item = self.create_item_from_url(url)
            items.append(item)

        return items

    @staticmethod
    def create_asset(href: str, title: str, band: str):
        logger.info(f"creating asset {href}")
        asset = pystac.Asset(
            href=href,
            title=title,
            extra_fields={
                "eo:bands": [  # REQUIRED: define the bands in the eo extension for openEO to be able to load it
                    {
                        "name": band,
                    }
                ],
            }
        )

        return asset

    @staticmethod
    def get_bbox_and_footprint(raster):
        with rasterio.open(raster) as r:
            bounds = r.bounds
            bbox = [bounds.left, bounds.bottom, bounds.right, bounds.top]
            footprint = Polygon([
                [bounds.left, bounds.bottom],
                [bounds.left, bounds.top],
                [bounds.right, bounds.top],
                [bounds.right, bounds.bottom],
                [bounds.left, bounds.bottom]
            ])

            return bbox, mapping(footprint)

    @staticmethod
    def infer_extents_from(items: list):
        logger.info("inferring extents for " + str(len(items)) + " items")
        geometries = list()
        datetimes = list()

        for item in items:
            geometries.append(shape(item.geometry))
            datetimes.append(item.common_metadata.start_datetime)
            datetimes.append(item.common_metadata.end_datetime)

        # spatial
        unioned_footprint = shapely.union_all(geometries)
        collection_bbox = list(unioned_footprint.bounds)
        spatial_extent = pystac.SpatialExtent(bboxes=[collection_bbox])
        # temporal
        sorted_datetimes = sorted(datetimes)
        first_datetime = sorted_datetimes[0]
        last_datetime = sorted_datetimes[len(datetimes) - 1]
        temporal_extent = pystac.TemporalExtent(intervals=[[first_datetime, last_datetime]])

        return spatial_extent, temporal_extent

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
        band_name = Convert.extract_band_from_name(file_name=filename, known_bands=self.known_bands)

        item = pystac.Item(
            id=filename,
            geometry=polygon,
            bbox=[left, bottom, right, top],
            datetime=self.date_time,
            start_datetime=self.start_datetime,
            end_datetime=self.end_datetime,
            properties={  # These properties are optional, but can speed up the loading of the data.
                "proj:epsg": src.crs.to_epsg(),
                "proj:shape": src.shape,  # Caveat: this is [height, width] and not [width, height] if you want to set them yourself
                "proj:bbox": proj_bounds,
            },
            stac_extensions=[
                "https://stac-extensions.github.io/eo/v1.1.0/schema.json",
                "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
            ]
        )

        asset = Convert.create_asset(href=href, title=title, band=band_name)
        item.add_asset("image", asset)
        item.validate()
        return item

    @staticmethod
    def create_bands(src):
        bands = list()

        for band in src:
            bands.append(Band.create(name=band))

        return bands

    @staticmethod
    def parse_bands(file_path):
        if not os.path.isfile(file_path):
            raise Exception(f"{file_path} is not a file")

        with open(file_path) as f:
            bands = json.load(f)

            return bands

    @staticmethod
    def extract_band_from_name(file_name: str, known_bands: list):
        tokens = file_name.split(Convert.token_separator)
        nbr_tokens = len(tokens)

        if nbr_tokens != Convert.max_nbr_tokens:
            raise Exception(f"incorrect number of tokens: {nbr_tokens}")

        band = tokens[1]

        if band not in known_bands:
            raise Exception(f"band {band}: is unknown")

        return band
