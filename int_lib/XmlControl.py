"""
    VUT FIT IPP project 2
    IPPcode22 XML interpret
    Author: Samuel Šulo
"""

import re
import xml.etree.ElementTree as ET
from int_lib.Reports import Reports
from int_lib.Errors import Errors

# Loads and checks xml format in source file
class XmlControl:
    def __init__(self, source_file):
        self.__reports = Reports

        try:
            tree = ET.parse(source_file)
            self.root = tree.getroot()
        except:
            self.__reports.stderr("Wrong xml format.\n", Errors.WRONG_XML)

        try:
            self.__language = self.root.attrib['language']
        except:
            self.__reports.stderr("Wrong xml language format.\n", Errors.WRONG_XML)

        if self.__language != "IPPcode22":
            self.__reports.stderr("Wrong language.\n", Errors.WRONG_XML_STRUCTURE)

        # Instructions
        for child in self.root:
            if child.tag != 'instruction':
                self.__reports.stderr("Expected instruction.\n", Errors.WRONG_XML_STRUCTURE)

            if 'order' not in child.attrib or 'opcode' not in child.attrib or len(child.attrib) != 2:
                self.__reports.stderr("Wrong parameters in instruction {0}.\n".format(child.attrib), Errors.WRONG_XML_STRUCTURE)

            # Arguments
            for count, grandchild in enumerate(child, 1):
                if count > 3 or grandchild.tag != 'arg' + str(count):
                    self.__reports.stderr("Argument error in {0}: {1} of instruction: {2}\n".format(grandchild.tag, grandchild.attrib, child.attrib['opcode']), Errors.WRONG_XML_STRUCTURE)

                if 'type' not in grandchild.attrib or len(grandchild.attrib) != 1:
                    self.__reports.stderr("Argument attributes error in {0}: {1}\n".format(grandchild.tag, grandchild.attrib), Errors.WRONG_XML)

                # Checks if arguments value is correct according to type using regex
                if grandchild.attrib['type'] == 'int':
                    self.check_int(grandchild.text)
                elif grandchild.attrib['type'] == 'bool':
                    self.check_bool(grandchild.text)
                elif grandchild.attrib['type'] == 'string':
                    if grandchild.text is not None:
                        self.check_string(grandchild.text)
                elif grandchild.attrib['type'] == 'var':
                    self.check_var(grandchild.text)
                elif grandchild.attrib['type'] == 'label':
                    self.check_label(grandchild.text)
                elif grandchild.attrib['type'] == 'type':
                    self.check_type(grandchild.text)
                elif grandchild.attrib['type'] == 'nil':
                    continue
                else:
                    self.__reports.stderr("Wrong type.\n", Errors.WRONG_XML)

    def check_int(self, val):
        if not re.match(r'^(\+|\-)?\d+$', val):
            self.__reports.stderr("Wrong int value.\n", Errors.WRONG_XML_STRUCTURE)

    def check_bool(self, val):
        if val != 'true' and val != 'false':
            self.__reports.stderr("Not bool value.\n", Errors.WRONG_XML_STRUCTURE)

    def check_string(self, val):
        if not re.match(r'[^\\\s]|(\\\d{3})*', val):
            self.__reports.stderr("Wrong string syntax.\n", Errors.WRONG_XML_STRUCTURE)

    def check_var(self, val):
        if not re.match(r'^(LF|TF|GF)@[a-zA-Z_\-$&%*][a-zA-Z0-9_\-$&%*]*$', val):
            self.__reports.stderr("Wrong var syntax.\n", Errors.WRONG_XML_STRUCTURE)

    def check_label(self, val):
        if not re.match(r'^[a-zA-Z_\-$&%*][a-zA-Z0-9_\-$&%*]*$', val):
            self.__reports.stderr("Wrong label syntax.\n", Errors.WRONG_XML_STRUCTURE)

    def check_type(self, val):
        if not (val == 'int' or val == 'bool' or val == 'string'):
            self.__reports.stderr("Wrong type syntax.\n", Errors.WRONG_XML_STRUCTURE)