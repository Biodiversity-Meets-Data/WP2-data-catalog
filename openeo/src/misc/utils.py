import os
import json
import logging
import pystac
from pystac import Extent
from pystac.extensions.eo import Band
import shapely
from shapely.geometry import Polygon, mapping, shape
import rasterio

logger = logging.getLogger(__name__)


class Utils:
    @staticmethod
    def create_catalog(catalog_id: str, description: str):
        logger.info(f"creating catalog {catalog_id}")
        catalog = pystac.Catalog(id=catalog_id, description=description)

        return catalog

    @staticmethod
    def create_collection(collection_id: str, description: str, extent: Extent | None = None):
        logger.info(f"creating collection {collection_id}")
        collection = pystac.Collection(id=collection_id, description=description, extent=extent, license="toto")

        return collection

    @staticmethod
    def create_item(item_id: str, polygon, bbox, datetime, start_datetime, end_datetime, src, proj_bounds):
        logger.info(f"creating item {item_id}")
        item = pystac.Item(
            id=item_id,
            geometry=polygon,
            bbox=bbox,
            datetime=datetime,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
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

        return item

    @staticmethod
    def create_asset(href: str, title: str, media_type: str):
        logger.info(f"creating asset {href}")
        asset = pystac.Asset(
            href=href,
            title=title,
            media_type=media_type
        )

        return asset

    @staticmethod
    def create_bands(band_names):
        bands = list()

        for band_name in band_names:
            bands.append(Band.create(name=band_name))

        return bands

    @staticmethod
    def parse_bands(file_path):
        if not os.path.isfile(file_path):
            raise Exception(f"{file_path} is not a file")

        with open(file_path) as f:
            bands = json.load(f)

            return bands

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
