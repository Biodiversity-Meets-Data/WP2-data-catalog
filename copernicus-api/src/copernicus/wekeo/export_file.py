import logging
# to install metapype
# https://www.anaconda.com/docs/tools/working-with-conda/packages/pip-install
import metapype.eml.names as names
import metapype.eml.validate as validate
import metapype.eml.export
from metapype.model.node import Node
from metapype.eml.exceptions import MetapypeRuleError

eml = Node(names.EML)
eml.add_attribute('packageId', 'edi.23.1')
eml.add_attribute('system', 'metapype')

dataset = Node(names.DATASET, parent=eml)
eml.add_child(dataset)

title = Node(names.TITLE, parent=dataset)
title.content = 'Green sea turtle counts: Tortuga Island 20017'
dataset.add_child(title)

creator = Node(names.CREATOR, parent=dataset)
dataset.add_child(creator)

individualName_creator = Node(names.INDIVIDUALNAME, parent=creator)
creator.add_child(individualName_creator)

surName_creator = Node(names.SURNAME, parent=individualName_creator)
surName_creator.content = 'Gaucho'
individualName_creator.add_child(surName_creator)

contact = Node(names.CONTACT, parent=dataset)
dataset.add_child(contact)

individualName_contact = Node(names.INDIVIDUALNAME, parent=contact)
contact.add_child(individualName_contact)

surName_contact = Node(names.SURNAME, parent=individualName_contact)
surName_contact.content = 'Gaucho'
individualName_contact.add_child(surName_contact)

try:
    validate.tree(eml)
except MetapypeRuleError as e:
    logging.error(e)

xml_str = metapype.eml.export.to_xml(eml)
with open('../data/test_eml.xml', 'w') as f:
    f.write(xml_str)