from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import pathlib
from ply.yacc import yacc
import tempfile
import subprocess


class Node(object):

    def child_obj(self):
        pass

    def base(self, buf=sys.stdout, offset=0, attrnames=False, showlineno=True):
        indent = 2
        lead = ' ' * offset

        buf.write(lead + self.__class__.__name__ + ': ')

        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self, n)) for n in self.attr_names]
                attrstr = ', '.join('%s=%s' % (n, v) for (n, v) in nvlist)
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)

        if showlineno:
            buf.write(' (at %s)' % self.lineno)

        buf.write('\n')

        for c in self.child_obj():
            c.base(buf, offset + indent, attrnames, showlineno)


class Source(Node):
    attr_names = ('name', )

    def __init__(self, name, description, lineno=0):
        self.lineno = lineno
        self.name = name
        self.description = description

    def child_obj(self):
        nodelist = []
        if self.description:
            nodelist.append(self.description)
        return tuple(nodelist)


class ModuleDef(Node):
    attr_names = ('name', )

    def __init__(self,
                 name,
                 paramlist,
                 portlist,
                 items,
                 default_nettype='wire',
                 lineno=0):
        self.lineno = lineno
        self.name = name
        self.paramlist = paramlist
        self.portlist = portlist
        self.items = items
        self.default_nettype = default_nettype

    def child_obj(self):
        nodelist = []
        if self.paramlist:
            nodelist.append(self.paramlist)
        if self.portlist:
            nodelist.append(self.portlist)
        if self.items:
            nodelist.extend(self.items)
        return tuple(nodelist)


class Paramlist(Node):
    attr_names = ()

    def __init__(self, params, lineno=0):
        self.lineno = lineno
        self.params = params

    def child_obj(self):
        nodelist = []
        if self.params:
            nodelist.extend(self.params)
        return tuple(nodelist)


class Portlist(Node):
    attr_names = ()

    def __init__(self, ports, lineno=0):
        self.lineno = lineno
        self.ports = ports

    def child_obj(self):
        nodelist = []
        if self.ports:
            nodelist.extend(self.ports)
        return tuple(nodelist)


class Port(Node):
    attr_names = (
        'name',
        'type',
    )

    def __init__(self, name, width, dimensions, type, lineno=0):
        self.lineno = lineno
        self.name = name
        self.width = width
        self.dimensions = dimensions
        self.type = type

    def child_obj(self):
        nodelist = []
        if self.width:
            nodelist.append(self.width)
        return tuple(nodelist)


class Identifier(Node):
    attr_names = ('name', )

    def __init__(self, name, scope=None, lineno=0):
        self.lineno = lineno
        self.name = name
        self.scope = scope

    def child_obj(self):
        nodelist = []
        if self.scope:
            nodelist.append(self.scope)
        return tuple(nodelist)


class Value(Node):
    attr_names = ()

    def __init__(self, value, lineno=0):
        self.lineno = lineno
        self.value = value

    def child_obj(self):
        nodelist = []
        if self.value:
            nodelist.append(self.value)
        return tuple(nodelist)


class Constant(Value):
    attr_names = ('value', )

    def __init__(self, value, lineno=0):
        self.lineno = lineno
        self.value = value

    def child_obj(self):
        nodelist = []
        return tuple(nodelist)


class Variable(Value):
    attr_names = ('name', 'signed')

    def __init__(self,
                 name,
                 width=None,
                 signed=False,
                 dimensions=None,
                 value=None,
                 lineno=0):
        self.lineno = lineno
        self.name = name
        self.width = width
        self.signed = signed
        self.dimensions = dimensions
        self.value = value

    def child_obj(self):
        nodelist = []
        if self.width:
            nodelist.append(self.width)
        if self.dimensions:
            nodelist.append(self.dimensions)
        if self.value:
            nodelist.append(self.value)
        return tuple(nodelist)


class Ioport(Node):
    attr_names = ()

    def __init__(self, first, second=None, lineno=0):
        self.lineno = lineno
        self.first = first
        self.second = second

    def child_obj(self):
        nodelist = []
        if self.first:
            nodelist.append(self.first)
        if self.second:
            nodelist.append(self.second)
        return tuple(nodelist)


class Parameter(Node):
    attr_names = ('name', 'signed')

    def __init__(self, name, value, width=None, signed=False, lineno=0):
        self.lineno = lineno
        self.name = name
        self.value = value
        self.width = width
        self.signed = signed
        self.dimensions = None

    def child_obj(self):
        nodelist = []
        if self.value:
            nodelist.append(self.value)
        if self.width:
            nodelist.append(self.width)
        return tuple(nodelist)


