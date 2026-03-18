from owslib.csw import CatalogueServiceWeb
from owslib.fes import PropertyIsEqualTo, PropertyIsLike
from pprint import pprint
import json


def convert(data):
    print("transform from xml to xml")
    # TODO


csw = CatalogueServiceWeb('https://emodnet.ec.europa.eu/geonetwork/emodnet/eng/csw')

# print(csw.identification.type)
# print(csw.identification.title)
# print(csw.identification.version)
# print([op.name for op in csw.operations])
#
# records = csw.get_operation_by_name("GetRecords").parameters
# print("GetRecords :")
# print(json.dumps(records, indent=4))
#
# csw.getdomain('GetRecords.CONSTRAINTLANGUAGE')
# constraint = csw.results
# print(json.dumps(constraint, indent=4))

anytext_query = PropertyIsEqualTo('apiso:Title', 'coastal')
csw.getrecords2(constraints=[anytext_query], maxrecords=1, esn='full', outputschema='http://www.isotc211.org/2005/gmd')
# csw.getrecords2(constraints=[anytext_query], maxrecords=1, esn='full')
# csw.getrecords2(constraints=[anytext_query], maxrecords=1)
print(csw.results)

for rec in csw.records:
    print(rec)
    record = csw.records[rec]
    # pprint(vars(record.identification[0]))
    # pprint(vars(record))
    print(record.xml)
    # print(type(record))
    # print(record)
    # print(json.dumps(record, indent=4))
    # print(type(record.identification))
    # print(len(record.identification))
    # print(type(record.identification[0]))
    # print(json.dumps(record.identification[0]))
    # print(csw.records[rec].identification[0].title)
    # print(csw.records[rec].identification[0].abstract)
    print("----")

    # for resource in record.distribution.online:
    #     print('Description: ', resource.description)
    #     print('Protocol: ', resource.protocol)
    #     print('URL: ', resource.url)
    #     print("---")
