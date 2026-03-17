import os
import traceback
import argparse
import glob
from datetime import datetime
from tempfile import TemporaryDirectory
from urllib import parse
from urllib.parse import urlparse
import pystac
from pystac import Extent
from pystac.extensions.eo import Band, EOExtension
import rasterio
import rasterio.warp
import shapely
from shapely.geometry import Polygon, mapping, shape


class Convert:
    def __init__(self, arguments):
        self.date_time = datetime.fromisoformat(arguments.datetime)
        self.start_datetime = datetime.fromisoformat(arguments.start_datetime)
        self.end_datetime = datetime.fromisoformat(arguments.end_datetime)
        self.projection = arguments.projection
        self.input_path = arguments.input_path
        self.output_path = arguments.output_path
        self.title = arguments.title

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
        catalog.describe()
        # catalog.normalize_and_save(root_href=os.path.join(tmp_dir.name, 'stac-collection'),
        #                            catalog_type=pystac.CatalogType.SELF_CONTAINED)
        catalog.normalize_and_save(root_href=self.output_path, catalog_type=pystac.CatalogType.SELF_CONTAINED)

    def create_from_directory(self, directory_path):
        print(f"creating items for directory {directory_path}")
        items = list()

        if not os.path.isdir(directory_path):
            raise Exception(f"{directory_path} is not a directory")

        files = glob.glob(f"{directory_path}/*.tif")
        print(f"found " + str(len(files)) + " files")

        for file in files:
            items.append(self.create_item_from_file(file))

        return items

    def create_item_from_file(self, file_path):
        print(f"creating item for file {file_path}")

        if not os.path.isfile(file_path):
            raise Exception(f"{file_path} is not a file")

        with rasterio.open(file_path) as src:
            filename = os.path.basename(file_path)
            return self.create_item_from_raster(src=src, filename=filename, href=file_path, title=self.title)

    @staticmethod
    def create_catalog(catalog_id: str, description: str):
        print(f"creating catalog {catalog_id}")
        catalog = pystac.Catalog(id=catalog_id, description=description)

        return catalog

    @staticmethod
    def create_collection(collection_id: str, description: str, extent: Extent):
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

    @staticmethod
    def create_asset(href: str, title: str):
        print(f"creating asset {href}")
        asset = pystac.Asset(
            href=href,
            title=title,
            extra_fields={
                "eo:bands": [ # REQUIRED: define the bands in the eo extension for openEO to be able to load it
                    {
                        "name": "bdod-band",
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
            ],
            assets={
                "bdod": Convert.create_asset(href=href, title=title)
            }
        )

        item.validate()
        return item

    @staticmethod
    def create_bands(src):
        bands = list()

        for band in src:
            bands.append(Band.create(name=band))

        return bands


def manage_arguments(arguments):
    """
    TODO
    maybe infer start_datetime from datetime
    """


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

for bdod_tiff in bdod_tiffs:
    url = parse.urljoin(bdod_url, bdod_tiff)
    bdod_urls.append(url)

# bands
band_names = ["0-5cm",
             "5-15cm",
             "15-30cm",
             "30-60cm",
             "60-100cm",
             "100-200cm"]

# parser for arguments
parser = argparse.ArgumentParser(
    prog='STAC converter',
    description='converts datasets into collection/items')
# setup arguments
parser.add_argument('-d', '--datetime', required=True)
parser.add_argument('-e', '--end_datetime', required=True)
parser.add_argument('-i', '--input_path')
parser.add_argument('-o', '--output_path', required=True)
parser.add_argument('-p', '--projection', required=True)
parser.add_argument('-s', '--start_datetime', required=True)
parser.add_argument('-t', '--title', required=True)
# parse
args = parser.parse_args()
# check with some logic
manage_arguments(args)

try:
    convert = Convert(arguments=args)
    convert.convert(urls=bdod_urls)
except Exception as e:
    print(traceback.format_exc())
