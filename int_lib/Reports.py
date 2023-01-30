"""
    VUT FIT IPP project 2
    IPPcode22 XML interpret
    Author: Samuel Šulo
"""

import sys

class Reports:
    @classmethod
    def help(self):
        sys.stdout.write("--source=file -> input file with XML representation of source code.\n"
                         "--input=file  -> file with inputs for interpretation specified source code.\n")

    @classmethod
    def stderr(self, message, exit_code):
        sys.stderr.write(message)
        exit(exit_code)
