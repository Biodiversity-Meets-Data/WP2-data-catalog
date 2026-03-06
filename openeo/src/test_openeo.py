import os
import traceback
from tempfile import TemporaryDirectory
from urllib import parse
from urllib.parse import urlparse
import pystac
import shapely
from pystac import Extent
from datetime import datetime
import rasterio
import rasterio.warp
from shapely.geometry import Polygon, mapping, shape


class Convert:
    def create_from_urls(self, urls: list, datetime, start_datetime, end_datetime):
        print("converting " + str(len(urls)) + " urls")

        # tmp_dir = TemporaryDirectory()
        # print(f"temp dir {tmp_dir}")

        items = self.create_items_from_urls(urls, datetime=datetime, start_datetime=start_datetime, end_datetime=end_datetime)

        spatial_extent, temporal_extent = self.infer_extents_from(items)
        collection_extent = pystac.Extent(spatial=spatial_extent, temporal=temporal_extent)
        collection = self.create_collection("test_collection", "test collection", extent=collection_extent)
        collection.add_items(items)

        catalog = self.create_catalog("test_catalog", "test catalog")
        catalog.add_child(collection)
        catalog.describe()
        # catalog.normalize_and_save(root_href=os.path.join(tmp_dir.name, 'stac-collection'),
        #                            catalog_type=pystac.CatalogType.SELF_CONTAINED)
        catalog.normalize_and_save(root_href=os.path.join("../data", 'stac-collection'),
                                   catalog_type=pystac.CatalogType.SELF_CONTAINED)

    def create_catalog(self, catalog_id: str, description: str):
        print(f"creating catalog {catalog_id}")
        catalog = pystac.Catalog(id=catalog_id, description=description)

        return catalog

    def create_collection(self, collection_id: str, description: str, extent: Extent):
        print(f"creating collection {collection_id}")
        collection = pystac.Collection(id=collection_id, description=description, extent=extent)

        return collection

    def create_items_from_urls(self, urls, datetime, start_datetime, end_datetime):
        print("creating items for " + str(len(urls)) + " urls")
        items = list()

        for url in urls:
            print(f"url {url}")
            # item = self.create_item(entry.id)
            item = self.create_item_from_url(url, datetime=datetime, start_datetime=start_datetime, end_datetime=end_datetime)
            items.append(item)

        return items

    def create_item(self, item_id: str):
        print(f"creating item {item_id}")
        item = pystac.Item(item_id)
        asset = self.create_asset()
        item.add_asset(asset)

        return item

    def create_asset(self, href: str):
        print(f"creating asset {href}")
        asset = pystac.Asset(href)

        return asset

    def get_bbox_and_footprint(self, raster):
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

    def infer_extents_from(self, items: list):
        print("inferring extents for " + str(len(items)) + " items")
        geometries = list()
        datetimes = list()

        for item in items:
            geometries.append(shape(item.geometry))
            datetimes.append(item.datetime)

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

    def create_item_from_url(self, url, datetime, start_datetime, end_datetime):
        with rasterio.open(url) as src:
            filename = os.path.basename(urlparse(url).path)
            proj_bounds = list(src.bounds)
            left, bottom, right, top = rasterio.warp.transform_bounds(src.crs, "EPSG:4326", *src.bounds)
            polygon = mapping(Polygon([
                [left, bottom],
                [right, bottom],
                [right, top],
                [left, top],
                [left, bottom]
            ]))

            item = pystac.Item(
                id=filename,
                geometry=polygon,
                bbox=[left, bottom, right, top],
                datetime=datetime,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                properties={ # These properties are optional, but can speed up the loading of the data.
                    "proj:epsg": src.crs.to_epsg(),
                    "proj:shape": src.shape, # Caveat: this is [height, width] and not [width, height] if you want to set them yourself
                    "proj:bbox": proj_bounds,
                },
                stac_extensions=[
                    "https://stac-extensions.github.io/eo/v1.1.0/schema.json",
                    "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
                ],
                assets={
                    "bdod": pystac.Asset(
                        href=url,
                        title="SoilGrids250m 2.0 - Bulk density aggregated 5000m",
                        extra_fields={
                            "eo:bands": [ # REQUIRED: define the bands in the eo extension for openEO to be able to load it
                                {
                                    "name": "bdod-band",
                                }
                            ],
                        }
                    )
                }
            )

            item.validate()
            return item


# def convert_url(url, name):
#     print(f"converting url {url}")
#
#     dt = datetime.fromisoformat("1905-04-01")
#     start_datetime = dt
#     end_datetime = datetime.fromisoformat("2016-07-05")
#     output_path = f"../data/{name}.json"
#
#     with rasterio.open(url) as src:
#         proj_bounds = list(src.bounds)
#         left, bottom, right, top = rasterio.warp.transform_bounds(src.crs, "EPSG:4326", *src.bounds)
#         polygon = mapping(Polygon([
#             [left, bottom],
#             [right, bottom],
#             [right, top],
#             [left, top],
#             [left, bottom]
#         ]))
#
#         item = pystac.Item(
#             id="bdod-stac-item",
#             geometry=polygon,
#             bbox=[left, bottom, right, top],
#             datetime=dt,
#             start_datetime=start_datetime,
#             end_datetime=end_datetime,
#             properties={ # These properties are optional, but can speed up the loading of the data.
#                 "proj:epsg": src.crs.to_epsg(),
#                 "proj:shape": src.shape, # Caveat: this is [height, width] and not [width, height] if you want to set them yourself
#                 "proj:bbox": proj_bounds,
#             },
#             stac_extensions=[
#                 "https://stac-extensions.github.io/eo/v1.1.0/schema.json",
#                 "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
#             ],
#             assets={
#                 "bdod": pystac.Asset(
#                     href=url,
#                     title="SoilGrids250m 2.0 - Bulk density aggregated 5000m",
#                     extra_fields={
#                         "eo:bands": [ # REQUIRED: define the bands in the eo extension for openEO to be able to load it
#                             {
#                                 "name": "bdod-band",
#                             }
#                         ],
#                     }
#                 )
#             }
#         )
#
#         item.validate()
#         item.save_object(dest_href=output_path, include_self_link=False)


# base url
bdod_url = "https://files.isric.org/soilgrids/latest/data_aggregated/5000m/bdod/"
# url to the tiff files
bdod_tiffs = ["bdod_0-5cm_mean_5000.tif",
              "bdod_5-15cm_mean_5000.tif",
              "bdod_15-30cm_mean_5000.tif",
              "bdod_30-60cm_mean_5000.tif",
              "bdod_60-100cm_mean_5000.tif",
              "bdod_100-200cm_mean_5000.tif"]
bdod_urls = list()
datetime = datetime.fromisoformat("1905-04-01")
start_datetime = datetime
end_datetime = datetime.fromisoformat("2016-07-05")

for bdod_tiff in bdod_tiffs:
    url = parse.urljoin(bdod_url, bdod_tiff)
    bdod_urls.append(url)
    # convert_url(url, bdod_tiff)

try:
    convert = Convert()
    convert.create_from_urls(urls=bdod_urls, datetime=datetime, start_datetime=start_datetime, end_datetime=end_datetime)
except Exception as e:
    # print(f"An error occurred: {e}")
    print(traceback.format_exc())