class Localparam(Parameter):
    pass


class Pointer(Node):
    attr_names = ()

    def __init__(self, var, ptr, lineno=0):
        self.lineno = lineno
        self.var = var
        self.ptr = ptr

    def child_obj(self):
        nodelist = []
        if self.var:
            nodelist.append(self.var)
        if self.ptr:
            nodelist.append(self.ptr)
        return tuple(nodelist)


class Operator(Node):
    attr_names = ()

    def __init__(self, left, right, lineno=0):
        self.lineno = lineno
        self.left = left
        self.right = right

    def child_obj(self):
        nodelist = []
        if self.left:
            nodelist.append(self.left)
        if self.right:
            nodelist.append(self.right)
        return tuple(nodelist)

    def __repr__(self):
        ret = '(' + self.__class__.__name__
        for c in self.child_obj():
            ret += ' ' + c.__repr__()
        ret += ')'
        return ret


class UnaryOperator(Operator):
    attr_names = ()

    def __init__(self, right, lineno=0):
        self.lineno = lineno
        self.right = right

    def child_obj(self):
        nodelist = []
        if self.right:
            nodelist.append(self.right)
        return tuple(nodelist)


class Assign(Node):
    attr_names = ()

    def __init__(self, left, right, ldelay=None, rdelay=None, lineno=0):
        self.lineno = lineno
        self.left = left
        self.right = right
        self.ldelay = ldelay
        self.rdelay = rdelay

    def child_obj(self):
        nodelist = []
        if self.left:
            nodelist.append(self.left)
        if self.right:
            nodelist.append(self.right)
        if self.ldelay:
            nodelist.append(self.ldelay)
        if self.rdelay:
            nodelist.append(self.rdelay)
        return tuple(nodelist)


class Always(Node):
    attr_names = ()

    def __init__(self, sens_list, statement, lineno=0):
        self.lineno = lineno
        self.sens_list = sens_list
        self.statement = statement

    def child_obj(self):
        nodelist = []
        if self.sens_list:
            nodelist.append(self.sens_list)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)


class Substitution(Node):
    attr_names = ()

    def __init__(self, left, right, ldelay=None, rdelay=None, lineno=0):
        self.lineno = lineno
        self.left = left
        self.right = right
        self.ldelay = ldelay
        self.rdelay = rdelay

    def child_obj(self):
        nodelist = []
        if self.left:
            nodelist.append(self.left)
        if self.right:
            nodelist.append(self.right)
        if self.ldelay:
            nodelist.append(self.ldelay)
        if self.rdelay:
            nodelist.append(self.rdelay)
        return tuple(nodelist)


class IfStatement(Node):
    attr_names = ()

    def __init__(self, cond, true_statement, false_statement, lineno=0):
        self.lineno = lineno
        self.cond = cond
        self.true_statement = true_statement
        self.false_statement = false_statement

    def child_obj(self):
        nodelist = []
        if self.cond:
            nodelist.append(self.cond)
        if self.true_statement:
            nodelist.append(self.true_statement)
        if self.false_statement:
            nodelist.append(self.false_statement)
        return tuple(nodelist)


class ForStatement(Node):
    attr_names = ()

    def __init__(self, pre, cond, post, statement, lineno=0):
        self.lineno = lineno
        self.pre = pre
        self.cond = cond
        self.post = post
        self.statement = statement

    def child_obj(self):
        nodelist = []
        if self.pre:
            nodelist.append(self.pre)
        if self.cond:
            nodelist.append(self.cond)
        if self.post:
            nodelist.append(self.post)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)


class WhileStatement(Node):
    attr_names = ()

    def __init__(self, cond, statement, lineno=0):
        self.lineno = lineno
        self.cond = cond
        self.statement = statement

    def child_obj(self):
        nodelist = []
        if self.cond:
            nodelist.append(self.cond)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)


class CaseStatement(Node):
    attr_names = ()

    def __init__(self, comp, caselist, lineno=0):
        self.lineno = lineno
        self.comp = comp
        self.caselist = caselist

    def child_obj(self):
        nodelist = []
        if self.comp:
            nodelist.append(self.comp)
        if self.caselist:
            nodelist.extend(self.caselist)
        return tuple(nodelist)


class Case(Node):
    attr_names = ()

    def __init__(self, cond, statement, lineno=0):
        self.lineno = lineno
        self.cond = cond
        self.statement = statement

    def child_obj(self):
        nodelist = []
        if self.cond:
            nodelist.extend(self.cond)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)


