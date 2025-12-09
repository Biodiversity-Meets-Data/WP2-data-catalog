import json


def starts_with_value(wrapper, key, target):
    if key in wrapper:
        for entry in wrapper[key]:
            if entry.startswith(target):
                return True

    return False


def is_platform(wrapper, targets):
    key = "platform"

    for target in targets:
        if starts_with_value(wrapper, key, target):
            return True

    return False


def is_level(wrapper, target):
    key = "processing:level"

    return starts_with_value(wrapper, key, target)


f = open("../../data/stac_collections.json")
raw = json.loads(f.read())
collections = raw["collections"]
matches = []

for index, collection in enumerate(collections):
    # print("collection " + str(index))
    platform = "sentinel-2"
    platforms = ["sentinel-2", "sentinel-3", "sentinel-5p"]
    level = "L2"

    if is_platform(collection["summaries"], platforms):
        print("platform found for " + collection["id"] + " at index " + str(index))

        if is_level(collection["summaries"], level):
            print("level [" + level + "] found for " + collection["id"] + " at index " + str(index))
            matches.append(collection["id"])

matches.sort()
print(len(matches))
# print(json.dumps(matches, indent=4))
# print(json.dumps(collections, indent=4))

for match in matches:
    print(match)
