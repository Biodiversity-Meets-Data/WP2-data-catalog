import constants
import json
import logging
import metapype.eml.names as names
import metapype.eml.validate as validate
import metapype.eml.export
from datetime import datetime
from metapype.eml.exceptions import MetapypeRuleError

from src.copernicus.shared.shared_constants import *


def convert_dataset(dataset):
    """
    some properties are identical in json and xml, some are similar, some must be inferred
    :param dataset:
    :return:
    """
    # internal identifier
    dataset_id = dataset[constants.DATASET_ID]
    terms = dataset[constants.TERMS]
    metadata = dataset[constants.METADATA]
    # displayed identifier
    title = metadata[TITLE]
    description = metadata[DESCRIPTION]
    source = metadata[constants.SOURCE]
    distribution = extract_data(source, constants.DISTRIBUTION)
    # readable title
    dataset_title = source[constants.DATASET_TITLE]
    short_name = extract_data(source, constants.ALTERNATE_TITLE)
    language = extract_data(source, constants.LANGUAGE)
    abstract = source[constants.ABSTRACT]
    # seems to be the matching date
    pub_date = extract_data(source, constants.CREATION_DATE)
    # may not be there
    distributor = extract_data(metadata, constants.DISTRIBUTOR_CONTACT)
    # aka contacts
    responsible_party = source[constants.RESPONSIBLE_PARTY]
    keywords = source[KEYWORDS]
    location = source[constants.LOCATION]
    coordinates = location[constants.COORDINATES]
    start_date = extract_data(source, constants.TEMPEXTENT_BEGIN)
    end_date = extract_data(source, constants.TEMPEXTENT_END)

    eml = Node(names.EML)
    eml.add_attribute('packageId', 'edi.23.1')
    eml.add_attribute('system', 'metapype')

    dataset = Node(names.DATASET, parent=eml)
    eml.add_child(dataset)

    alt_identifier = Node(names.ALTERNATEIDENTIFIER, parent=dataset)
    alt_identifier.content = dataset_id
    dataset.add_child(alt_identifier)

    short_name_node = add_node(dataset, names.SHORTNAME)
    short_name_node.content = short_name

    title_node = add_node(dataset, names.TITLE)
    title_node.content = dataset_title

    # creator
    add_creators(dataset, responsible_party)

    # metadata provider
    add_metadata_provider(dataset)

    # publication date
    add_pub_date(dataset, pub_date)

    # language
    add_language(dataset, language)

    # abstract
    add_abstract(dataset, abstract)

    # keywords
    success = add_keywords_objects(dataset, source)

    if success is False:
        add_keywords(dataset, keywords)

    # intellectual property
    add_intellectual_right(dataset, terms)

    # license
    add_licenses(dataset, terms)

    # distribution
    # add_distribution(dataset, distribution)
    # add_distributors(dataset, distributor)

    # coverage
    add_coverage(dataset, coordinates, start_date, end_date)

    # contact
    add_contacts(dataset, responsible_party)

    # methods
    # TODO

    # project
    add_project(dataset, dataset_title, "", "Copernicus")

    # datatables
    # todo may be request to STAC http://stac.marine.copernicus.eu/metadata/SEALEVEL_EUR_PHY_L4_MY_008_068/cmems_obs-sl_eur_phy-ssh_my_allsat-l4-duacs-0.0625deg_P1D_202411/dataset.stac.json
    # found under digitalTransfers property

    # extract_stac(source)

    return eml


def add_project(parent_node, dataset_title, givenname, surname):
    project_node = add_node(parent_node, names.PROJECT)
    title_node = add_node(project_node, names.TITLE)
    title_node.content = dataset_title
    personnel_node = add_node(project_node, names.PERSONNEL)
    add_individual(personnel_node, givenname, surname)
    role_node = add_node(personnel_node, names.ROLE)
    role_node.content = "NA"


def add_contacts(parent_node, data):
    if isinstance(data, list):
        for contact in data:
            add_contact(parent_node, contact)
    else:
        add_contact(parent_node, data)


def add_contact(parent_node, data):
    contact_node = add_node(parent_node, names.CONTACT)
    add_entity(data, contact_node)


def add_creators(parent_node, content):
    if isinstance(content, list):
        for party in content:
            add_creator(parent_node, party)
    else:
        add_creator(parent_node, content)


def add_creator(parent_node, content):
    """
    only if content is originator
    :param parent_node:
    :param content:
    :return:
    """
    if content[RESPONSIBLE_PARTY_ROLE] == constants.ORIGINATOR or content[RESPONSIBLE_PARTY_ROLE] == constants.RESOURCE_PROVIDER:
        creator_node = add_node(parent_node, names.CREATOR)
        add_entity(content, creator_node)


def add_coverage(parent_node, coordinates, start_date, end_date):
    coverage_node = add_node(parent_node, names.COVERAGE)
    add_geographical_coverage(coverage_node, coordinates)
    add_temporal_coverage(coverage_node, start_date, end_date)


