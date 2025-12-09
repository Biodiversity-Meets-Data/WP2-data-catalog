import json
import constants

"""this is deprecated"""
"""was parsing a local json payload downloaded from /collections endpoint"""


def parse_dataset(dataset):
    if dataset.get(constants.DATASET_ID) is None:
        raise KeyError("missing dataset identifier")

    dataset_id = dataset[constants.DATASET_ID]
    # print(dataset_id)
    disabled = is_disabled(dataset_id, dataset[constants.STATUS])

    return disabled


def is_disabled(dataset_id, status):
    disabled = False

    if status == "disabled":
        disabled = True
        print("dataset {0} disabled".format(dataset_id))

    return disabled


f = open("../../datasets.json")
datasets = json.loads(f.read())
print(len(datasets))
nbr_disabled = 0

for dataset in datasets:
    disabled = parse_dataset(dataset)

    if disabled:
        nbr_disabled = nbr_disabled +1

print("number of disabled dataset: {0}".format(nbr_disabled))
