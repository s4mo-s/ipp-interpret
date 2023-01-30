"""
    VUT FIT IPP project 2
    IPPcode22 XML interpret
    Author: Samuel Šulo
"""

import re
import sys
from int_lib.Errors import Errors
from int_lib.Reports import Reports
from int_lib.XmlControl import XmlControl
from int_lib.CommandLine import CommandLine

class Nil:
    pass

# Checks argument and gives it value and if its variable then frame too
class Argument:
    def __init__(self, arg):
        self.__reports = Reports
        self.frame = Center()
        self.type = arg.attrib['type']

        if arg.attrib['type'] == 'var':
            self.frame, self.name = arg.text.split('@')
            self.value = None

        elif arg.attrib['type'] == 'int':
            self.value = int(arg.text)
            self.frame = None
            self.name = None

        elif arg.attrib['type'] == 'bool':
            if arg.text == 'true':
                self.value = True
            elif arg.text == 'false':
                self.value = False
            self.frame = None
            self.name = None

        elif arg.attrib['type'] == 'string':
            if arg.text is None:
                self.value = ''
                self.frame = None
                self.name = None

            elif re.match(r'[^\\\s#]|(\\\d{3})*', arg.text):
                sequence = re.compile(r'(\\\d{3})', re.UNICODE)
                symbols = sequence.split(arg.text)
                self.value = ''

                for symb in symbols:
                    if sequence.match(symb):
                        symb = chr(int(symb[1:]))
                    self.value += symb

            else:
                self.value = arg.text
                self.frame = None
                self.name = None

        elif arg.attrib['type'] == 'nil':
            self.value = Nil()
            self.frame = None
            self.name = None

        elif arg.attrib['type'] == 'type' or arg.attrib['type'] == 'label':
            self.value = arg.text
            self.frame = None
            self.name = None


