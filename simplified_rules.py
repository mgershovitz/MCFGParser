import copy
import re


class SimplifiedRules:
    def __init__(self, rules, terminals, start_symbol):

        self.terminals = terminals
        self.start_symbol = start_symbol
        self.rules = self.simplify(rules)

    def get_rules(self):
        return self.rules

    def simplify(self, rules):
        '''
        Receives a list of unconstrained MCFG rules and simplifies them.
        Rules simplification that I've chosen to implement:
        1. Eliminating useless rules

        :param rules: a list of MCFGRule objects
        :return: a list of near cnf rules
        '''
        rules = self.eliminate_useless_rules(rules)
        rules = self.eliminate_unreachable_rules(rules)
        return rules

    def eliminate_useless_rules(self, rules):
        original_rules = copy.deepcopy(rules)
        useful_rules = set()

        # terminal_predicates set contains all the predicates that lead to terminals
        terminal_predicates = set()
        terminal_predicates.update(self.terminals)

        # Start with all terminal rules
        for rule in original_rules:
            if rule.is_terminating_rule:
                useful_rules.add(rule)
                terminal_predicates.add(rule.symbol)

        for rule in original_rules:
            right_hand_side = self.get_right_hand_side(rule)
            if self.all_vector_components_in_set(right_hand_side, terminal_predicates):
                useful_rules.add(rule)
                terminal_predicates.add(rule.symbol)

        found_useful_rules = self.update_original_rules(useful_rules, original_rules)

        if not found_useful_rules:
            return []

        # Recursively find all rules that can reach the rules in useful rules
        while found_useful_rules:
            for rule in original_rules:
                right_hand_side = self.get_right_hand_side(rule)
                if self.all_vector_components_in_set(right_hand_side, terminal_predicates):
                    useful_rules.add(rule)
                    terminal_predicates.add(rule.symbol)

            found_useful_rules = self.update_original_rules(useful_rules, original_rules)

        return useful_rules

    def eliminate_unreachable_rules(self, rules):
        original_rules = copy.deepcopy(rules)
        reachable_rules = set()

        # terminal_predicates set contains all the predicates that are reachable from starting symbol
        reachable_predicates = set()

        # Start with all starting rules
        for rule in original_rules:
            if rule.symbol == self.start_symbol:
                reachable_rules.add(rule)
                right_hand_side = self.get_right_hand_side(rule)
                reachable_predicates.update(right_hand_side)

        found_reachable_rules = self.update_original_rules(reachable_rules, original_rules)

        if not found_reachable_rules:
            return []

        # Recursively find all rules that can reach the rules in useful rules
        while found_reachable_rules:
            for rule in original_rules:
                if rule.symbol in reachable_predicates:
                    reachable_rules.add(rule)
                    right_hand_side = self.get_right_hand_side(rule)
                    reachable_predicates.update(right_hand_side)

            found_reachable_rules = self.update_original_rules(reachable_rules, original_rules)

        return reachable_rules

    def update_original_rules(self, useful_rules, original_rules):
        '''
        Removes every rule in useful rules from original rules

        :param useful_rules: a list of MCFGRules, which have been found useful
        :param original_rules: a list of MCFGRules
        :return: True if any rules were removed from original rules, False otherwise
        '''
        found_useful_rules = False
        for rule in useful_rules:
            if rule in original_rules:
                original_rules.remove(rule)
                found_useful_rules = True

        return found_useful_rules

    def get_right_hand_side(self, rule):
        if rule.is_terminating_rule:
            return set(rule.function)

        right_hand_side = set()
        result_vector = rule.function.result_vector
        for v in result_vector:
            for c in v:
                if c not in self.terminals:
                    symbol, index = re.match('([^\(]*)\((.*)\)', c).groups()
                    arg_index = rule.function.input_args.index(symbol)
                    c = rule.vars[arg_index]
                right_hand_side.add(c)
        return right_hand_side

    def all_vector_components_in_set(self, l, predicate_set):
        '''
        :param l: a list of predicates
        :return: True if all predicates in the list are in predicate_set
        '''
        for v in l:
            if v not in predicate_set:
                return False
        return True
