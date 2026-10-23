import logging
from typing import Any

import requests

from abc import ABCMeta, abstractmethod, ABC
from datetime import datetime

from pystac import Collection, Item, Extent, Provider, SpatialExtent, TemporalExtent
from shapely.geometry import box
from shapely.geometry.geo import mapping
from shapely.ops import unary_union

from src.misc.constants import Constants
from src.misc.query_types import QueryTypes
from src.misc.geonetwork.utils import Utils as GeonetworkUtils
from src.misc.utils import Utils

logger = logging.getLogger(__name__)


class ParserInterface(ABC):
    """
    - behavior shared by subclasses: manage commandline arguments -> log -> convert
    - one child class per datasource
    """
    __metaclass__ = ABCMeta

    def __init__(self, args):
        # check with some logic ?
        self.manage_arguments(args)
        self.output_path = args.output_path
        # only EML, elasticsearch support removed
        self.query_type = QueryTypes.EML

    @abstractmethod
    def manage_arguments(self, arguments): raise NotImplementedError

    def get_extractor(self):
        return GeonetworkUtils.get_extraction_instance(self.query_type)

    def query_dataset(self, uuid: str) -> dict:
        # get geonetwork dataset
        dataset = self.get_extractor().query_dataset(uuid=uuid, query_type=self.query_type)

        return dataset

    @abstractmethod
    def create_item(self, wrapper: dict) -> Item | None: raise NotImplementedError

    @abstractmethod
    def create_collection_id(self, wrapper: dict) -> str: raise NotImplementedError

    @abstractmethod
    def create_item_id(self, wrapper: dict) -> str: raise NotImplementedError

    def get_collection_title(self, dataset) -> tuple[str, str]:
        project = Utils.check_key(Constants.project_key, dataset)

        return self.get_extractor().extract_title_description(project=project)

    def get_collection_license(self, dataset) -> tuple[str, str]:
        return self.get_extractor().extract_license(dataset=dataset)

    def get_keywords(self, dataset, keywords: list[str]) -> list[str]:
        extracted_keywords = self.get_extractor().extract_keywords(dataset=dataset)
        all_keywords = extracted_keywords + keywords
        # make it unique with set()
        collection_keywords = list(set(all_keywords))

        return collection_keywords

    def get_providers(self, dataset) -> list[Provider]:
        return self.get_extractor().extract_providers(dataset=dataset)

    def get_extra_fields(self, dataset, projection=None):
        methods = Utils.check_key(Constants.methods_key, dataset)
        first_citation = self.get_extractor().extract_citation(methods=methods[0])
        doi = self.get_extractor().extract_doi(citation=first_citation)
        result = {
            "sci:citation": first_citation,
            "sci:doi": doi
        }

        if projection is not None:
            result["proj:code"] = projection

        # extra fields
        return result

    def create_collection(self,
                          collection_id: str,
                          title: str,
                          description: str,
                          extent: Extent,
                          license: str,
                          keywords: list[str] | None = None,
                          providers: list[Provider] | None = None,
                          extra_fields: dict[str, Any] | None = None) -> Collection:
        return Utils.create_collection(collection_id=collection_id,
                                       title=title,
                                       description=description,
                                       extent=extent,
                                       license=license,
                                       keywords=keywords,
                                       providers=providers,
                                       extra_fields=extra_fields)

    def get_dates(self, dataset) -> tuple[str, str, str]:
        """
            - will try to manage missing values
            - currently: if no datetime will use end_date instead
        """
        coverage = Utils.check_key(Constants.coverage_key, dataset)
        temporal = Utils.check_key(Constants.temporal_coverage_key, coverage)[0]
        start_date = Utils.check_key(Constants.begin_date_key, temporal)[0]
        end_date = Utils.check_key(Constants.end_date_key, temporal)[0]

        if Constants.datetime_key in temporal:
            date_time = Utils.check_key(Constants.datetime_key, temporal)[0]
        else:
            date_time = end_date

        return start_date, end_date, date_time

    def get_bounding_coordinates(self, dataset) -> tuple[float, float, float, float]:
        coverage = Utils.check_key(Constants.coverage_key, dataset)
        geographical = Utils.check_key(Constants.geographic_coverage_key, coverage)
        bounding_coordinates = Utils.check_key(Constants.bounding_coordinates_key, geographical)
        west = float(Utils.check_key(Constants.west_bounding_key, bounding_coordinates))
        east = float(Utils.check_key(Constants.east_bounding_key, bounding_coordinates))
        north = float(Utils.check_key(Constants.north_bounding_key, bounding_coordinates))
        south = float(Utils.check_key(Constants.south_bounding_key, bounding_coordinates))

        return west, east, north, south

    def get_extents(self, dataset):
        start_datetime, end_datetime, date_time = self.get_dates(dataset)
        bbox = self.get_bbox(dataset)
        spatial = SpatialExtent(bboxes=[bbox])
        temporal = TemporalExtent(intervals=[[datetime.fromisoformat(start_datetime), datetime.fromisoformat(end_datetime)]])
        extent = Extent(spatial, temporal)

        return extent

    def get_bbox(self, dataset) -> list[float | int]:
        """helper method to directly get ordered values"""
        west, east, north, south = self.get_bounding_coordinates(dataset)

        return [west, south, east, north]

    def get_geometry(self, dataset):
        geometries = []
        west, east, north, south = self.get_bounding_coordinates(dataset)
        geom = box(west, south, east, north)
        geometries.append(geom)
        merged_geom = unary_union(geometries)
        geometry = mapping(merged_geom)

        return geometry

    # @abstractmethod
    # def create_catalog(self) -> Catalog: raise NotImplementedError
    #
    # def steps(self):
    #     """putative implementation"""
    #     dataset = self.query_dataset()
    #     catalog = self.create_catalog()
    #     collection = self.create_collection()
    #     items = self.create_items()
    #
    #     collection.add_items(items)
    #     catalog.add_child(collection)
    #     catalog.normalize_and_save(root_href=self.output_path, catalog_type=CatalogType.SELF_CONTAINED)

    @abstractmethod
    def convert(self): raise NotImplementedError

    def run(self):
        logger.info("start")
        start = datetime.now()
        self.convert()
        end = datetime.now()
        elapsed = end - start
        logger.info(f"end in {elapsed}")
