
class VerilogDataflowAnalyzer(VerilogCodeParser):
    def __init__(self, filelist, topmodule='TOP', noreorder=False, nobind=False,
                 preprocess_include=None,
                 preprocess_define=None):
        self.topmodule = topmodule
        self.terms = {}
        self.binddict = {}
        self.frametable = None
        files = filelist if isinstance(filelist, tuple) or isinstance(
            filelist, list) else [filelist]
        VerilogCodeParser.__init__(self, files,
                                   preprocess_include=preprocess_include,
                                   preprocess_define=preprocess_define)
        self.noreorder = noreorder
        self.nobind = nobind

    def generate(self):
        ast = self.parse()

        module_visitor = ModuleVisitor()
        module_visitor.visit(ast)
        modulenames = module_visitor.get_modulenames()
        moduleinfotable = module_visitor.get_moduleinfotable()

        signal_visitor = SignalVisitor(moduleinfotable, self.topmodule)
        signal_visitor.start_visit()
        frametable = signal_visitor.getFrameTable()

        if self.nobind:
            self.frametable = frametable
            return

        bind_visitor = BindVisitor(moduleinfotable, self.topmodule, frametable,
                                   noreorder=self.noreorder)

        bind_visitor.start_visit()
        dataflow = bind_visitor.getDataflows()

        self.frametable = bind_visitor.getFrameTable()
        self.terms = dataflow.getTerms()
        self.binddict = dataflow.getBinddict()



class VerilogOptimizer(object):
    default_width = 32
    compare_ops = ('LessThan', 'GreaterThan', 'LassEq', 'GreaterEq', 'Eq', 'NotEq', 'Eql', 'NotEql')

    def __init__(self, terms, constlist=None, default_width=32, level=2):
        self.terms = terms
        self.constlist = constlist if constlist is not None else {}
        self.default_width = default_width
        self.level = level

    def setConstant(self, name, value):
        self.constlist[name] = value

    def resetConstant(self, name):
        if name in self.constlist:
            del self.constlist[name]

    def getConstant(self, name):
        if not name in self.constlist:
            raise verror.DefinitionError('constant value not found: %s' % str(name))
        return self.constlist[name]

    def hasConstant(self, name):
        return name in self.constlist

    def getConstlist(self):
        return self.constlist

    def setTerm(self, name, term):
        self.terms[name] = term

    def getTerm(self, name):
        return self.terms[name]

    def hasTerm(self, name):
        return name in self.terms

    def optimize(self, tree):
        t = tree
        for i in range(self.level):
            t = self.optimizeConstant(t)
            t = self.optimizeHierarchy(t)
        return t

    def optimizeConstant(self, tree):
        if tree is None:
            return None
        if isinstance(tree, DFBranch):
            condnode = self.optimizeConstant(tree.condnode)
            truenode = self.optimizeConstant(tree.truenode)
            falsenode = self.optimizeConstant(tree.falsenode)
            if isinstance(condnode, DFEvalValue):
                if self.isCondTrue(condnode):
                    return truenode
                return falsenode
            return DFBranch(condnode, truenode, falsenode)

        if isinstance(tree, DFEvalValue):
            return tree
        if isinstance(tree, DFUndefined):
            return tree
        if isinstance(tree, DFHighImpedance):
            return tree
        if isinstance(tree, DFDelay):
            raise FormatError('Can not evaluate and optimize a DFDelay')
            # return tree

        if isinstance(tree, DFIntConst):
            if 'x' in tree.value or 'z' in tree.value:
                return DFUndefined(tree.width())
            if 'X' in tree.value or 'Z' in tree.value:
                return DFUndefined(tree.width())
            return DFEvalValue(tree.eval(), tree.width())
        if isinstance(tree, DFFloatConst):
            return DFEvalValue(tree.eval(), self.default_width, isfloat=True)
        if isinstance(tree, DFStringConst):
            return DFEvalValue(tree.eval(), None, isstring=True)
        if isinstance(tree, DFConstant):
            if 'x' in tree.value or 'z' in tree.value:
                return DFUndefined()
            if 'X' in tree.value or 'Z' in tree.value:
                return DFUndefined()
            return DFEvalValue(tree.eval(), self.default_width)

        if isinstance(tree, DFOperator):
            nextnodes_rslts, all_const = self.evalNextnodes(tree.nextnodes)
            if all_const:
                evalop = self.evalOperator(tree.operator, nextnodes_rslts)
                if evalop is not None:
                    return evalop
            return DFOperator(tuple(nextnodes_rslts), tree.operator)

        if isinstance(tree, DFTerminal):
            if not self.hasConstant(tree.name):
                return tree
            msb = self.getTerm(tree.name).msb
            lsb = self.getTerm(tree.name).lsb
            const = self.getConstant(tree.name)
            constwidth = const.width
            if msb is not None and lsb is not None:
                msb_val = self.optimizeConstant(msb)
                lsb_val = self.optimizeConstant(lsb)
                if isinstance(msb_val, DFEvalValue) and isinstance(lsb_val, DFEvalValue):
                    constwidth = msb_val.value - lsb_val.value + 1
            return DFEvalValue(const.value, constwidth)

        if isinstance(tree, DFConcat):
            nextnodes_rslts, all_const = self.evalNextnodes(tree.nextnodes)
            if all_const:
                evalcc = self.evalConcat(nextnodes_rslts)
                if evalcc is not None:
                    return evalcc
            return DFConcat(tuple(nextnodes_rslts))

        if isinstance(tree, DFPartselect):
            var = self.optimizeConstant(tree.var)
            msb = self.optimizeConstant(tree.msb)
            lsb = self.optimizeConstant(tree.lsb)
            if isinstance(var, DFEvalValue) and isinstance(msb, DFEvalValue) and isinstance(msb, DFEvalValue):
                evalcc = self.evalPartselect(var, msb, lsb)
                return evalcc
            return DFPartselect(var, msb, lsb)

        if isinstance(tree, DFPointer):
            if not isinstance(tree.var, DFTerminal):
                return tree
            term = self.getTerm(tree.var.name)
            var = self.optimizeConstant(tree.var)
            ptr = self.optimizeConstant(tree.ptr)
            if term.dims is not None:
                return DFPointer(var, ptr)
            if isinstance(var, DFEvalValue) and isinstance(ptr, DFEvalValue):
                evalcc = self.evalPointer(var, ptr)
                return evalcc
            return DFPointer(var, ptr)

        if isinstance(tree, DFSyscall):
            return DFSyscall(tree.syscall, tuple([self.optimizeConstant(n) for n in tree.nextnodes]))

        raise verror.DefinitionError('Can not optimize the tree: %s %s' %
                                     (str(type(tree)), str(tree)))