class Block(Node):
    attr_names = ('scope', )

    def __init__(self, statements, scope=None, lineno=0):
        self.lineno = lineno
        self.statements = statements
        self.scope = scope

    def child_obj(self):
        nodelist = []
        if self.statements:
            nodelist.extend(self.statements)
        return tuple(nodelist)


class Initial(Node):
    attr_names = ()

    def __init__(self, statement, lineno=0):
        self.lineno = lineno
        self.statement = statement

    def child_obj(self):
        nodelist = []
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)


class Instance(Node):
    attr_names = ('name', 'module')

    def __init__(self,
                 module,
                 name,
                 portlist,
                 parameterlist,
                 array=None,
                 lineno=0):
        self.lineno = lineno
        self.module = module
        self.name = name
        self.portlist = portlist
        self.parameterlist = parameterlist
        self.array = array

    def child_obj(self):
        nodelist = []
        if self.array:
            nodelist.append(self.array)
        if self.parameterlist:
            nodelist.extend(self.parameterlist)
        if self.portlist:
            nodelist.extend(self.portlist)
        return tuple(nodelist)


class Verilogfile(object):

    def __init__(self, file, outputfile='pp.out', include=None, define=None):

        if not isinstance(file, (tuple, list)):
            file = list(file)
        self.temp_files_paths = []
        self.file = []

        for source in file:
            if not os.path.isfile(source):
                temp_fd, temp_path = tempfile.mkstemp(prefix="pyverilog_temp_",
                                                      suffix=".v")
                with open(temp_fd, 'w') as f:
                    f.write(source)

                self.temp_files_paths.append(temp_path)

            else:
                self.file.append(source)

        self.file += self.temp_files_paths

        iverilog = os.environ.get('PYVERILOG_IVERILOG')
        if iverilog is None:
            iverilog = 'iverilog'

        if include is None:
            include = ()

        if define is None:
            define = ()

        self.iv = [iverilog]

        for inc in include:
            self.iv.append('-I')
            self.iv.append(inc)

        for dfn in define:
            self.iv.append('-D')
            self.iv.append(dfn)


def build(self, **kwargs):
    self.lexer = lex(object=self, **kwargs)


def input(self, data):
    self.lexer.input(data)


def token(self):
    return self.lexer.token()


keywords = (
    'MODULE',
    'ENDMODULE',
    'BEGIN',
    'END',
    'GENERATE',
    'ENDGENERATE',
    'GENVAR',
    'FUNCTION',
    'ENDFUNCTION',
    'TASK',
    'ENDTASK',
    'INPUT',
    'INOUT',
    'OUTPUT',
    'TRI',
    'REG',
    'LOGIC',
    'WIRE',
    'INTEGER',
    'REAL',
    'SIGNED',
    'PARAMETER',
    'LOCALPARAM',
    'SUPPLY0',
    'SUPPLY1',
    'ASSIGN',
    'ALWAYS',
    'ALWAYS_FF',
    'ALWAYS_COMB',
    'ALWAYS_LATCH',
    'SENS_OR',
    'POSEDGE',
    'NEGEDGE',
    'INITIAL',
    'IF',
    'ELSE',
    'FOR',
    'WHILE',
    'CASE',
    'CASEX',
    'CASEZ',
    'UNIQUE',
    'ENDCASE',
    'DEFAULT',
    'WAIT',
    'FOREVER',
    'DISABLE',
    'FORK',
    'JOIN',
)

reserved = {}
for keyword in keywords:
    if keyword == 'SENS_OR':
        reserved['or'] = keyword
    else:
        reserved[keyword.lower()] = keyword

operators = (
    'PLUS',
    'MINUS',
    'POWER',
    'TIMES',
    'DIVIDE',
    'MOD',
    'NOT',
    'OR',
    'NOR',
    'AND',
    'NAND',
    'XOR',
    'XNOR',
    'LOR',
    'LAND',
    'LNOT',
    'LSHIFTA',
    'RSHIFTA',
    'LSHIFT',
    'RSHIFT',
    'LT',
    'GT',
    'LE',
    'GE',
    'EQ',
    'NE',
    'EQL',
    'NEL',
    'COND',  # ?
    'EQUALS',
)

tokens = keywords + operators + (
    'ID',
    'AT',
    'COMMA',
    'COLON',
    'SEMICOLON',
    'DOT',
    'PLUSCOLON',
    'MINUSCOLON',
    'FLOATNUMBER',
    'STRING_LITERAL',
    'INTNUMBER_DEC',
    'SIGNED_INTNUMBER_DEC',
    'INTNUMBER_HEX',
    'SIGNED_INTNUMBER_HEX',
    'INTNUMBER_OCT',
    'SIGNED_INTNUMBER_OCT',
    'INTNUMBER_BIN',
    'SIGNED_INTNUMBER_BIN',
    'LPAREN',
    'RPAREN',
    'LBRACKET',
    'RBRACKET',
    'LBRACE',
    'RBRACE',
    'DELAY',
    'DOLLER',
)

