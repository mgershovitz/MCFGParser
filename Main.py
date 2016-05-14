"""
Advance Computational Linguistics - Final Project
Tel Aviv Univerity, course no. 0627.4090, Fall 2015.

An implementation of PCFG parsing.

@author: Maya Gershovitz
"""

#================================================================================
# Imports
#================================================================================

from aux_functions_and_classes import MCFG
from MCFG import MCFGParser
from tests import tests
from aux_functions_and_classes import MCFGParserChart

#================================================================================
# Main
#================================================================================

if __name__ == "__main__":

    successful_parsings = 0
    for test in tests:
        print("\nGrammar functions:")
        for func in test.functions:
            print (func)

        print("\n\nGrammar rules:")
        for rule in test.rules:
            print (rule)

        print('\n\nGrammar terminals: %s' % ', '.join(test.terminals))

        print ('\n\nText: %s' % test.text)

        mcfg_grammar = MCFG(terminals=test.terminals, functions=test.functions, rules=test.rules)
        mcfg_parser = MCFGParser(mcfg_grammar)
        parse_chart = mcfg_parser.parse(test.text)
        if parse_chart:
            successful_parsings+=1
            print('\n\nParsing table:')
            mcfg_parser.chart.print_chart(parse_chart)
            print('*************************************************************'
                  '********************************************************************************')

        else:
            print("\n\nCouldn't find a successful parsing, sentance is not in the language")

    print ("Finished: %s Successful parsings, %s failed parsings." % (successful_parsings, len(tests) - successful_parsings))