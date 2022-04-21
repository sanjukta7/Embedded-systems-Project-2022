from __future__ import absolute_import
from __future__ import print_function
import sys
import os
from optparse import OptionParser


def main():

    analyzer = VerilogDataflowAnalyzer(filelist, options.topmodule,
                                       preprocess_include=options.include,
                                       preprocess_define=options.define)
    analyzer.generate()

    directives = analyzer.get_directives()
    terms = analyzer.getTerms()
    binddict = analyzer.getBinddict()

    optimizer = VerilogDataflowOptimizer(terms, binddict)

    optimizer.resolveConstant()
    resolved_terms = optimizer.getResolvedTerms()
    resolved_binddict = optimizer.getResolvedBinddict()
    constlist = optimizer.getConstlist()
    fsm_vars = tuple(['fsm', 'state', 'count', 'cnt', 'step', 'mode'] + options.searchtarget)

    canalyzer = VerilogControlflowAnalyzer(options.topmodule, terms, binddict,
                                           resolved_terms, resolved_binddict, constlist, fsm_vars)
    fsms = canalyzer.getFiniteStateMachines()

    for signame, fsm in fsms.items():
        print('# SIGNAL NAME: %s' % signame)
        print('# DELAY CNT: %d' % fsm.delaycnt)
        fsm.view()
        if not options.nograph:
            fsm.tograph(filename=util.toFlatname(signame) + '.' +
                        options.graphformat, nolabel=options.nolabel)
        loops = fsm.get_loop()
        print('Loop')
        for loop in loops:
            print(loop)


if __name__ == '__main__':
    main()