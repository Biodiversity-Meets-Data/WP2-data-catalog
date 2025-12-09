import logging
from datetime import datetime
from typing import List, Any, Dict

from metapype.model.node import Node  # type: ignore
import metapype.eml.names as names  # type: ignore

TITLE = "title"
DESCRIPTION = "description"
WEST = "west"
EAST = "east"
NORTH = "north"
SOUTH = "south"
START = "start"
END = "end"
KEYWORDS = "keywords"
LICENSE = "license"
INDIVIDUAL_NAME = "individualName"
ORGANISATION_NAME = "organisationName"
GIVEN_NAME = "givenname"
SURNAME = "surnmane"
RESPONSIBLE_PARTY_ROLE = "responsiblePartyRole"
PHONE = "phone"
EMAIL = "email"
URL = "url"
HREF = "href"
PLATFORM = "platform"
TYPE = "type"


def add_node(parent_node, eml_node_type):
    new_node = Node(eml_node_type, parent=parent_node)
    parent_node.add_child(new_node)
    return new_node


def add_date(parent_node, date: str):
    calendar_date = add_node(parent_node, names.CALENDARDATE)
    calendar_date.content = date


def add_alternative_id(parent_node, alt_id: str):
    logging.debug("add alternative id")
    node = add_node(parent_node, names.ALTERNATEIDENTIFIER)
    node.content = alt_id


def add_short_name(parent_node, short_name: str):
    logging.debug("add short name")
    node = add_node(parent_node, names.SHORTNAME)
    node.content = short_name


def add_title(parent_node, title: str):
    logging.debug("add title")
    title_node = add_node(parent_node, names.TITLE)
    title_node.content = title


def add_keywords(parent_node, keywords: List[str]):
    logging.debug("add keywords")
    keyword_set_node = add_node(parent_node, names.KEYWORDSET)

    for keyword in keywords:
        add_keyword(keyword_set_node, keyword)


def add_keyword(parent_node, keyword: str):
    logging.debug("add keyword")
    keyword_node = add_node(parent_node, names.KEYWORD)
    keyword_node.content = keyword


def add_license(parent_node, license: str):
    license_node = add_node(parent_node, names.LICENSED)
    license_name_node = add_node(license_node, names.LICENSENAME)
    license_name_node.content = license

    return license_node


def add_license_simple(parent_node, license: str):
    license_node = add_node(parent_node, "license")
    license_node.content = license


def add_method_step(parent_node, method_step: str):
    method_step_node = add_node(parent_node, names.METHODSTEP)
    description_node = add_node(method_step_node, names.DESCRIPTION)
    para_node = add_node(description_node, names.PARA)
    para_node.content = method_step


def add_entity(data, node):
    individual_name = extract_data(data, INDIVIDUAL_NAME)
    organisation_name = extract_data(data, ORGANISATION_NAME)
    givenname = ""

    if individual_name == "":
        givenname = extract_data(data, GIVEN_NAME)
        surname = extract_data(data, SURNAME)
    else:
        surname = individual_name

    if surname == "":
        surname = organisation_name

    position = extract_data(data, RESPONSIBLE_PARTY_ROLE)
    # individual
    add_individual(node, givenname, surname)
    # position
    add_data(node, names.POSITIONNAME, position)
    # the rest is optional
    add_optional_data(node, data, ORGANISATION_NAME, names.ORGANIZATIONNAME)
    add_optional_data(node, data, PHONE, names.PHONE)
    add_optional_data(node, data, EMAIL, names.ELECTRONICMAILADDRESS)
    add_optional_data(node, data, URL, names.ONLINEURL)


def add_individual(parent_node, givenname: str, surname: str):
    """
    :param parent_node: required
    :param givenname: optional
    :param surname: required
    :return:
    """
    individual_name_node = add_node(parent_node, names.INDIVIDUALNAME)
    # given name
    add_data(individual_name_node, names.GIVENNAME, givenname)
    # surname
    add_required_data(individual_name_node, names.SURNAME, surname)


