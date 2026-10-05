import os
import logging
import time
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime

from pystac import Asset, RelType, Extent, CatalogType, MediaType
from pystac.extensions.eo import EOExtension
import rasterio
import rasterio.warp
from pystac.extensions.raster import RasterExtension
from rasterio import RasterioIOError
from shapely.geometry import box, mapping
from shapely.ops import unary_union
from src.misc.soilgrids.constants import Constants as Soilgrids_Constants
from src.misc.soilgrids.utils import Utils as Soilgrids_Utils
from src.misc.utils import Utils
from src.misc.geonetwork.extraction_elasticsearch import ExtractionElasticsearch
from src.misc.geonetwork.extraction_eml import ExtractionEML
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
        self.query_type = arguments.query_type

    def convert(self):
        """
        main function with the top-level steps:
        - Catalog/Collections/Items creation
        - associate Items and Collection, Collection and Catalog,
        - normalize and save
        """
        # TODO: add dates, geometry
        # get geonetwork dataset
        if self.query_type == Soilgrids_Constants.elastic_value:
            extractor = ExtractionElasticsearch()
        elif self.query_type == Soilgrids_Constants.eml_value:
            extractor = ExtractionEML()
        else:
            raise Exception(f"incorrect type {self.query_type}")

        soilgrids_dataset = extractor.query_dataset(uuid=Soilgrids_Constants.soilgrids_dataset_uuid,
                                                    query_type=self.query_type)

        # create top to bottom
        top_catalog = Utils.create_catalog("top_catalog", description="at the top")
        soilgrids_catalog = Utils.create_catalog("soilgrids_catalog", "below top")

        # resolutions = [Soilgrids_Constants.RESOLUTION_1000]
        resolutions = Soilgrids_Constants.RESOLUTIONS
        # variable_names = [Soilgrids_Constants.BDOD_VALUE, Soilgrids_Constants.SAND_VALUE]
        variable_names = Soilgrids_Constants.VARIABLE_NAMES
        attributes = extractor.extract_attributes(soilgrids_dataset)

        for resolution in resolutions:
            items = list()
            # collection id
            collection_id = Soilgrids_Utils.create_collection_id(resolution)
            # citations
            methods = Utils.check_key(Soilgrids_Constants.methods_key, soilgrids_dataset)
            first_citation = extractor.extract_citation(methods=methods)
            doi = extractor.extract_doi(citation=first_citation)
            # extra fields
            extra_fields = {
                "sci:citation": first_citation,
                "sci:doi": doi,
                "proj:code": Soilgrids_Constants.HOMOLOSINE_CODE
            }

            for variable_name in variable_names:
                entries = ConvertMultipleAssets.generate_entries(resolution=resolution, variable_names=[variable_name])
                item_id = Soilgrids_Utils.create_item_id(collection_id=collection_id, variable_name=variable_name)
                item = self.create_item_from_rasters(variable_name,
                                                     item_id=item_id,
                                                     entries=entries,
                                                     projection=self.projection,
                                                     attributes=attributes,
                                                     extra_fields=extra_fields)

                if item is None:
                    logger.warning(f"no item for {variable_name}")
                else:
                    links = Soilgrids_Utils.create_links(rel_type=RelType.VIA, action=self.query_type)
                    item.add_links(links)
                    items.append(item)

            # gather extents
            spatial_extent, temporal_extent = Utils.infer_extents_from(items)
            collection_extent = Extent(spatial=spatial_extent, temporal=temporal_extent)

            # collection level
            keywords = extractor.extract_keywords(dataset=soilgrids_dataset)
            # make it unique with set()
            collection_keywords = list(set(list(("soilgrids", "aggregated", resolution)) + variable_names + keywords))
            # license name and url
            license_wrapper = extractor.extract_license(dataset=soilgrids_dataset)
            collection_license_name = license_wrapper[0]
            license_url = license_wrapper[1]
            collection_license_link = Utils.create_link(rel="license",
                                                        href=license_url,
                                                        type="text/html",
                                                        title=collection_license_name)
            # many providers
            collection_providers = extractor.extract_providers(soilgrids_dataset)
            # wrapper for title and description
            project = Utils.check_key(Soilgrids_Constants.project_key, soilgrids_dataset)
            tmp = extractor.extract_title_description(project=project)
            collection_title = tmp[0]
            collection_description = tmp[1]

            soilgrids_collection = Utils.create_collection(collection_id=collection_id,
                                                           title=collection_title,
                                                           description=collection_description,
                                                           extent=collection_extent,
                                                           license=collection_license_name,
                                                           keywords=collection_keywords,
                                                           providers=collection_providers,
                                                           extra_fields=extra_fields)

            # absolute links
            links = Soilgrids_Utils.create_links(rel_type=RelType.VIA, action=self.query_type)
            soilgrids_collection.add_links(links)

            # add bottom to top
            soilgrids_collection.add_items(items)
            soilgrids_collection.add_link(collection_license_link)
            soilgrids_catalog.add_child(soilgrids_collection)

        top_catalog.add_child(soilgrids_catalog)
        # top_catalog.describe()
        top_catalog.normalize_and_save(root_href=self.output_path, catalog_type=CatalogType.SELF_CONTAINED)

    def create_item_from_rasters(self, variable_name: str, item_id: str, entries: list, projection: str,
                                 attributes: dict, extra_fields: dict):
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
            extra_fields["soilgrids:variable"] = variable_name
            item = Utils.create_simple_item(item_id=item_id,
                                            datetime=self.date_time,
                                            start_datetime=self.start_datetime,
                                            end_datetime=self.end_datetime,
                                            bbox=bbox,
                                            geometry=geometry,
                                            properties=extra_fields)

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

                    # reuse attribute data read from the datasource (catalog)
                    if variable_name in attributes:
                        logger.info("there are attributes to add")
                        raster_band = Utils.create_raster_band(attributes[variable_name])
                        raster_ext = RasterExtension.ext(asset, add_if_missing=True)
                        raster_ext.apply(bands=[raster_band])

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
    def create_asset(entry) -> Asset:
        """simple wrapper around Asset creation"""
        # TODO add file-related properties
        asset = Utils.create_asset(href=entry[Soilgrids_Constants.href_key],
                                   title=entry[Soilgrids_Constants.title_key],
                                   media_type=MediaType.GEOTIFF)

        return asset

    @staticmethod
    def create_assets(entries: list) -> list[Asset]:
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
