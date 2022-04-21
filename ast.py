import os
import sys
import subprocess

text = open('filename', 'r').read()
lines = text.split('\n')

from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import math
import functools
from jinja2 import Environment, FileSystemLoader


class ConvertVisitor(object):

    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        ret = []
        for c in node.children():
            ret.append(self.visit(c))
        return ''.join(ret)


def getfilename(node):
    return node.__class__.__name__.lower() + '.txt'


def escape(s):
    if s.startswith('\\'):
        return s + ' '
    return s


def del_paren(s):
    if s.startswith('(') and s.endswith(')'):
        return s[1:-1]
    return s


def del_space(s):
    return s.replace(' ', '')


class ASTCodeGenerator(ConvertVisitor):

    def __init__(self, indentsize=2):
        self.env = Environment(loader=FileSystemLoader(DEFAULT_TEMPLATE_DIR))
        self.indent = functools.partial(indent, prefix=' ' * indentsize)
        self.template_cache = {}

    def get_template(self, filename):
        if filename in self.template_cache:
            return self.template_cache[filename]

        template = self.env.get_template(filename)
        self.template_cache[filename] = template
        return template

    def visit_Source(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'description': self.visit(node.description),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Description(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'definitions':
            [self.visit(definition) for definition in node.definitions],
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_ModuleDef(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        paramlist = self.indent(self.visit(
            node.paramlist)) if node.paramlist is not None else ''
        portlist = self.indent(self.visit(
            node.portlist)) if node.portlist is not None else ''
        template_dict = {
            'modulename':
            escape(node.name),
            'paramlist':
            paramlist,
            'portlist':
            portlist,
            'items': [self.indent(self.visit(item))
                      for item in node.items] if node.items else (),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Paramlist(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        params = [self.visit(param).replace(';', '') for param in node.params]
        template_dict = {
            'params': params,
            'len_params': len(params),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Portlist(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        ports = [self.visit(port) for port in node.ports]
        template_dict = {
            'ports': ports,
            'len_ports': len(ports),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Port(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.name),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Width(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'msb': del_space(del_paren(self.visit(node.msb))),
            'lsb': del_space(del_paren(self.visit(node.lsb))),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Length(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'msb': del_space(del_paren(self.visit(node.msb))),
            'lsb': del_space(del_paren(self.visit(node.lsb))),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Identifier(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.name),
            'scope': '' if node.scope is None else self.visit(node.scope),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Value(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'value': node.value,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Constant(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'value': node.value,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_IntConst(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'value': node.value,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_FloatConst(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'value': node.value,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_StringConst(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'value': node.value,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Variable(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name':
            escape(node.name),
            'width':
            '' if node.width is None else self.visit(node.width),
            'signed':
            node.signed,
            'dimensions':
            '' if node.dimensions is None else self.visit(node.dimensions),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Input(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name':
            escape(node.name),
            'width':
            '' if node.width is None else self.visit(node.width),
            'signed':
            node.signed,
            'dimensions':
            '' if node.dimensions is None else self.visit(node.dimensions),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Output(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name':
            escape(node.name),
            'width':
            '' if node.width is None else self.visit(node.width),
            'signed':
            node.signed,
            'dimensions':
            '' if node.dimensions is None else self.visit(node.dimensions),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Inout(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name':
            escape(node.name),
            'width':
            '' if node.width is None else self.visit(node.width),
            'signed':
            node.signed,
            'dimensions':
            '' if node.dimensions is None else self.visit(node.dimensions),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Tri(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name':
            escape(node.name),
            'width':
            '' if node.width is None else self.visit(node.width),
            'signed':
            node.signed,
            'dimensions':
            '' if node.dimensions is None else self.visit(node.dimensions),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Wire(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name':
            escape(node.name),
            'width':
            '' if node.width is None else self.visit(node.width),
            'signed':
            node.signed,
            'dimensions':
            '' if node.dimensions is None else self.visit(node.dimensions),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Reg(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name':
            escape(node.name),
            'width':
            '' if node.width is None else self.visit(node.width),
            'signed':
            node.signed,
            'dimensions':
            '' if node.dimensions is None else self.visit(node.dimensions),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Integer(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.name),
            'signed': node.signed,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Real(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.name),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Genvar(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.name),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Ioport(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'first':
            node.first.__class__.__name__.lower(),
            'second':
            ''
            if node.second is None else node.second.__class__.__name__.lower(),
            'name':
            escape(node.first.name),
            'width':
            '' if node.first.width is None else self.visit(node.first.width),
            'signed':
            node.first.signed
            or (node.second is not None and node.second.signed),
            'dimensions':
            '' if node.first.dimensions is None else self.visit(
                node.first.dimensions)
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Parameter(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        value = self.visit(node.value)
        template_dict = {
            'name':
            escape(node.name),
            'width':
            '' if node.width is None or
            (value.startswith('"') and value.endswith('"')) else self.visit(
                node.width),
            'value':
            value,
            'signed':
            node.signed,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Localparam(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        value = self.visit(node.value)
        template_dict = {
            'name':
            escape(node.name),
            'width':
            '' if node.width is None or
            (value.startswith('"') and value.endswith('"')) else self.visit(
                node.width),
            'value':
            value,
            'signed':
            node.signed,
        }
        rslt = template.render(template_dict)
        return rslt