def add_required_data(parent_node, eml_node, data):
    if data == "":
        raise ValueError("required value missing")

    add_data(parent_node, eml_node, data)


def add_data(parent_node, eml_node, data: Any):
    if data != "":
        new_node = add_node(parent_node, eml_node)
        new_node.content = data


def add_optional_data(parent_node, data, json_node, eml_node):
    if data.get(json_node) is not None:
        new_node = add_node(parent_node, eml_node)
        new_node.content = data[json_node]


def extract_data(data, key: str):
    if data.get(key) is None:
        return ""
    return data.get(key)


def add_abstract(parent_node, abstract: str):
    """
    @TODO fetch real abstract from remote source when available
    :param parent_node:
    :param abstract:
    :return:
    """
    logging.debug("add abstract")
    abstract_node = add_node(parent_node, names.ABSTRACT)
    para_node = add_node(abstract_node, names.PARA)
    para_node.content = abstract


def add_coverage(parent_node, coordinates, start_date: str, end_date: str):
    coverage_node = add_node(parent_node, names.COVERAGE)
    add_geographical_coverage(coverage_node, coordinates)
    add_temporal_coverage(coverage_node, start_date, end_date)


def add_geographical_coverage(parent_node, json_coordinates):
    geographical_coverage = add_node(parent_node, names.GEOGRAPHICCOVERAGE)

    # description
    # geographic_description = add_node(geographical_coverage, names.GEOGRAPHICDESCRIPTION)
    # geographic_description.content = "world"

    # coordinates
    add_coordinates(geographical_coverage, json_coordinates)
    # print(geographical_coverage)


def add_coordinates(parent_node, coordinates: Dict[str, str]):
    logging.debug("add coordinates")
    coordinates_node = add_node(parent_node, names.BOUNDINGCOORDINATES)
    # west
    west_node = add_node(coordinates_node, names.WESTBOUNDINGCOORDINATE)
    west_node.content = coordinates[WEST]
    # east
    east_node = add_node(coordinates_node, names.EASTBOUNDINGCOORDINATE)
    east_node.content = coordinates[EAST]
    # north
    north_node = add_node(coordinates_node, names.NORTHBOUNDINGCOORDINATE)
    north_node.content = coordinates[NORTH]
    # south
    south_node = add_node(coordinates_node, names.SOUTHBOUNDINGCOORDINATE)
    south_node.content = coordinates[SOUTH]
    # print(coordinates)


def add_temporal_coverage(parent_node, start: str, end: str):
    temporal_coverage = add_node(parent_node, names.TEMPORALCOVERAGE)
    range_of_dates = add_node(temporal_coverage, names.RANGEOFDATES)

    if start != "":
        begin_date = add_node(range_of_dates, names.BEGINDATE)
        add_date(begin_date, start)

    end_date = add_node(range_of_dates, names.ENDDATE)

    # if end == "":
    #     end = datetime.today().strftime('%Y-%m-%d')

    add_date(end_date, end)


def add_metadata_provider(parent_node):
    """hard-coded"""
    provider_node = add_node(parent_node, names.METADATAPROVIDER)
    content = {
        ORGANISATION_NAME: "SIB Swiss Institute of Bioinformatics",
        GIVEN_NAME: "Olivier",
        SURNAME: "Martin",
        EMAIL: "olivier.martin@sib.swiss",
        RESPONSIBLE_PARTY_ROLE: "Data Manager"
    }
    add_entity(content, provider_node)


def add_distribution(parent_node, storage: Dict[str, str]):
    logging.debug("add distribution")
    online_node = add_node(parent_node, names.ONLINE)
    online_description_node = add_node(online_node, names.ONLINEDESCRIPTION)
    online_description_node.content = storage[TITLE]
    url_node = add_node(online_node, names.URL)
    url_node.content = storage[PLATFORM]
    connection_node = add_node(online_node, names.CONNECTION)
    connection_node.content = storage[DESCRIPTION]