# Main class of interpret which controls everything
class Center:
    def __init__(self):
        self.commands = CommandLine(sys.argv[1:])
        self.__reports = Reports

        xml = XmlControl(self.commands.source_file)

        self.root = xml.root
        self.global_frame = {}
        self.local_frames = []
        self.tmp_frame = None
        self.data_stack = []
        self.call_stack = []
        self.labels = {}

        self.instruction_counter = 0
        self.order = {}
        self.__opcode = ''

        self.arg_cnt = 0
        self.arg1 = None
        self.arg2 = None
        self.arg3 = None

    # If opcode is equal instruction 'LABEL' then stores name of label with order number of instruction into dictionary
    def set_labels(self):
        try:
            for i in range(len(self.root)):
                if self.root[i].attrib['opcode'] == 'LABEL':
                    for child in self.root[i]:
                        if child.text not in self.labels:
                            self.labels.update({child.text: int(self.root[i].attrib['order'])})
                        else:
                            self.__reports.stderr("Label redefinition.\n", Errors.SEMANTIC_ERROR)

        except (ValueError, AttributeError, SyntaxError):
            self.__reports.stderr("Wrong XML.\n", Errors.WRONG_XML_STRUCTURE)

    # Defines variable on a given frame
    def define(self, name, frame):
        if frame == 'GF':
            if name not in self.global_frame.keys():
                self.global_frame[name] = None
            else:
                self.__reports.stderr("Var with name {0} already defined in global frame.\n".format(name), Errors.SEMANTIC_ERROR)
        elif frame == 'LF':
            if name not in self.get_local_frame().keys():
                self.get_local_frame()[name] = None
            else:
                self.__reports.stderr("Var with name {0} already defined in local frame.\n".format(name), Errors.SEMANTIC_ERROR)
        elif frame == 'TF':
            if name not in self.get_tmp_frame().keys():
                self.get_tmp_frame()[name] = None
            else:
                self.__reports.stderr("Var with name {0} already defined in temporary frame.\n".format(name), Errors.SEMANTIC_ERROR)

    # Sets values to defined variables
    def set_value(self, name, value, frame):
        if value is None:
            self.__reports.stderr("Value is missing.\n", Errors.NON_EXISTENT_VALUE)
        if frame == 'GF' and name in self.global_frame.keys():
            self.global_frame[name] = value
        elif frame == 'LF' and name in self.get_local_frame().keys():
            self.get_local_frame()[name] = value
        elif frame == 'TF' and name in self.get_tmp_frame().keys():
            self.get_tmp_frame()[name] = value
        else:
            self.__reports.stderr("Variable with name: {0} is missing.\n".format(name), Errors.NON_EXISTENT_VAR)

    # If it is a variable defined in certain frame then gets its value, otherwise return same argument value
    def get_value(self, arg):
        var_value = None
        if arg.type == 'var':
            if arg.frame == 'GF':
                try:
                    var_value = self.global_frame[arg.name]
                except:
                    self.__reports.stderr("Var with name: {0} non-exist in global frame.\n".format(arg.name), Errors.NON_EXISTENT_VAR)
            elif arg.frame == 'LF':
                if len(self.local_frames) == 0:
                    self.__reports.stderr("Local frame non-exist.\n", Errors.NON_EXISTENT_FRAME)
                try:
                    var_value = self.local_frames[len(self.local_frames) - 1][arg.name]
                except:
                    self.__reports.stderr("Var with name: {0} non-exist in local frame.\n".format(arg.name), Errors.NON_EXISTENT_VAR)
            elif arg.frame == 'TF':
                try:
                    var_value = self.get_tmp_frame()[arg.name]
                except Exception:
                    self.__reports.stderr("Var with name: {0} non-exist in local frame.\n".format(arg.name), Errors.NON_EXISTENT_VAR)
            else:
                self.__reports.stderr("Wrong frame type.\n", Errors.NON_EXISTENT_FRAME)

            return var_value
        else:
            return arg.value

    # Returns temporary frame
    def get_tmp_frame(self):
        if self.tmp_frame is not None:
            return self.tmp_frame
        else:
            self.__reports.stderr("There is no temporary frame.\n", Errors.NON_EXISTENT_FRAME)

    # Returns local frame
    def get_local_frame(self):
        try:
            return self.local_frames[-1]
        except:
            self.__reports.stderr("There is no local frame.\n", Errors.NON_EXISTENT_FRAME)

    def start(self):
        self.set_labels()

        self.instruction_counter = 1
        self.order = {}

        top = 0
        count = 0

        # Sets the instructions in the correct order
        for child in self.root:
            number = 0
            try:
                number = int(child.attrib['order'])
            except:
                self.__reports.stderr("Wrong order number.\n", Errors.WRONG_XML_STRUCTURE)

            if number < 1:
                self.__reports.stderr("Wrong order number.\n", Errors.WRONG_XML_STRUCTURE)
            if number > top:
                top = number
            if number not in self.order.keys():
                self.order.update({number: count})
                count += 1
            else:
                self.__reports.stderr("Order number already in dictionary.\n", Errors.WRONG_XML_STRUCTURE)

        # Loads instructions in ascending order
        while self.instruction_counter < (top + 1):
            try:
                instruction = self.order[self.instruction_counter]
            except:
                self.instruction_counter += 1
                continue

            self.exec(instruction)

    # Executes given instruction
    def exec(self, order):
        not_implemented_opcodes = ['CLEARS', 'ADDS', 'SUBS', 'MULS', 'IDIVS', 'LTS', 'GTS', 'EQS', 'ANDS', 'ORS',
                                   'NOTS', 'INT2CHARS', 'STRI2INTS', 'JUMPIFEQS', 'JUMPIFNEQS']

        self.arg_cnt = 0
        self.arg1 = None
        self.arg2 = None
        self.arg3 = None

        # Stores the opcode name
        try:
            self.__opcode = (self.root[order].attrib['opcode']).upper()
        except:
            self.__reports.stderr("Wrong Xml format.\n", Errors.WRONG_XML_STRUCTURE)

        # Counts how many arguments got given instruction
        for child in self.root[order]:
            self.arg_cnt += 1
            if self.arg_cnt == 1:
                self.arg1 = child
            elif self.arg_cnt == 2:
                self.arg2 = child
            elif self.arg_cnt == 3:
                self.arg3 = child

        # Copy value of second arg into first
        if self.__opcode == 'MOVE':
            self.instruction_counter += 1
            if self.arg_cnt != 2:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg2_val = self.get_value(arg2)

            if arg2_val is None:
                self.__reports.stderr("MOVE: arg without value.\n", Errors.NON_EXISTENT_VALUE)

            if arg2.type != 'label':
                self.set_value(arg1.name, arg2_val, arg1.frame)
            else:
                self.__reports.stderr("Can't moving label.\n", Errors.WRONG_XML_STRUCTURE)

        # Creates new tmp frame or override possible occurrence of current tmp frame with empty
        elif self.__opcode == 'CREATEFRAME':
            self.instruction_counter += 1
            if self.arg_cnt != 0:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            self.tmp_frame = {}

        # Moves tmp frame, if exists, on stack of local frames
        elif self.__opcode == 'PUSHFRAME':
            self.instruction_counter += 1
            if self.arg_cnt != 0:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            self.local_frames.append(self.get_tmp_frame())
            self.tmp_frame = None

        # Moves top local frame, if exists, from stack of local frames into tmp frame
        elif self.__opcode == 'POPFRAME':
            self.instruction_counter += 1

            if len(self.local_frames) != 0:
                self.tmp_frame = (self.local_frames[len(self.local_frames) - 1]).copy()
                del self.local_frames[len(self.local_frames) - 1]
            else:
                self.__reports.stderr("There is non-existent frame to pop.\n", Errors.NON_EXISTENT_FRAME)

        # Defines variable in a specific frame without initialization
        elif self.__opcode == 'DEFVAR':
            self.instruction_counter += 1
            if self.arg_cnt != 1:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            self.define(arg1.name, arg1.frame)

        # Jumps on specified label and stores incremented actual position
        elif self.__opcode == 'CALL':
            if self.arg_cnt != 1:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg1_val = self.get_value(arg1)

            try:
                jump = self.labels[arg1_val]
                self.call_stack.append(self.instruction_counter + 1)
                self.instruction_counter = jump
            except:
                self.__reports.stderr("Wrong call.\n", Errors.SEMANTIC_ERROR)

        # Takes out a position from stack of calls and jumps on that position through setting instruction counter
        elif self.__opcode == 'RETURN':
            try:
                self.instruction_counter = self.call_stack[len(self.call_stack) - 1]
                del self.call_stack[len(self.call_stack) - 1]
            except:
                self.__reports.stderr("There is no return.\n", Errors.NON_EXISTENT_VALUE)

        # Stores argument value on data stack
        elif self.__opcode == 'PUSHS':
            self.instruction_counter += 1
            if self.arg_cnt != 1:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg1_val = self.get_value(arg1)

            if arg1_val is None:
                self.__reports.stderr("arg is not defined.\n", Errors.NON_EXISTENT_VALUE)

            if arg1.type != 'label':
                self.data_stack.append(arg1_val)
            else:
                self.__reports.stderr("Arg of type 'label' cannot be pushed.\n", Errors.WRONG_XML_STRUCTURE)

        # Takes out a value from data stack, if is non-empty, and stores it in a variable
        elif self.__opcode == 'POPS':
            self.instruction_counter += 1
            if self.arg_cnt != 1:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)

            if len(self.data_stack) != 0:
                val = self.data_stack[len(self.data_stack) - 1]
                del self.data_stack[len(self.data_stack) - 1]
                self.set_value(arg1.name, val, arg1.frame)
            else:
                self.__reports.stderr("Data stack is empty.\n", Errors.NON_EXISTENT_VALUE)


        elif self.__opcode == 'ADD':
            self.instruction_counter += 1
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("Can't add args without value.\n", Errors.NON_EXISTENT_VALUE)

            if type(arg2_val) is int and type(arg3_val) is int:
                val = arg2_val + arg3_val
            else:
                self.__reports.stderr("Can't add non-int types.\n", Errors.BAD_OPERAND_TYPE)

            self.set_value(arg1.name, val, arg1.frame)

        elif self.__opcode == 'SUB':
            self.instruction_counter += 1
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("SUB: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if type(arg2_val) is int and type(arg3_val) is int:
                val = arg2_val - arg3_val
                self.set_value(arg1.name, val, arg1.frame)
            else:
                self.__reports.stderr("Can't sub non-int types.\n", Errors.BAD_OPERAND_TYPE)

        elif self.__opcode == 'MUL':
            self.instruction_counter += 1
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("MUL: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if (type(arg2_val) is int) and (type(arg3_val) is int):
                val = arg2_val * arg3_val
                self.set_value(arg1.name, val, arg1.frame)
            else:
                self.__reports.stderr("Can't multiply non-int types.\n", Errors.BAD_OPERAND_TYPE)

        elif self.__opcode == 'IDIV':
            self.instruction_counter += 1
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("IDIV: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if (type(arg2_val) is int) and (type(arg3_val) is int):
                if arg3_val == 0:
                    self.__reports.stderr("Can't divide by zero.\n", Errors.WRONG_OPERAND_VALUE)
                val = int(int(arg2_val) / int(arg3_val))
                self.set_value(arg1.name, val, arg1.frame)
            else:
                self.__reports.stderr("Can't divide non-int types.\n", Errors.BAD_OPERAND_TYPE)

        elif self.__opcode == 'LT':
            self.instruction_counter += 1
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("LT: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if isinstance(arg2_val, Nil) or isinstance(arg3_val, Nil):
                self.__reports.stderr("LT: args are nil.\n", Errors.BAD_OPERAND_TYPE)

            if type(arg2_val) != type(arg3_val):
                self.__reports.stderr("LT: args are not of the same type.\n", Errors.BAD_OPERAND_TYPE)

            if ((type(arg2_val) is int and type(arg3_val) is int) or
                (type(arg2_val) is str and type(arg3_val) is str) or
                (type(arg2_val) is bool and type(arg3_val) is bool)):

                val = arg2_val < arg3_val
                self.set_value(arg1.name, val, arg1.frame)

            else:
                self.__reports.stderr("LT: args are of the wrong type.\n", Errors.BAD_OPERAND_TYPE)

        elif self.__opcode == 'GT':
            self.instruction_counter += 1
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("GT: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if isinstance(arg2_val, Nil) or isinstance(arg3_val, Nil):
                self.__reports.stderr("LT: args are nil.\n", Errors.BAD_OPERAND_TYPE)

            if type(arg2_val) != type(arg3_val):
                self.__reports.stderr("GT: args are not of the same type.\n", Errors.BAD_OPERAND_TYPE)

            if ((type(arg2_val) is int and type(arg3_val) is int) or
                (type(arg2_val) is str and type(arg3_val) is str) or
                (type(arg2_val) is bool and type(arg3_val) is bool)):

                val = arg2_val > arg3_val
                self.set_value(arg1.name, val, arg1.frame)

            else:
                self.__reports.stderr("GT: args are of the wrong type.\n", Errors.BAD_OPERAND_TYPE)

        elif self.__opcode == 'EQ':
            self.instruction_counter += 1
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("EQ: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if not isinstance(arg2_val, Nil) and not isinstance(arg3_val, Nil):
                if type(arg2_val) != type(arg3_val):
                    self.__reports.stderr("EQ: args are not of the same type.\n", Errors.BAD_OPERAND_TYPE)

            else:
                if isinstance(arg2_val, Nil):
                    arg2_val = None
                if isinstance(arg3_val, Nil):
                    arg3_val = None

            val = arg2_val == arg3_val
            self.set_value(arg1.name, val, arg1.frame)

        elif self.__opcode == 'AND':
            self.instruction_counter += 1
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("AND: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if (type(arg2_val) is bool) and (type(arg3_val) is bool):
                if arg2_val and arg3_val:
                    self.set_value(arg1.name, 'true', arg1.frame)
                else:
                    self.set_value(arg1.name, 'false', arg1.frame)
            else:
                self.__reports.stderr("AND: args are not of the bool type.\n", Errors.BAD_OPERAND_TYPE)

        elif self.__opcode == 'OR':
            self.instruction_counter += 1
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("OR: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if (type(arg2_val) is bool) and (type(arg3_val) is bool):
                if arg2_val or arg3_val:
                    self.set_value(arg1.name, 'true', arg1.frame)
                else:
                    self.set_value(arg1.name, 'false', arg1.frame)
            else:
                self.__reports.stderr("OR: args are not of the bool type.\n", Errors.BAD_OPERAND_TYPE)

        elif self.__opcode == 'NOT':
            self.instruction_counter += 1
            if self.arg_cnt != 2:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg2_val = self.get_value(arg2)

            if arg2_val is None:
                self.__reports.stderr("NOT: arg without value.\n", Errors.NON_EXISTENT_VALUE)

            if type(arg2_val) is bool:
                if not arg2_val:
                    self.set_value(arg1.name, 'true', arg1.frame)
                else:
                    self.set_value(arg1.name, 'false', arg1.frame)
            else:
                self.__reports.stderr("NOT: arg is not of the bool type.\n", Errors.BAD_OPERAND_TYPE)

        elif self.__opcode == 'INT2CHAR':
            self.instruction_counter += 1
            if self.arg_cnt != 2:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg2_val = self.get_value(arg2)

            if arg2_val is None:
                self.__reports.stderr("INT2CHAR: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if type(arg2_val) is not int:
                self.__reports.stderr("INT2CHAR: arg is not of the int type.\n", Errors.BAD_OPERAND_TYPE)

            try:
                val = chr(arg2_val)
            except:
                self.__reports.stderr("INT2CHAR: arg has not valid ordinal value in Unicode.\n", Errors.STRING_ERROR)

            self.set_value(arg1.name, val, arg1.frame)

        elif self.__opcode == 'STRI2INT':
            self.instruction_counter += 1
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("STRI2INT: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if arg2_val == '':
                self.__reports.stderr("STRI2INT: arg is of bad type.\n", Errors.BAD_OPERAND_TYPE)

            if type(arg2_val) is not str:
                self.__reports.stderr("STRI2INT: arg is not of the string type.\n", Errors.BAD_OPERAND_TYPE)

            if type(arg3_val) is not int:
                self.__reports.stderr("STRI2INT: arg is not of the int type.\n", Errors.BAD_OPERAND_TYPE)

            if len(arg2_val) <= arg3_val or arg3_val < 0:
                self.__reports.stderr("STRI2INT: index is out of range.\n", Errors.STRING_ERROR)

            try:
                val = ord(arg2_val[arg3_val])
            except:
                self.__reports.stderr("STRI2INT: indexation is out of string.\n", Errors.STRING_ERROR)

            self.set_value(arg1.name, val, arg1.frame)

        elif self.__opcode == 'CONCAT':
            self.instruction_counter += 1
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("CONCAT: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if isinstance(arg2_val, Nil) or isinstance(arg3_val, Nil):
                self.__reports.stderr("CONCAT: arg is nil.\n", Errors.BAD_OPERAND_TYPE)

            if type(arg2_val) is str and type(arg3_val) is str:
                val = arg2_val + arg3_val
            elif arg3_val is None and type(arg2_val) is str:
                val = arg2_val
            elif arg2_val is None and type(arg3_val) is str:
                val = arg3_val
            else:
                self.__reports.stderr("CONCAT: args are of wrong type.\n", Errors.BAD_OPERAND_TYPE)
            self.set_value(arg1.name, val, arg1.frame)

        elif self.__opcode == 'STRLEN':
            self.instruction_counter += 1
            if self.arg_cnt != 2:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg2_val = self.get_value(arg2)

            if arg2_val is None:
                self.__reports.stderr("STRLEN: arg without value.\n", Errors.NON_EXISTENT_VALUE)
                if isinstance(arg2_val, Nil):
                    self.__reports.stderr("STRLEN: arg is nil.\n", Errors.BAD_OPERAND_TYPE)

            elif arg2_val == '':
                val = 0
                self.set_value(arg1.name, val, arg1.frame)

            elif type(arg2_val) is str:
                val = len(arg2_val)
                self.set_value(arg1.name, val, arg1.frame)
            else:
                self.__reports.stderr("STRLEN: arg is not of the string type.\n", Errors.BAD_OPERAND_TYPE)

        elif self.__opcode == 'GETCHAR':
            self.instruction_counter += 1
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("GETCHAR: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if isinstance(arg2_val, Nil):
                self.__reports.stderr("GETCAHR: arg is nil.\n", Errors.BAD_OPERAND_TYPE)

            if type(arg2_val) is not str:
                self.__reports.stderr("GETCHAR: arg is not of the string type.\n", Errors.BAD_OPERAND_TYPE)

            if type(arg3_val) is not int:
                self.__reports.stderr("GETCHAR: arg is not of the int type.\n", Errors.BAD_OPERAND_TYPE)

            if len(arg2_val) <= arg3_val or arg3_val < 0:
                self.__reports.stderr("GETCHAR: index is out of range.\n", Errors.STRING_ERROR)

            try:
                val = arg2_val[arg3_val]
            except:
                self.__reports.stderr("GETCHAR: indexation is out of string.\n", Errors.STRING_ERROR)

            self.set_value(arg1.name, val, arg1.frame)

        elif self.__opcode == 'SETCHAR':
            self.instruction_counter += 1
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg1_val = self.get_value(arg1)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg1_val is None or arg2_val is None or arg3_val is None:
                self.__reports.stderr("SETCHAR: empty strings.\n", Errors.NON_EXISTENT_VALUE)

            if type(arg1_val) != str or type(arg3_val) != str:
                self.__reports.stderr("SETCHAR: wrong type, should be str.\n", Errors.BAD_OPERAND_TYPE)

            if type(arg2_val) is not int:
                self.__reports.stderr("SETCHAR: wrong type, should be int.\n", Errors.BAD_OPERAND_TYPE)

            if arg1_val == '' or arg3_val == '':
                self.__reports.stderr("SETCHAR: empty char.\n", Errors.STRING_ERROR)

            if len(arg1_val) <= arg2_val or arg2_val < 0:
                self.__reports.stderr("GETCHAR: index is out of range.\n", Errors.STRING_ERROR)

            if type(arg3_val) is str:
                try:
                    val = list(arg1_val)
                    val[arg2_val] = arg3_val[0]
                    val = "".join(val)
                except:
                    self.__reports.stderr("SETCHAR: wrong strings.\n", Errors.STRING_ERROR)

            else:
                self.__reports.stderr("SETCHAR: wrong type, should be int.\n", Errors.BAD_OPERAND_TYPE)

            self.set_value(arg1.name, val, arg1.frame)

        elif self.__opcode == 'READ':
            self.instruction_counter += 1
            if self.arg_cnt != 2:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg2_val = self.get_value(arg2)

            if self.commands.input:
                line = self.commands.input_file.readline()
                try:
                    if line == '':
                        line = Nil()
                    else:
                        line = line.rstrip('\n')
                        if arg2_val == 'int':
                            if line.lstrip('-+').isdigit():
                                line = int(line)
                            else:
                                line = Nil()

                        elif arg2_val == 'string':
                            if type(line) is not str:
                                line = ''
                            else:
                                pass
                        elif arg2_val == 'bool':
                            line = line.lower()
                            if line == "true":
                                line = True
                            else:
                                line = False
                        else:
                            self.__reports.stderr("Wrong type.\n", Errors.BAD_OPERAND_TYPE)
                except:
                    if arg2_val == 'int':
                        line = 0
                    elif arg2_val == 'string':
                        line = ''
                    elif arg2_val == 'bool':
                        line = False
                    else:
                        self.__reports.stderr("Wrong type.\n", Errors.BAD_OPERAND_TYPE)

            else:
                line = input()
                if arg2_val == 'int':
                    if line.lstrip('-+').isdigit():
                        line = int(line)
                    else:
                        line = Nil()
                elif arg2_val == 'string':
                    if type(line) is not str:
                        line = ''
                    else:
                        pass
                elif arg2_val == 'bool':
                    line = line.lower()
                    if line == "true":
                        line = True
                    else:
                        line = False
                else:
                    self.__reports.stderr("Wrong type.\n", Errors.BAD_OPERAND_TYPE)

            self.set_value(arg1.name, line, arg1.frame)

        # Prints value of variable on standard output
        elif self.__opcode == 'WRITE':
            self.instruction_counter += 1
            if self.arg_cnt != 1:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg1_val = self.get_value(arg1)

            if type(arg1_val) == bool:
                if arg1_val:
                    arg1_val = 'true'
                else:
                    arg1_val = 'false'

            if isinstance(arg1_val, Nil):
                arg1_val = ''

            elif arg1_val is None:
                self.__reports.stderr("WRITE: arg without value.\n", Errors.NON_EXISTENT_VALUE)

            arg1_val = str(arg1_val)
            print(arg1_val, end='')

        # Gets type of symb and stores in variable
        elif self.__opcode == 'TYPE':
            self.instruction_counter += 1
            if self.arg_cnt != 2:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg2_val = self.get_value(arg2)

            if arg2_val == 'true':
                arg2_val = True
            elif arg2_val == 'false':
                arg2_val = False

            if type(arg2_val) is int:
                self.set_value(arg1.name, 'int', arg1.frame)
            elif type(arg2_val) is bool:
                self.set_value(arg1.name, 'bool', arg1.frame)
            elif type(arg2_val) is str:
                self.set_value(arg1.name, 'string', arg1.frame)
            elif isinstance(arg2_val, Nil):
                self.set_value(arg1.name, 'nil', arg1.frame)
            elif arg2_val is None:
                self.set_value(arg1.name, '', arg1.frame)
            else:
                self.__reports.stderr("Bad operand type.\n", Errors.BAD_OPERAND_TYPE)

        # Labels are already set so it only increments instruction counter
        elif self.__opcode == 'LABEL':
            self.instruction_counter += 1

        # Jumps on specified label
        elif self.__opcode == 'JUMP':
            if self.arg_cnt != 1:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg1_val = self.get_value(arg1)

            try:
                jump = self.labels[arg1_val]
                self.instruction_counter = int(jump)
            except:
                self.__reports.stderr("Wrong specified label.\n", Errors.SEMANTIC_ERROR)

        # Jumps if args are of same type and their values are equal
        elif self.__opcode == 'JUMPIFEQ':
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg1_val = self.get_value(arg1)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("JUMPIFEQ: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if not isinstance(arg2_val, Nil) and not isinstance(arg3_val, Nil):
                if type(arg2_val) != type(arg3_val):
                    self.__reports.stderr("EQ: args are not of the same type.\n", Errors.BAD_OPERAND_TYPE)

            if isinstance(arg2_val, Nil):
                arg2_val = None
            if isinstance(arg3_val, Nil):
                arg3_val = None

            try:
                self.labels[arg1_val]
            except:
                self.__reports.stderr("Wrong specified label.\n", Errors.SEMANTIC_ERROR)

            if arg2_val == arg3_val:
                jump = self.labels[arg1_val]
                self.instruction_counter = int(jump)
            else:
                self.instruction_counter += 1

        # Jumps if args are of same type and their values are not equal
        elif self.__opcode == 'JUMPIFNEQ':
            if self.arg_cnt != 3:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg2 = Argument(self.arg2)
            arg3 = Argument(self.arg3)
            arg1_val = self.get_value(arg1)
            arg2_val = self.get_value(arg2)
            arg3_val = self.get_value(arg3)

            if arg2_val is None or arg3_val is None:
                self.__reports.stderr("JUMPIFNEQ: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if not isinstance(arg2_val, Nil) and not isinstance(arg3_val, Nil):
                if type(arg2_val) != type(arg3_val):
                    self.__reports.stderr("EQ: args are not of the same type.\n", Errors.BAD_OPERAND_TYPE)

            if isinstance(arg2_val, Nil):
                arg2_val = None
            if isinstance(arg3_val, Nil):
                arg3_val = None

            try:
                self.labels[arg1_val]
            except:
                self.__reports.stderr("Wrong specified label.\n", Errors.SEMANTIC_ERROR)

            if arg2_val != arg3_val:
                jump = self.labels[arg1_val]
                self.instruction_counter = int(jump)
            else:
                self.instruction_counter += 1

        # Terminate code execution and return exit code with given value in range 0-49
        elif self.__opcode == 'EXIT':
            if self.arg_cnt != 1:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg1_val = self.get_value(arg1)

            if arg1_val is None:
                self.__reports.stderr("EXIT: args without value.\n", Errors.NON_EXISTENT_VALUE)

            if arg1.type != 'var' and arg1.type != 'int':
                self.__reports.stderr("Wrong exit types.\n", Errors.BAD_OPERAND_TYPE)

            if arg1_val == '' or type(arg1_val) != int:
                self.__reports.stderr("Wrong exit types.\n", Errors.BAD_OPERAND_TYPE)

            if arg1_val in range(0, 50):
                exit(int(arg1_val))
            else:
                self.__reports.stderr("Non-valid exit value.\n", Errors.WRONG_OPERAND_VALUE)

        # Prints value on stderr
        elif self.__opcode == 'DPRINT':
            self.instruction_counter += 1
            if self.arg_cnt != 1:
                self.__reports.stderr("Bad quantity of args.\n", Errors.WRONG_XML_STRUCTURE)

            arg1 = Argument(self.arg1)
            arg1_val = self.get_value(arg1)
            sys.stderr.write(str(arg1_val))

        # Prints interpret actual status
        elif self.__opcode == 'BREAK':
            sys.stderr.write("In order {0}. instruction, with order number: {1}\n".format(self.order[self.instruction_counter] + 1, self.instruction_counter))
            sys.stderr.write("{0}. instructions has been already executed\n".format(self.order[self.instruction_counter]))
            sys.stderr.write("Current content of global frame: {0}\n".format(self.global_frame))
            sys.stderr.write("Current content of local frames: {0}\n".format(self.local_frames))
            sys.stderr.write("Current content of temporary frame: {0}\n".format(self.tmp_frame))

            self.instruction_counter += 1

        elif self.__opcode in not_implemented_opcodes:
            self.__reports.stderr("Opcode is not implemented.\n", Errors.NOT_IMPLEMENTED_OPCODE)

        else:
            self.__reports.stderr("Unknown opcode.\n", Errors.WRONG_XML_STRUCTURE)
