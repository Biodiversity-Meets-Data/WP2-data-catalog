from dateutil import parser
from deprecated import deprecated

import metapype.eml.names as names  # type: ignore
import metapype.eml.validate as validate  # type: ignore
import metapype.eml.export  # type: ignore
from metapype.model.node import Node  # type: ignore
from metapype.eml.exceptions import MetapypeRuleError  # type: ignore

import src.copernicus.stac.constants as constants
from src.copernicus.shared.shared_constants import *


def add_project(parent_node, title: str, description: str):
    logging.debug("add project")
    project_node = add_node(parent_node, names.PROJECT)
    title_node = add_node(project_node, names.TITLE)
    title_node.content = title
    abstract_node = add_node(project_node, names.ABSTRACT)
    abstract_node.content = description
    personnel_node = add_node(project_node, names.PERSONNEL)


def add_creator(parent_node, creator: Dict[str, str]):
    logging.debug("add creator")
    creator_node = add_node(parent_node, names.CREATOR)
    org_node = add_node(creator_node, names.ORGANIZATIONNAME)
    org_node.content = creator[constants.NAME]
    url_node = add_node(creator_node, names.ONLINEURL)
    url_node.content = creator[URL]


def add_license_url(parent_node, wrapper):
    logging.debug("add license url")
    url_node = add_node(parent_node, names.URL)
    url_node.content = wrapper[HREF]


@deprecated(reason="use intellectualRight node instead")
def add_licensor(parent_node, wrapper):
    logging.debug("add more licensor")
    licensed_node = add_node(parent_node, names.LICENSED)
    license_name_node = add_node(licensed_node, names.LICENSENAME)
    license_name_node.content = wrapper[constants.ROLES][0]
    url_node = add_node(licensed_node, names.URL)
    url_node.content = wrapper[URL]
    identifier_node = add_node(licensed_node, names.IDENTIFIER)
    identifier_node.content = wrapper[constants.NAME]


def add_distributions(parent_node, schemes, dataset_id: str):
    distribution_node = add_node(parent_node, names.DISTRIBUTION)

    # add link to stac browser
    source = {
        TITLE: "Copernicus STAC browser",
        PLATFORM: "https://browser.stac.dataspace.copernicus.eu/collections/{0}".format(dataset_id),
        DESCRIPTION: "this is the link to the Copernicus STAC browser"
    }
    add_distribution(distribution_node, source)

    # add other
    if schemes is not False:
        for key, value in schemes.items():
            # hard-code generic link to documentation instead of the page requiring credentials
            value["platform"] = "https://documentation.dataspace.copernicus.eu/APIs/S3.html"
            add_distribution(distribution_node, value)


def extract_coordinates(wrapper):
    """order is specific to copernicus stac geojson"""
    bbox = wrapper[constants.BBOX][0]
    result = {
        WEST: bbox[0],
        SOUTH: bbox[1],
        EAST: bbox[2],
        NORTH: bbox[3]
    }

    return result


def extract_interval(wrapper):
    interval = wrapper[constants.INTERVAL][0]
    result = {
        START: datetime_to_date(interval[0]),
        END: datetime_to_date(interval[1])
    }

    return result


def datetime_to_date(date):
    if date is not None:
        return parser.isoparse(date).strftime("%Y-%m-%d")
    return date


def extract_license(links):
    for link in links:
        if link[constants.REL] == "license":
            return link

    return False


def extract_creator(providers):
    """producer seems to be the equivalent term to creator/originator"""
    for provider in providers:
        if "producer" in provider[constants.ROLES]:
            return provider

    return False


def extract_licensor(providers):
    for provider in providers:
        if "licensor" in provider[constants.ROLES]:
            return provider

    return False


def extract_methods(item_assets):
    steps = []

    for key, value in item_assets.items():
        steps.append(value[TITLE])

    return steps


def extract_data_tables(item_assets):
    result = []

    for key, value in item_assets.items():
        wrapper = {
            constants.NAME: key,
            DESCRIPTION: value[TITLE],
            TYPE: value[TYPE]
        }
        result.append(wrapper)

    return result


def extract_storage(wrapper: dict):
    key = "storage:schemes"

    if key in wrapper.keys():
        return wrapper.get(key)

    return False


@deprecated(reason="replaced by data tables")
def add_methods(parent_node, methods):
    logging.debug("add methods")
    methods_node = add_node(parent_node, names.METHODS)

    for method_step in methods:
        add_method_step(methods_node, method_step)


def add_data_tables(parent_node, wrapper: list):
    for entry in wrapper:
        data_table_node = add_node(parent_node, names.DATATABLE)
        entity_name = add_node(data_table_node, names.ENTITYNAME)
        entity_name.content = entry[constants.NAME]
        entity_description = add_node(data_table_node, names.ENTITYDESCRIPTION)
        entity_description.content = entry[DESCRIPTION]
        physical_node = add_node(data_table_node, names.PHYSICAL)
        data_format_node = add_node(physical_node, names.DATAFORMAT)
        externally_node = add_node(data_format_node, names.EXTERNALLYDEFINEDFORMAT)
        format_name_node = add_node(externally_node, names.FORMATNAME)
        format_name_node.content = entry[TYPE]
        # TODO add bands if present


def add_intellectual_rights(parent_node, wrapper):
    intellectual_node = add_node(parent_node, names.INTELLECTUALRIGHTS)
    para_node = add_node(intellectual_node, names.PARA)
    para_node.content = "Licensor: " + wrapper[URL]


def convert_collection(collection):
    # get reusable values early
    # collection.
    dataset_id = collection[constants.ID]
    title = collection[TITLE]
    logging.info("convert collection {0} {1}".format(dataset_id, title))
    extend = collection[constants.EXTENT]
    description = collection[DESCRIPTION]
    keywords = collection[KEYWORDS]
    license = collection[LICENSE]
    links = collection[constants.LINKS]
    providers = collection[constants.PROVIDERS]
    item_assets = collection["item_assets"]
    linked_license = extract_license(links)
    creator = extract_creator(providers)
    licensor = extract_licensor(providers)
    methods = extract_methods(item_assets)
    data_tables_wrapper = extract_data_tables(item_assets)
    schemes = extract_storage(collection)

    # eml root
    eml = Node(names.EML)
    eml.add_attribute('packageId', 'edi.23.1')
    eml.add_attribute('system', 'metapype')
    # data root
    dataset_node = Node(names.DATASET, parent=eml)
    eml.add_child(dataset_node)
    # children
    add_project(dataset_node, title, description)
    add_alternative_id(dataset_node, dataset_id)
    add_short_name(dataset_node, dataset_id)
    add_title(dataset_node, title)
    add_abstract(dataset_node, description)
    add_creator(dataset_node, creator)
    coordinates = extract_coordinates(extend[constants.SPATIAL])
    coverage = extract_interval(extend[constants.TEMPORAL])
    add_coverage(dataset_node, coordinates, coverage[START], coverage[END])
    add_keywords(dataset_node, keywords)
    add_intellectual_rights(dataset_node, licensor)
    license_node = add_license(dataset_node, license)
    add_license_url(license_node, linked_license)
    add_metadata_provider(dataset_node)
    add_distributions(dataset_node, schemes, dataset_id)
    # add_methods(dataset_node, methods)
    add_data_tables(dataset_node, data_tables_wrapper)

    try:
        validate.tree(eml)
    except MetapypeRuleError as e:
        logging.error(e)

    return eml
