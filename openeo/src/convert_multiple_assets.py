import logging
import pystac
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
        self.date_time = datetime.fromisoformat(arguments.datetime)
        self.start_datetime = datetime.fromisoformat(arguments.start_datetime)
        self.end_datetime = datetime.fromisoformat(arguments.end_datetime)
        self.projection = arguments.projection
        self.input_path = arguments.input_path

    def convert(self):
        top_catalog = Utils.create_catalog("top_catalog", description="at the top")
        top_collection = Utils.create_collection("top_collection", "below catalog", extent=None)
        inner_catalog = Utils.create_catalog("inner_catalog", "below collection")
        inner_collection = Utils.create_collection("inner_collection", "inner collection")

        items = list()
        proj_bounds, bbox, polygon = Soilgrids_Utils.extract_meta_data_from_raster("....", "EPSG:4326")
        item = Utils.create_simple_item("item", bbox=bbox, datetime=None, geometry=None, properties=None)
        items.append(item)

        inner_catalog.add_items(items)

        top_collection.add_child(inner_collection)
        # top_collection.add_child(inner_catalog)
        top_catalog.add_child(top_collection)

        top_catalog.normalize_and_save(root_href="toto", catalog_type=pystac.CatalogType.SELF_CONTAINED)
        items = self.create_from_directory(self.input_path)
        spatial_extent, temporal_extent = Utils.infer_extents_from(items)
        collection_extent = pystac.Extent(spatial=spatial_extent, temporal=temporal_extent)
        outer_collection = Utils.create_collection("outer_collection", )

        item = pystac.Item()
        assets = self.create_assets({})

        for asset in assets:
            item.add_asset(Soilgrids_Constants.asset_key, asset)

    def create_item_from_rasters(self, item_id, entries, projection):
        srcs = entries.map(lambda entry: entry[Soilgrids_Constants.src_key])
        geometry, bbox = self.extract_from_srcs(srcs, projection)
        item = Utils.create_simple_item(item_id=item_id, datetime=self.date_time, bbox=bbox, geometry=geometry, properties={})

        # assets must be added to item first
        assets = self.create_assets(entries)

        for asset in assets:
            item.add_asset(Soilgrids_Constants.asset_key, asset)

        # then add band
        # eo = EOExtension.ext(asset, add_if_missing=True)
        # eo.apply(Utils.create_bands([band_name]))

        item.validate()

        return item

    def create_assets(self, entries: list):
        logger.info(f"creating {str(len(entries))} assets")
        assets = list()

        for entry in entries:
            asset = Utils.create_asset(href=entry[Soilgrids_Constants.href_key],
                                       title=entry[Soilgrids_Constants.title_key],
                                       media_type=pystac.MediaType.GEOTIFF)
            assets.append(asset)

        return assets

    def extract_from_srcs(self, srcs, projection):
        logger.info("extracting from sources")
        geometries = []

        for src in srcs:
            left, bottom, right, top = rasterio.warp.transform_bounds(src.crs, projection, *src.bounds)
            geom = box(left, bottom, right, top)
            geometries.append(geom)

        merged_geom = unary_union(geometries)
        geometry = mapping(merged_geom)
        bbox = list(merged_geom.bounds)

        return geometry, bbox