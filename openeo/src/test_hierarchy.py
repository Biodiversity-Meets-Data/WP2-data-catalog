from misc.utils import Utils
import pystac
from src.misc.soilgrids.utils import Utils as Soilgrids_Utils
from src.misc.soilgrids.constants import Constants as Soilgrids_Constants

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

class Convert:
    def convert(self):
        items = self.create_from_directory(self.input_path)
        spatial_extent, temporal_extent = Utils.infer_extents_from(items)
        collection_extent = pystac.Extent(spatial=spatial_extent, temporal=temporal_extent)
        outer_collection = Utils.create_collection("outer_collection", )

        item = pystac.Item()
        assets = self.create_assets({})

        for asset in assets:
            item.add_asset(Soilgrids_Constants.asset_key, asset)

    def create_assets(self, wrapper: dict):
        assets = list()

        for href, title in wrapper.items():
            asset = Utils.create_asset(href=href, title=title, media_type=pystac.MediaType.GEOTIFF)
            assets.append(asset)

        return assets
