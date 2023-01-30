"""
    VUT FIT IPP project 2
    IPPcode22 XML interpret
    Author: Samuel Šulo
"""

import sys
import os
from int_lib.Errors import Errors
from int_lib.Reports import Reports

# Parses args in command line
class CommandLine:
    def __init__(self, args):
        self.__reports = Reports

        # Check how many arguments are in command line
        if len(args) < 1 or len(args) > 3:
            self.__reports.stderr("Bad quantity of arguments.\n", Errors.WRONG_PARAMETER)

        if "--help" in args:
            if len(args) == 1:
                self.__reports.help()
                sys.exit(0)
            else:
                self.__reports.stderr("--help cannot be combined with other arguments.\n", Errors.WRONG_PARAMETER)

        self.input = False
        self.source = False

        # Check source and input files and store them if exists
        for argument in args:
            if "--input=" in argument:
                if not self.input:
                    argument_list = argument.split('=')
                    self.input_file = argument_list[1]
                    self.input = True
                else:
                    self.__reports.stderr("Same argument was entered.\n", Errors.WRONG_PARAMETER)

            elif "--source=" in argument:
                if not self.source:
                    argument_list = argument.split('=')
                    self.source_file = argument_list[1]
                    self.source = True
                else:
                    self.__reports.stderr("Same argument was entered.\n", Errors.WRONG_PARAMETER)

            else:
                self.__reports.stderr("At least one argument has to be entered.\n", Errors.WRONG_PARAMETER)

        # Check if input file exists, if not then stores user input
        if self.input:
            if not os.path.isfile(self.input_file):
                self.__reports.stderr("Error while opening input file.\n", Errors.INPUT_FILE_ERROR)
            self.input_file = open(self.input_file)
        else:
            self.input_file = sys.stdin

        # Check if source file exists
        if self.source:
            if not os.path.isfile(self.source_file):
                self.__reports.stderr("Error while opening source file.\n", Errors.INPUT_FILE_ERROR)
        else:
            self.__reports.stderr("There is no source file.\n", Errors.WRONG_PARAMETER)
