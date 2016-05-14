"""
@author: Maya Gershovitz
"""

#================================================================================
# Imports
#================================================================================

import copy, re
from tabulate import tabulate


#================================================================================
# Classes
#================================================================================
from aux_functions_and_classes import ActiveItem, MCFGParserChart

EPSILON = ''

class MCFGParser:
    def __init__(self, mcfg_grammar=None):
        self.grammar = mcfg_grammar

    def parse(self, text):
        """
        Parses the given sentence, using the Incremental Algorithm for parsing MCFG grammar,
        as seen in Parsing Beyond Context Free Grammar
        
        @param text: A sequence of natural language words.
        @type text: A string
        
        @return: If sentence is in the language, returns a valid parse parsing table of the sentence,
                 otherwise returns None.
        @rtype: A list of ActiveItems or None.

        """
        # tokens = [token for token in text]
        tokens = text.split(' ')
        self.tokens = tokens
        self.chart = MCFGParserChart(tokens, self.grammar.terminals)

        # for index in range(0, len(tokens)):
        successful_parsing_item = None
        for index in range(0, len(tokens)):
            self.run_incremental_parse_for_max_position_i(tokens, index)

            # Check if we've finished
            for item in self.chart.get_items_list('completed_items'):
                if item.symbol == self.grammar.start_symbol and ' '.join(item.found_sequence) == text:
                    successful_parsing_item = item
                    break

        if successful_parsing_item:
            return self.chart.get_parsing_table(successful_parsing_item.get_item_id())
        else:
            return None

    def run_incremental_parse_for_max_position_i(self, tokens, index):
        """
        Parses the given text using the incremental parse algorithm.

        @param tokens: A sequence of natural language words.
        @type tokens: A sequence (e.g. a tuple) of strings.

        @:param index: A position in tokens (0 <= index <= len(tokens))
        @:type index: int

        @return: If sentence is in the language, returns a valid parse ParseTree of the sentence that has maximum
            probability. Otherwise, returns None.
        @rtype: ParseTree or None.

        """

        # If any item we'll be added to the parsing chart, this flag would be True
        not_finished = True
        token = tokens[index]

        # Do first prediction, for starting variable
        if index == 0:
            self.run_action_and_add_items_to_chart('predict', {'prediction_strategy': [self.grammar.start_symbol],
                                                               'token_index': 0, 'token': token})

        while not_finished:
            not_finished = False

            # Try predictions
            prediction_strategy = self.chart.get_current_prediction_strategy()
            predicted_items_added = self.run_action_and_add_items_to_chart('predict', {'token_index': index, 'token': token,
                                                                                       'prediction_strategy': prediction_strategy})
            not_finished = not_finished or predicted_items_added

            # Try combining
            current_active_items = self.chart.get_items_list('active_items')
            for completed_item in self.chart.get_items_list('active_items_with_completed_components'):
                combined_items_added = self.run_action_and_add_items_to_chart('combine',
                                                                              {'completed_item': completed_item, 'token_index': index,
                                                                               'current_active_items': current_active_items})
                not_finished = not_finished or combined_items_added

            # Try scanning
            current_active_items = self.chart.get_items_list('active_items')
            for active_item in current_active_items:
                scanned_items_added = self.run_action_and_add_items_to_chart('scan', {'active_item':active_item,
                                                                                      'token': token, 'token_index': index})
                not_finished = not_finished or scanned_items_added

    def run_action_and_add_items_to_chart(self, action_name, args):
        if action_name == 'predict':
            active_items = self.do_predict(**args)
            return self.chart.add_active_items_to_chart(active_items)

        if action_name == 'combine':
            combined_items, completed_items_after_combining = self.do_combine(**args)
            f1 = self.chart.add_active_items_to_chart(combined_items)
            f2 = self.chart.add_active_items_to_chart(completed_items_after_combining)
            f3 = self.chart.add_completed_items_to_chart(completed_items_after_combining)
            return f1 or f2 or f3

        if action_name == 'scan':
            active_items, completed_items = self.do_scan(**args)
            f1 = self.chart.add_active_items_to_chart(active_items)
            f2 = self.chart.add_active_items_to_chart(completed_items)
            f3 = self.chart.add_completed_items_to_chart(completed_items)
            return f1 or f2 or f3

    def do_predict(self, token, token_index, prediction_strategy):
        dot_position = (0,0) # dot position for predictions is always (0,0)
        active_items = []

        for symbol in prediction_strategy:
            rules = self.grammar.vars_to_rules[symbol]
            for rule in rules:
                if rule.used_in_prediction():
                    continue

                if rule.is_terminating_rule:
                    vector_binding = [[rule.function]]
                    possible_arg_index_order = [(0,)]

                else:
                    rule_func = rule.function
                    vector_binding = self.call_func(rule_func, rule.vars)
                    possible_arg_index_order = rule_func.get_all_possible_orders_for_result_vector()

                # Decide if we should make a prediction of this rule, and if so, guess a starting position
                first_symbol_in_yield = vector_binding[0][0]
                if first_symbol_in_yield in self.grammar.terminals and first_symbol_in_yield != token:
                    # Don't predict this rule, it's starts with the wrong terminal
                    continue

                rule.mark_used() # We don't want to make the same prediction twice
                found_start = found_end = token_index
                # We would like to add a different ActiveItem for each possible order
                # Let's count how many arguments we have in the rule right hand side

                # self.chart.add_item_to_prediction_strategy(set(rule_func.get_function_arguments()))
                self.chart.add_item_to_prediction_strategy(set(rule.vars))

                for possible_order in possible_arg_index_order:
                # iterate over all possible orders of the rules
                    active_item = ActiveItem(symbol, found_start, found_end, dot_position, 'predict', possible_order, token_index, vector_binding, rule)
                    active_items.append(active_item)
        return active_items

    def do_scan(self, active_item, token, token_index):
        active_items = []
        completed_items = []
        # Don't scan past current token index
        if active_item.token_index > token_index:
            return active_items, completed_items

        if not active_item.is_scanned():

            # Check if first argument after dot is terminal
            symbol_after_dot = self.get_symbol_after_dot(active_item)

            # Check if symbol is identical to left-most token we haven't found yet
            if symbol_after_dot == token:
                antecedent_ids = [active_item.get_item_id()]

                # Remove scanned symbol from vector binding
                vector_binding_copy = copy.copy(active_item.vector_binding)
                next_dot_position, complete = active_item.get_next_dot_position_and_check_if_complete()

                # Add scan step
                found_sequence = copy.deepcopy(active_item.found_sequence)
                found_sequence.append(symbol_after_dot)

                scanned_active_item = ActiveItem(active_item.symbol, active_item.found_start, active_item.found_end+1,
                                             next_dot_position, 'scan', active_item.range_order, token_index, vector_binding_copy,
                                             active_item.rule, antecedent_ids, found_sequence)

                active_items.append(scanned_active_item)

                # Mark active item as scanned, so it won't be scanned again
                active_item.mark_scanned()

                # If the scanned item is complete, we'll mark it as ignored, so we'll only handle the complete one in the future
                if complete:
                    scanned_active_item.mark_ignored()
                    complete_active_item = scanned_active_item.create_complete_item()
                    completed_items.append(complete_active_item)


        return active_items, completed_items

    def do_combine(self, completed_item, token_index, current_active_items):
        combined_items = []
        completed_items_after_combining = []

        # using the current dot position, and the range order, calculate the completed component in this item
        completed_components_and_values = completed_item.get_all_completed_components_and_values()

        # Find all active items looking for this component at the moment
        for completed_component in completed_components_and_values.keys():
            completed_component_value = ' '.join(completed_components_and_values[completed_component])

            candidates_for_combining = []

            for item in current_active_items:
                if self.get_symbol_after_dot(item) == completed_component:
                    candidates_for_combining.append(item)

            for active_item in candidates_for_combining:
                # Don't combine past the current token
                if active_item.token_index > token_index:
                    continue

                # Check if this couple was already combined
                couple_ids = (active_item.get_item_id(), completed_item.get_item_id())

                if self.chart.check_if_couple_is_already_combined(couple_ids):
                    continue

                self.chart.update_combined_couples(couple_ids)

                # Compare completed components.
                # If there are any completed components in active item, that are also completed in completed item,
                # They must match in order to combine
                item_completed_components = active_item.get_all_completed_components_and_values()
                if item_completed_components and len(completed_components_and_values.keys()) >1:
                    # The completed item and the active item have the same completed component,
                    # We need to make sure they match, before proceeding to combining
                    common_components = set(completed_components_and_values.keys()).intersection(set(item_completed_components.keys()))
                    for component in common_components:
                        if item_completed_components[component] != completed_components_and_values[component]:
                            # Can't combine
                            continue

                else:

                    antecedent_ids = [active_item.get_item_id(), completed_item.get_item_id()]
                    new_vector_binding = self.get_new_vector_binding(active_item, completed_component_value)
                    # Since we know the symbol after the do equals to the component, we can replace it immediately

                    # We're always combining forward, never backwards
                    next_dot_position, complete = active_item.get_next_dot_position_and_check_if_complete()
                    # Merge found sequences
                    new_found_sequence = copy.deepcopy(active_item.found_sequence)
                    new_found_sequence.append(completed_component_value)

                    # update start and end points
                    new_found_start = active_item.found_start
                    new_found_end = active_item.found_end + 1

                    combined_item = ActiveItem(active_item.symbol, new_found_start, new_found_end, next_dot_position,
                                               'combine', active_item.range_order, token_index, new_vector_binding, active_item.rule,
                                               antecedent_ids, new_found_sequence, found_components=completed_component)

                    # If the combined item is complete, we'll mark it as ignored, so we'll only handle the complete one in the future
                    combined_items.append(combined_item)

                    if complete:
                        combined_item.mark_ignored()
                        completed_combined_item = combined_item.create_complete_item()
                        completed_items_after_combining.append(completed_combined_item)


        return combined_items, completed_items_after_combining

    ######### AUX ###########

    def get_symbol_after_dot(self, active_item):
        try:
            component_index = active_item.range_order[active_item.dot_position[0]]
            next_symbol = active_item.vector_binding[component_index][active_item.dot_position[1]]
            return next_symbol

        except:
            # This must be an item with a completed vector
            return None

    def get_new_vector_binding(self, active_item, new_component_value):
        '''
        Receives an active item, and creates a new vector binding which is a copy of the active item's binding,
        where the component after the dot position is replaced with a new_component_value

        :param active_item: an ActiveItem object
        :param new_component_value: string value
        :return: new vector binding list
        '''
        try:
            new_vector_binding = copy.deepcopy(active_item.vector_binding)
            component_index = active_item.range_order[active_item.dot_position[0]]
            new_vector_binding[component_index][active_item.dot_position[1]] = new_component_value
            return new_vector_binding

        except:
            raise ("Got a wrong dot position")

    def call_func(self, func, args):
        if len(args) != len(func.input_args):
            raise ("Function got wrong number of arguments")

        call_result = []
        for component in func.result_vector:
            component_result = []
            for item in component:
                if item in self.grammar.terminals:
                    component_result.append(item)
                else:
                    item_symbol, index = re.match('([^\(]*)\((.*)\)', item).groups()
                    arg_index = func.input_args.index(item_symbol)
                    arg = args[arg_index]
                    component_result.append(arg + '(%s)' % index)
            call_result.append(component_result)
        return call_result

