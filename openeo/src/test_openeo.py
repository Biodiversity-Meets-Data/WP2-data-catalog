import os
import traceback
import argparse
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
    def __init__(self, arguments):
        self.arguments = arguments

    def create_from_directory(self, directory_path):
        """TODO: read from filesystem instead of accessing url"""

    def create_from_urls(self, urls: list):
        print("converting " + str(len(urls)) + " urls")

        # tmp_dir = TemporaryDirectory()
        # print(f"temp dir {tmp_dir}")

        items = self.create_items_from_urls(urls)

        spatial_extent, temporal_extent = self.infer_extents_from(items)
        collection_extent = pystac.Extent(spatial=spatial_extent, temporal=temporal_extent)
        collection = self.create_collection("test_collection", "test collection", extent=collection_extent)
        collection.add_items(items)

        catalog = self.create_catalog("test_catalog", "test catalog")
        catalog.add_child(collection)
        catalog.describe()
        # catalog.normalize_and_save(root_href=os.path.join(tmp_dir.name, 'stac-collection'),
        #                            catalog_type=pystac.CatalogType.SELF_CONTAINED)
        catalog.normalize_and_save(root_href=self.arguments.output_path, catalog_type=pystac.CatalogType.SELF_CONTAINED)

    def create_catalog(self, catalog_id: str, description: str):
        print(f"creating catalog {catalog_id}")
        catalog = pystac.Catalog(id=catalog_id, description=description)

        return catalog

    def create_collection(self, collection_id: str, description: str, extent: Extent):
        print(f"creating collection {collection_id}")
        collection = pystac.Collection(id=collection_id, description=description, extent=extent)

        return collection

    def create_items_from_urls(self, urls):
        print("creating items for " + str(len(urls)) + " urls")
        items = list()

        for url in urls:
            print(f"url {url}")
            item = self.create_item_from_url(url)
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
        date_time = datetime.fromisoformat(self.arguments.datetime)
        start_datetime = datetime.fromisoformat(self.arguments.start_datetime)
        end_datetime = datetime.fromisoformat(self.arguments.end_datetime)
        projection = self.arguments.projection

        with rasterio.open(url) as src:
            filename = os.path.basename(urlparse(url).path)
            proj_bounds = list(src.bounds)
            left, bottom, right, top = rasterio.warp.transform_bounds(src.crs, projection, *src.bounds)
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
                datetime=date_time,
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


def manage_arguments(arguments):
    """
    TODO
    maybe infer start_datetime from datetime
    """
    print(arguments.datetime, arguments.start_datetime, arguments.end_datetime)


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
# output_path = os.path.join("../data/output/test_catalog", 'stac-collection')

# parser for arguments
parser = argparse.ArgumentParser(
    prog='STAC converter',
    description='converts datasets into collection/items')
# setup arguments
parser.add_argument('-d', '--datetime', required=True)
parser.add_argument('-s', '--start_datetime', required=True)
parser.add_argument('-e', '--end_datetime', required=True)
parser.add_argument('-p', '--projection', required=True)
parser.add_argument('-o', '--output_path', required=True)
# parse
args = parser.parse_args()
# check with some logic
manage_arguments(args)

for bdod_tiff in bdod_tiffs:
    url = parse.urljoin(bdod_url, bdod_tiff)
    bdod_urls.append(url)

try:
    convert = Convert(arguments=args)
    convert.create_from_urls(urls=bdod_urls)
except Exception as e:
    print(traceback.format_exc())