class VerilogDataflowOptimizer(VerilogOptimizer):
    def __init__(self, terms, binddict):
        VerilogOptimizer.__init__(self, terms, {})
        self.binddict = binddict
        self.resolved_terms = {}
        self.resolved_binddict = {}

    def getResolvedTerms(self):
        return self.resolved_terms

    def getResolvedBinddict(self):
        return self.resolved_binddict

    def getConstlist(self):
        return self.constlist

    def getTerm(self, name):
        return self.terms[name]

    def resolveConstant(self):
        # 2-pass
        for bk, bv in sorted(self.binddict.items(), key=lambda x: len(x[0])):
            termtype = self.getTerm(bk).termtype
            if signaltype.isParameter(termtype) or signaltype.isLocalparam(termtype):
                rslt = self.optimizeConstant(bv[0].tree)
                if isinstance(rslt, DFEvalValue):
                    self.constlist[bk] = rslt

        for bk, bv in sorted(self.binddict.items(), key=lambda x: len(x[0])):
            termtype = self.getTerm(bk).termtype
            if signaltype.isParameter(termtype) or signaltype.isLocalparam(termtype):
                rslt = self.optimizeConstant(bv[0].tree)
                if isinstance(rslt, DFEvalValue):
                    self.constlist[bk] = rslt

        self.resolved_binddict = copy.deepcopy(self.binddict)
        for bk, bv in sorted(self.binddict.items(), key=lambda x: len(x[0])):
            new_bindlist = []
            for bind in bv:
                new_bind = copy.deepcopy(bind)
                if bk in self.constlist:
                    new_bind.tree = self.constlist[bk]
                new_bindlist.append(new_bind)
            self.resolved_binddict[bk] = new_bindlist

        self.resolved_terms = copy.deepcopy(self.terms)
        for tk, tv in sorted(self.resolved_terms.items(), key=lambda x: len(x[0])):
            if tv.msb is not None:
                rslt = self.optimizeConstant(tv.msb)
                self.resolved_terms[tk].msb = rslt
            if tv.lsb is not None:
                rslt = self.optimizeConstant(tv.lsb)
                self.resolved_terms[tk].lsb = rslt
            if tv.dims is not None:
                dims = []
                for l, r in tv.dims:
                    l = self.optimizeConstant(l)
                    r = self.optimizeConstant(r)
                    dims.append((l, r))
                self.resolved_terms[tk].dims = tuple(dims)