def add_geographical_coverage(parent_node, json_coordinates):
    geographical_coverage = add_node(parent_node, names.GEOGRAPHICCOVERAGE)

    # description
    geographic_description = add_node(geographical_coverage, names.GEOGRAPHICDESCRIPTION)
    geographic_description.content = "world"

    # coordinates
    add_coordinates(geographical_coverage, json_coordinates)
    # print(geographical_coverage)


def add_coordinates(parent_node, json_coordinates):
    coordinates_node = add_node(parent_node, names.BOUNDINGCOORDINATES)
    # west
    west_node = add_node(coordinates_node, names.WESTBOUNDINGCOORDINATE)
    west_node.content = extract_coordinate(json_coordinates, 0, 0)
    # east
    east_node = add_node(coordinates_node, names.EASTBOUNDINGCOORDINATE)
    east_node.content = extract_coordinate(json_coordinates, 1, 0)
    # north
    north_node = add_node(coordinates_node, names.NORTHBOUNDINGCOORDINATE)
    north_node.content = extract_coordinate(json_coordinates, 0, 1)
    # south
    south_node = add_node(coordinates_node, names.SOUTHBOUNDINGCOORDINATE)
    south_node.content = extract_coordinate(json_coordinates, 1, 1)
    # print(coordinates)


def add_distribution(parent_node, content):
    if isinstance(content, list):
        for name in content:
            distribution_node = add_node(parent_node, names.DISTRIBUTION)
            online_node = add_node(distribution_node, names.ONLINE)
            online_description_node = add_node(online_node, names.ONLINEDESCRIPTION)
            online_description_node.content = name
            url_node = add_node(online_node, names.URL)
            url_node.content = name


def add_distributors(parent_node, content):
    if isinstance(content, list):
        for entry in content:
            add_distributor(parent_node, entry)
    else:
        add_distributor(parent_node, content)


def add_distributor(parent_node, content):
    distribution_node = add_node(parent_node, names.DISTRIBUTION)
    online_node = add_node(distribution_node, names.ONLINE)
    online_description_node = add_node(online_node, names.ONLINEDESCRIPTION)
    online_description_node.content = content[ORGANISATION_NAME]
    url_node = add_node(online_node, names.URL)
    url_node.content = extract_data(content, URL)


def add_licenses(parent_node, licenses):
    for license in licenses:
        add_license(parent_node, license)


def add_intellectual_right(parent_node, content):
    intel_right_node = add_node(parent_node, names.INTELLECTUALRIGHTS)

    for wrapper in content:
        para_node = add_node(intel_right_node, names.PARA)
        para_node.content = wrapper


def add_language(parent_node, language):
    language_node = add_node(parent_node, names.LANGUAGE)
    language_node.content = language


def add_pub_date(parent_node, date):
    date_node = add_node(parent_node, names.PUBDATE)
    date_node.content = date


def add_keywords_objects(parent_node, data):
    if data.get(constants.KEYWORDS_AS_OBJECTS) is not None:
        keywords_objects = data[constants.KEYWORDS_AS_OBJECTS]

        # single entry may be directly a dict -> create list
        if isinstance(keywords_objects, dict):
            keywords_objects = [keywords_objects]

        for keywords_object in keywords_objects:
            if keywords_object.get(constants.KEYWORD) is not None:
                keyword_set_node = add_node(parent_node, names.KEYWORDSET)
                keywords = keywords_object[constants.KEYWORD]

                # single entry may be directly a dict -> create list
                if isinstance(keywords, str):
                    keywords = [keywords]

                add_keywords(keyword_set_node, keywords)

                if keywords_object.get(constants.THESAURUS) is not None:
                    thesaurus = keywords_object[constants.THESAURUS]
                    thesaurus_node = add_node(keyword_set_node, names.KEYWORDTHESAURUS)
                    thesaurus_node.content = thesaurus
        return True
    return False


def extract_coordinate(data, x, y):
    coordinate = data[x][y]

    if isinstance(coordinate, int) is False:
        raise ValueError("{0} is not a valid coordinate".format(coordinate))

    return coordinate


def extract_data_na(data, key):
    if data.get(key) is None:
        return "NA"
    return data.get(key)


def extract_stac(data):
    if data.get(constants.DIGITAL_TRANSFERS) is not None:
        digital_transfers = data[constants.DIGITAL_TRANSFERS]

        for digital_transfer in digital_transfers:

            if digital_transfer.get(constants.AVAILABILITY) is not None:
                sources = digital_transfer[constants.AVAILABILITY]
                # print(type(sources))

                for source in sources:
                    # print(source)

                    if isinstance(source, dict) and source[URL] is not None:
                        print(source[URL])


f = open("../data/extreme_precipitation_risk_indicators.json")
dataset = json.loads(f.read())
eml = convert_dataset(dataset)

try:
    validate.tree(eml)
except MetapypeRuleError as e:
    logging.error(e)

xml_str = metapype.eml.export.to_xml(eml)
file_path = "../data/converted_eml.xml"
with open(file_path, 'w') as f:
    f.write(xml_str)
    print("eml saved {0}".format(file_path))
