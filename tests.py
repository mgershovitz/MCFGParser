
from aux_functions_and_classes import MCFGFunc, MCFGRule

class ParsingTest:
    def __init__(self, functions, rules, terminals, text):
        self.functions = functions
        self.rules = rules
        self.terminals = terminals
        self.text = text

tests = []

# Test 1 and 2 are based on example in 'Parsing beyond context-free grammar'

## copies and repeats example ##

functions = [
    MCFGFunc('f1', ['A'], [['A(0)', 'A(1)', 'A(2)']]),
    MCFGFunc('f2', ['A'], [['a', 'A(0)'], ['a', 'A(1)'], ['a', 'A(2)']]),
    MCFGFunc('f3', ['A'], [['b', 'A(0)'], ['b', 'A(1)'], ['b', 'A(2)']]),
    MCFGFunc('f4', [''], [['a'], ['a'], ['a']]),
    MCFGFunc('f5', [''], [['b'], ['b'], ['b']])
]

rules = [
    MCFGRule('S', 'f1', ['A']),
    MCFGRule('A', 'f2', ['A']),
    MCFGRule('A', 'f3', ['A']),
    MCFGRule('A', 'f4', ['']),
    MCFGRule('A', 'f5', ['']),
]

terminals = ['a', 'b']
text = "a b a b a b"

test1 = ParsingTest(functions, rules, terminals, text)
tests.append(test1)

## Simple Example ##
functions = [
    MCFGFunc('f1', ['C', 'A'], [['C(0)', 'A(0)', 'C(1)']]),
    MCFGFunc('f2', ['A'], [['a', 'A(1)']]),
    MCFGFunc('f3', [], [['a']]),
    MCFGFunc('f4', ['C'], [['b', 'C(0)'], ['b', 'C(1)']]),
    MCFGFunc('f5', ['C'], [['c', 'C(0)'], ['c', 'C(1)']]),
    MCFGFunc('f6', [], [['c'], ['c']]),

]

rules = [
    MCFGRule('S', 'f1', ['C', 'A']),
    MCFGRule('A', 'f2', ['A']),
    MCFGRule('A', 'f3', []),
    MCFGRule('C', 'f4', ['C']),
    MCFGRule('C', 'f5', ['C']),
    MCFGRule('C', 'f6', []),
]

terminals = ['a', 'b', 'c']
text = 'b b c a b b c'

test2 = ParsingTest(functions, rules, terminals, text)
tests.append(test2)

# Multiple completed components example ##

functions = [
    MCFGFunc('f1', ['B'], [['B(0)', 'B(1)']]),
    MCFGFunc('f2', [], [['a'], ['b']]),
    MCFGFunc('f3', ['B'], [['B(0)']]),
    MCFGFunc('f4', ['C'], [['C(0)']]),
]

rules = [
    MCFGRule('S', 'f1', ['B']),
    MCFGRule('B', 'f2', []),
    MCFGRule('B', 'f3', ['B']),
    MCFGRule('B', 'f4', ['C']),
    MCFGRule('C', 'a', []),
]

terminals = ['a', 'b']
text = 'a b'

tests.append(ParsingTest(functions, rules, terminals, text))

# Natural language ##

functions = [
    MCFGFunc('f0', ['IP', 'I'], [['IP(0)', 'I(0)', 'IP(1)']]),
    MCFGFunc('f1', ['NP', 'VP'], [['NP(0)'], ['VP(0)']]),
    MCFGFunc('f2', ['Det', 'N'], [['Det(0)', 'N(0)']]),
    MCFGFunc('f3', ['X'], [['X(0)']]),
    MCFGFunc('f4', ['V', 'NP'], [['V(0)', 'NP(0)']]),
    MCFGFunc('f5', ['A', 'NP'], [['A(0)', 'NP(0)']]),
    MCFGFunc('f6', ['NP1', 'NP2'], [['NP1(0)', 'and', 'NP2(0)']]),
    MCFGFunc('f7', ['X'], [['X(0)', 'X(1)']]),
]