skipped = (
    'COMMENTOUT',
    'LINECOMMENT',
    'DIRECTIVE',
)

t_ignore = ' \t'
directive = r"""\`.*?\n"""

linecomment = r"""//.*?\n"""
commentout = r"""/\*(.|\n)*?\*/"""
t_LOR = r'\|\|'
t_LAND = r'\&\&'

t_NOR = r'~\|'
t_NAND = r'~\&'
t_XNOR = r'~\^'
t_OR = r'\|'
t_AND = r'\&'
t_XOR = r'\^'
t_LNOT = r'!'
t_NOT = r'~'

t_LSHIFTA = r'<<<'
t_RSHIFTA = r'>>>'
t_LSHIFT = r'<<'
t_RSHIFT = r'>>'

t_EQL = r'==='
t_NEL = r'!=='
t_EQ = r'=='
t_NE = r'!='

t_LE = r'<='
t_GE = r'>='
t_LT = r'<'
t_GT = r'>'

t_POWER = r'\*\*'
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'

t_COND = r'\?'
t_EQUALS = r'='

t_PLUSCOLON = r'\+:'
t_MINUSCOLON = r'-:'

t_AT = r'@'
t_COMMA = r','
t_SEMICOLON = r';'
t_COLON = r':'
t_DOT = r'\.'

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LBRACE = r'\{'
t_RBRACE = r'\}'

t_DELAY = r'\#'
t_DOLLER = r'\$'

bin_number = '[0-9]*\'[bB][0-1xXzZ?][0-1xXzZ?_]*'
signed_bin_number = '[0-9]*\'[sS][bB][0-1xZzZ?][0-1xXzZ?_]*'
octal_number = '[0-9]*\'[oO][0-7xXzZ?][0-7xXzZ?_]*'
signed_octal_number = '[0-9]*\'[sS][oO][0-7xXzZ?][0-7xXzZ?_]*'
hex_number = '[0-9]*\'[hH][0-9a-fA-FxXzZ?][0-9a-fA-FxXzZ?_]*'
signed_hex_number = '[0-9]*\'[sS][hH][0-9a-fA-FxXzZ?][0-9a-fA-FxXzZ?_]*'

decimal_number = '([0-9]*\'[dD][0-9xXzZ?][0-9xXzZ?_]*)|([0-9][0-9_]*)'
signed_decimal_number = '[0-9]*\'[sS][dD][0-9xXzZ?][0-9xXzZ?_]*'

exponent_part = r"""([eE][-+]?[0-9]+)"""
fractional_constant = r"""([0-9]*\.[0-9]+)|([0-9]+\.)"""
float_number = '((((' + fractional_constant + ')' + \
    exponent_part + '?)|([0-9]+' + exponent_part + ')))'

simple_escape = r"""([a-zA-Z\\?'"])"""
octal_escape = r"""([0-7]{1,3})"""
hex_escape = r"""(x[0-9a-fA-F]+)"""
escape_sequence = r"""(\\(""" + simple_escape + '|' + octal_escape + '|' + hex_escape + '))'
string_char = r"""([^"\\\n]|""" + escape_sequence + ')'
string_literal = '"' + string_char + '*"'

identifier = r"""(([a-zA-Z_])([a-zA-Z_0-9$])*)|((\\\S)(\S)*)"""


def preprocess(file, output='preprocess.output', include=None, define=None):
    pre = Verilogfile(file, output, include, define)
    pre.preprocess()
    text = open(output).read()
    os.remove(output)
    return text


def verilogparser(object):

    def preprocess(self):
        self.file.preprocess()
        text = open(self.preprocess_output).read()
        os.remove(self.preprocess_output)
        return text

    def parse(self, preprocess_output='preprocess.output', debug=0):
        text = self.preprocess()
        ast = self.parser.parse(text, debug=debug)
        self.main_direct = self.parser.get_main_direct()
        return ast

    def get_main_direct(self):
        return self.main_direct


def parse(file,
          preprocess_include=None,
          preprocess_define=None,
          outputdir=".",
          debug=True):
    codeparser = verilogparser(file,
                               preprocess_include=preprocess_include,
                               preprocess_define=preprocess_define,
                               outputdir=outputdir,
                               debug=debug)
    ast = codeparser.parse()
    main_direct = codeparser.get_main_direct()
    return ast,
