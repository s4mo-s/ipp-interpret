"""
    VUT FIT IPP project 2
    IPPcode22 XML interpret
    Author: Samuel Šulo
"""

class Errors:
    WRONG_PARAMETER = 10
    INPUT_FILE_ERROR = 11
    OUTPUT_FILE_ERROR = 12

    WRONG_XML = 31
    WRONG_XML_STRUCTURE = 32

    SEMANTIC_ERROR = 52
    BAD_OPERAND_TYPE = 53
    NON_EXISTENT_VAR = 54
    NON_EXISTENT_FRAME = 55
    NON_EXISTENT_VALUE = 56
    WRONG_OPERAND_VALUE = 57
    STRING_ERROR = 58

    # my error code for non-implemented opcodes
    NOT_IMPLEMENTED_OPCODE = 99