rules = [
    MCFGRule('S', 'f0', ['IP', 'I']),
    MCFGRule('S', 'f7', ['IP']),
    MCFGRule('IP', 'f1', ['NP', 'VP']),
    MCFGRule('VP', 'f4', ['V', 'NP']),

    MCFGRule('NP', 'f2', ['Det', 'NP']),
    MCFGRule('NP', 'f6', ['NP', 'NP']),
    MCFGRule('NP', 'f3', ['N']),
    MCFGRule('NP', 'f5', ['A', 'NP']),


    # Terminating rules
    MCFGRule('Det', 'the', []),
    MCFGRule('N', 'dog', []),
    MCFGRule('N', 'Miki', []),
    MCFGRule('N', 'cat', []),
    MCFGRule('N', 'cow', []),
    MCFGRule('V', 'see', []),
    MCFGRule('A', 'red', []),
    MCFGRule('A', 'beautiful', []),
    MCFGRule('I', 'will', []),

]

terminals = ['Miki', 'cat', 'dog', 'the', 'see', 'and', 'cow', 'red', 'beautiful', 'will']
text = 'Miki and the dog and the cat will see the red beautiful cow'

tests.append(ParsingTest(functions, rules, terminals, text))

# Test 5 and 6 is based on example in 'An introduction to multiple context-free grammars'

functions = [
    MCFGFunc('f0', ['IP'], [['IP(0)', 'IP(1)', 'IP(2)']]),
    MCFGFunc('f1', ['NP', 'VP'], [['NP(0)'], ['VP(0)'], ['VP(1)']]),
    MCFGFunc('f2', ['Det', 'NP'], [['Det(0)', 'NP(0)']]),
    MCFGFunc('f3', ['V', 'NP'], [['V(0)'], ['NP(0)']]),
    MCFGFunc('f4', ['N'], [['N(0)']]),
]

rules = [
    MCFGRule('S', 'f0', ['IP']),
    MCFGRule('IP', 'f1', ['NP', 'VP']),
    MCFGRule('NP', 'f2', ['Det', 'NP']),
    MCFGRule('VP', 'f3', ['V', 'NP']),
    MCFGRule('NP', 'f4', ['N']),


    # Terminating rules
    MCFGRule('Det', 'the', []),
    MCFGRule('N', 'book', []),
    MCFGRule('N', 'I', []),

    MCFGRule('V', 'is', []),
    MCFGRule('V', 'read', []),

]

text = "I read the book"
terminals = ['I', 'the', 'is', 'book', 'read',]

test5 = ParsingTest(functions, rules, terminals, text)
tests.append(test5)


functions = [

    # Movement function
    MCFGFunc('f0', ['IP'], [['IP(2)', 'that', 'IP(0)', 'IP(1)']]),
    MCFGFunc('f5', ['IP'], [['IP(0)', 'IP(1)', 'IP(2)']]),
    MCFGFunc('f1', ['NP', 'VP'], [['NP(0)'], ['VP(0)'], ['VP(1)']]),
    MCFGFunc('f2', ['Det', 'NP'], [['Det(0)', 'NP(0)']]),
    MCFGFunc('f3', ['V', 'NP'], [['V(0)'], ['NP(0)']]),
    MCFGFunc('f4', ['N'], [['N(0)']]),
]

rules = [
    MCFGRule('S', 'f0', ['IP']),
    MCFGRule('S', 'f5', ['IP']),

    MCFGRule('IP', 'f1', ['NP', 'VP']),
    MCFGRule('NP', 'f2', ['Det', 'NP']),
    MCFGRule('VP', 'f3', ['V', 'NP']),
    MCFGRule('NP', 'f4', ['N']),


    # Terminating rules
    MCFGRule('Det', 'the', []),
    MCFGRule('N', 'book', []),
    MCFGRule('N', 'I', []),

    MCFGRule('V', 'is', []),
    MCFGRule('V', 'read', []),

]

text = "the book that I read"
terminals = ['I', 'the', 'is', 'book', 'read', 'that']


test6 = ParsingTest(functions, rules, terminals, text)
tests.append(test6)