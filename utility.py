from __future__ import absolute_import
from __future__ import print_function
import sys
import os

def getIdentifiers(node):
    v = IdentifierVisitor()
    v.visit(node)
    ids = v.getIdentifiers()
    return ids


class IdentifierVisitor(NodeVisitor):
    def __init__(self):
        self.identifiers = []

    def getIdentifiers(self):
        return tuple(self.identifiers)

    def reset(self):
        self.identifiers = []

    def visit_Identifier(self, node):
        self.identifiers.append(node.name)

def infer(op, node):
    val = node.value
    funcname = 'op_' + op
    opfunc = getattr(this, funcname, op_None)
    return opfunc(val)

class InferredValue(object):
    def __init__(self, minval, maxval, inv=False):
        self.minval = minval
        self.maxval = maxval
        self.inv = inv

    def invert(self):
        self.inv = not self.inv



