"""queries /collections copernicus endpoint with some filters"""
import argparse
import os.path
import logging
import traceback
from pathlib import Path
from src.copernicus.stac import constants
from src.copernicus.stac.convert_collection import convert_collection
import metapype.eml.export  # type: ignore
from pystac_client import Client

# setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

# this is the other API that does not seem as useful
# client = Client.open("https://catalogue.dataspace.copernicus.eu/stac")
client = Client.open(constants.COPERNICUS_STAC_URL)


def filter_collections(collections):
    result = list()

    # filter on level manually
    for collection in collections:
        levels = collection["summaries"]["processing:level"]

        for level in levels:
            if level == constants.COPERNICUS_LEVEL_2:
                result.append(collection)
                break

    return result


def convert(dir: str, collections):
    for match in collections:
        dataset_id = match[constants.ID]

        try:
            eml = convert_collection(match)
            xml_str = metapype.eml.export.to_xml(eml)
            filename = "{dataset_id}_converted_eml.xml".format(dataset_id=dataset_id)
            file_path = os.path.join(dir, filename)
            with open(file_path, 'w') as f:
                f.write(xml_str)
                logging.info("eml saved {0}".format(file_path))
        except Exception:
            logging.error("exception with {0}".format(dataset_id))
            logging.error(traceback.format_exc())


def search():
    collection_search = client.collection_search(q='"sentinel-2" OR "sentinel-3" OR "sentinel-5p"')
    # collection_search = client.collection_search(q='"sentinel-2"')
    logging.info(f"{collection_search.matched()} collections found")
    # contains final collections
    result = filter_collections(collection_search.collections_as_dicts())
    logging.info("matching: {0}".format(len(result)))

    return result


def query_one(collection_id: str):
    collection = client.get_collection(collection_id)

    if collection is None:
        raise Exception("nothing found for {0}".format(collection_id))

    return collection.to_dict()


# parse args
# todo
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--identifier", metavar="identifier", required=False,
                    help="identifier of a specific dataset to convert")
args = parser.parse_args()
matches = list()

try:
    # actual query
    if args.identifier is None:
        logging.info("no identifier")
        matches = search()
    else:
        logging.info("identifier {0}".format(args.identifier))
        collection = query_one(args.identifier)
        matches = [collection]
except Exception:
    logging.error("could not search or query")
    logging.error(traceback.format_exc())

# build output
current_script = Path(__file__).resolve()
main_dir = current_script.parents[3]
output_dir = os.path.join(main_dir, "data", "converted", "stac", "automatic")
Path(output_dir).mkdir(parents=True, exist_ok=True)
logging.info("saving into: {0}".format(output_dir))

# convert each
convert(output_dir, matches)

logging.info("done")
