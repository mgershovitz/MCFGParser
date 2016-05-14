from collections import defaultdict
import copy
import itertools, re
from tabulate import tabulate
from simplified_rules import SimplifiedRules

class MCFG:
    """
    Represents a multiple context-free grammar.
    Based on the grammar as shown in:
        'Parsing beyond context-free grammar: CYK Parsing for MCFG', Laura Kallmeyer, Wolfgang Maier
        'On multiple context-free grammars', Hiroyuki Seki, Takashi Matsumura, Mamoru Fujii, Tadao Kasami

    """

    def __init__(self, terminals, functions, rules, start_symbol="S"):
        """
        Initializes a MCFG parser instance

        :param terminals: A finite set of terminals used in the language created by the grammar
        :param rules: A list of MCFGRules - mapping Symbols to symbols, functions and variables
        :param functions: A dictionary of MCFGFunc
        :param start_symbol: The initial symbol for this grammar

        """
        self.start_symbol = start_symbol
        self.terminals = terminals

        self.functions = functions
        self.func_name_to_func = {func.func_name: func for func in functions}

        self.rules = []
        self.connect_rules_to_funcs(rules)

        simplified_rules = SimplifiedRules(rules, terminals, start_symbol)
        self.rules = simplified_rules.get_rules()

        self.vars_to_rules = defaultdict(lambda : list())

        for rule in self.rules:
            self.vars_to_rules[rule.symbol].append(rule)

        self.tokens = None
        self.chart = None
        self.agenda = None

    def connect_rules_to_funcs(self, rules):
        for rule in rules:
            right_hand_element = rule.function
            if right_hand_element in self.terminals:
                rule.mark_terminating()
            else:
                func_name = right_hand_element
                rule_func = self.func_name_to_func[func_name]
                rule.function = rule_func
        self.rules = rules

class MCFGRule:
    """
    Represents a single rule in a MCFG.
    
    Rules are of the form:
        symbol -> function(V1... Vn)
    
    @ivar symbol: The variable on the left side of the rule.
    @type symbol: string
    
    @ivar function: The function the rule applies to the it's vars.
    @type function: string.
    
    @ivar vars: The variables on the right side of the rule (a var can be an empty string)
    @type vars: a list of strings.
    """
    
    def __init__(self, symbol, function, vars):

        self.symbol = symbol
        self.function = function
        self.vars = vars

        self.used = False
        self.is_terminating_rule = False

    def mark_used(self):
        self.used = True

    def used_in_prediction(self):
        return self.used

    def mark_terminating(self):
        self.is_terminating_rule = True

    def __repr__(self):
        return self.symbol + ' --> ' + self.function.__repr__()

    def __eq__(self, other):
        return (self.symbol == other.symbol and self.function == other.function and self.vars == other.vars)

    def __hash__(self):
        return hash(self.symbol) ^ hash(str(self.function)) ^ hash(str(','.join(self.vars)))

class MCFGFunc:
    '''
    Represents a single func in a MCFG with range constraint vectors.

    Functions are of the form:
        func := (V1(i)...Vn(j)

    @ivar input_vars: Input vars for the function (a var can be an empty string)
    @type input_vars: list of strings.

    @ivar result_vector: The vector of the function output, given the input vars
    @type result_vector: a vector of lists, each list is a combination of variables and terminals.
                         where terminals are strings, and variables are tuples of symbol and index

    '''
    def __init__(self, func_name, input_args, result_vector):
        self.func_name = func_name
        self.input_args = input_args
        self.result_vector = result_vector

    def get_function_arguments(self):
        return self.input_args

    def get_all_possible_orders_for_result_vector(self):
        all_possible_vector_index_orders = itertools.permutations(range(0, len(self.result_vector)), len(self.result_vector))
        return all_possible_vector_index_orders

    def __eq__(self, other):
        return (self.func_name == other.func_name and self.input_args == other.input_args and self.result_vector == other.result_vector)

    def __repr__(self):
        return_parts = []
        for component in self.result_vector:
            component_string = ' '.join(component)
            return_parts.append(component_string)

        return self.func_name + '[' + ','.join(self.input_args) + ']' + ' := ' + '<' + ','.join(return_parts) + '>'

class ActiveItem:

    items_counter=0
    def __init__(self, symbol, found_start, found_end, dot_position, action_type, range_order, token_index,
                 vector_binding, rule, antecedent_ids=None, found_sequence='', found_components = None):
        '''

        :param symbol:
        :param start:
        :param end:
        :param dot_position: a tuple of two indexs, describing the position of the dot -
                             for example, position (1, 0) is the left-most position in the second part of the vector
        :param action_type:
        :param range_order:
        :param vector_binding: a list, where the i'th item is the current value of the i'th part of the vector
        :param rule: original prediction rule
        :param antecedent_ids: ids of antecedent items, if there isn't an antecedent (predict items) the default value is None
        :return:
        '''
        self.symbol = symbol
        self.dot_position = dot_position
        self.found_start = found_start
        self.found_end = found_end
        self.range_order = range_order
        self.token_index = token_index
        self.action_type = action_type
        self.rule = rule

        if not found_sequence:
            found_sequence = []
        self.found_sequence = found_sequence

        if not antecedent_ids:
            antecedent_ids = []
        self.antecedent_ids = antecedent_ids

        # Keep track of processing
        self.scanned = False
        self.combined = False
        self.ignored = False

        # Add 1 to class counter, and fill item id
        type(self).items_counter += 1
        self.id = type(self).items_counter

        # update vector values with initial vector binding
        self.vector_binding = vector_binding

    def get_item_id(self):
        return self.id

    def mark_scanned(self):
        self.scanned = True

    def mark_ignored(self):
        self.ignored = True

    def get_next_dot_position_and_check_if_complete(self, force_complete=False):
        '''
        :return: the next do position, and a boolean value 'complete'
                 Complete=True if this dot position marks the last position of a vector component
        '''
        vector_component = self.vector_binding[self.dot_position[0]]
        vector_component_index = self.dot_position[0]

        if force_complete:
            # Just jump to the start of the next component
            next_dot_position = (vector_component_index+1, 0)
            complete = False

        else:
            next_position_in_vector_component = self.dot_position[1]+1
            next_dot_position = (vector_component_index, next_position_in_vector_component)

            if next_position_in_vector_component < len(vector_component):
                complete = False

            # next position completes a component
            elif next_position_in_vector_component == len(vector_component):
                complete = True

            # next_position_in_vector_component > len(vector_component) - next position start a new component
            else:
                vector_component_index += 1
                next_position_in_vector_component = 0
                next_dot_position = (vector_component_index, next_position_in_vector_component)
                complete = False

        return next_dot_position, complete

    def get_all_completed_components_and_values(self):
        completed_components_and_values = {}
        if self.dot_position[0] > 0:
            completed_components_indexes = list(range(0,self.dot_position[0]))
            for index in completed_components_indexes:
                range_constraint = self.symbol + '(' + str(self.range_order[index]) + ')'
                completed_components_and_values[range_constraint] = self.vector_binding[self.range_order[index]]

        return completed_components_and_values

    def create_complete_item(self):
        next_dot_position, complete = self.get_next_dot_position_and_check_if_complete(force_complete=True)

        complete_item = ActiveItem(self.symbol, self.found_start, self.found_end, next_dot_position,
                                   'complete', self.range_order, self.token_index, self.vector_binding, self.rule,
                                   [self.get_item_id()], self.found_sequence)
        return complete_item

    def is_scanned(self):
        return self.scanned

    def __eq__(self, other):
        object_dict = self.__dict__
        other_dict = other.__dict__
        for attr, val in object_dict.items():
            if attr != 'id' and attr != 'antecedent_ids':
                if (val != other_dict[attr]):
                    return False
        return True

    def __repr__(self):
        return self.__dict__.__repr__()

class MCFGParserChart:
    def __init__(self, tokens, terminals):
        if not isinstance(tokens, (list, tuple)):
            raise TypeError("Tokens must be a list or a tuple of strings")

        self.chart = {}
        self.chart['tokens'] = tokens
        self.chart['terminals'] = terminals
        self.chart['active_items'] = {}
        self.chart['active_items_with_completed_components'] = {}
        self.chart['completed_items'] = {}

        self.chart['prediction_strategy'] = set()
        self.chart['combined_couples'] = []


        self.chart['all_items'] = {}

    def add_item_to_prediction_strategy(self, strategy_set):
        grammar_terminals = self.chart['terminals']
        for item in strategy_set:
            if item and item not in grammar_terminals:
                self.chart['prediction_strategy'].update(strategy_set)

    def add_active_items_to_chart(self, active_items_list):
        '''
        The method receives a list of active items, created by predict, scan and combine actions.
        All the items that cannot create the original input text are filtered out,
        to save processing time.
        All 'good' active items are stored in self.chart['active_items']

        :param active_items_list: a list of ActiveItem objects

        :returns: True if any items were added to the chart
        '''
        filtered_active_items_list = self.filter_out_non_compatible_items(active_items_list)

        # items_id_to_items_dict = {item.get_item_id(): item for item in filtered_active_items_list}
        # self.chart['active_items'].update(items_id_to_items_dict)
        self.add_items_to_chart(filtered_active_items_list, 'active_items')

        if filtered_active_items_list:
            return True
        else:
            return False

    def add_completed_items_to_chart(self, completed_items_list):
        '''
        :param completed_items_list:
        :returns: True if any items were added to the chart
        '''
        filtered_completed_items_list = self.filter_out_non_compatible_items(completed_items_list)

        for item in filtered_completed_items_list:
            if item.dot_position[0] == len(item.vector_binding):
                # All vectors in item has been filled, this item is not active any more,
                self.add_items_to_chart([item], 'completed_items')
                item_id = item.get_item_id()
                if item_id in self.chart['active_items']:
                    self.chart['active_items'].pop(item_id)

        self.add_items_to_chart(filtered_completed_items_list, 'active_items_with_completed_components')

        if filtered_completed_items_list:
            return True
        else:
            return False

    def filter_out_non_compatible_items(self, items_list):
        filtered_item_list = []
        original_text = ' '.join(self.chart['tokens'])
        for item in items_list:
            # only filter out items with terminal strings
            item_sequence = item.found_sequence
            if not self.all_terminals(item_sequence):
                filtered_item_list.append(item)
            else:
                found_sequence_text = ' '.join(item_sequence)
                if found_sequence_text in original_text:
                    filtered_item_list.append(item)
        return filtered_item_list

    def all_terminals(self, l):
        '''
        :param l: a list of strings
        :return: True if all of the strings in the list are terminals
        '''
        for s in l:
            for c in s.split(' '):
                if c not in self.chart['terminals']:
                    return False
        return True

    def get_items_list(self, chart_name):
        if chart_name != 'all_items':
            return [item for item in self.chart[chart_name].values() if not item.ignored]
        else:
            return self.chart[chart_name].values()

    def get_current_prediction_strategy(self):
        prediction_strategy =  copy.copy(self.chart['prediction_strategy'])
        # self.chart['prediction_strategy'].clear()
        return prediction_strategy

    def update_combined_couples(self, ids_tuple):
        self.chart['combined_couples'].append(ids_tuple)

    def check_if_couple_is_already_combined(self, ids_tuple):
        id1, id2 = ids_tuple
        return (id1, id2) in self.chart['combined_couples'] or (id2, id1) in self.chart['combined_couples']

    def add_items_to_chart(self, items_list, chart_name):
        for item in items_list:
            item_id = item.get_item_id()
            self.chart['all_items'][item_id] = item
            if item in self.chart[chart_name].values():
                # We don't want to keep processing identical parsings
                item.mark_ignored()
            self.chart[chart_name][item_id] = item

    # pretty printing
    def print_chart(self, items_list=None):
        if not items_list:
            items_list = self.get_items_list('active_items')
        items_dict = {item.get_item_id():item for item in items_list}
        ordered_ids = [item.get_item_id() for item in items_list]

        headers_row = ['id', 'Item', 'Sequence', 'i', 's', 'Rule', 'Binding']
        table = []

        for item_id in ordered_ids:
            table_row = []
            active_item = items_dict[item_id]
            table_row.append(item_id)
            rule_representation = active_item.rule.__repr__()
            rule_representation = re.match('([^=]*)', rule_representation).group(1) + '= '
            rule_representation += '<R%s=' % active_item.range_order[0]
            rule_representation += '<%s,%s>  ' % (active_item.found_start, active_item.found_end)
            table_row.append(rule_representation)

            # Add dot in its right position
            vector_binding_copy = copy.deepcopy(active_item.vector_binding)
            # Order vector according to range
            ordered_vector_binding = []
            for index in active_item.range_order:
                ordered_vector_binding.append(vector_binding_copy[index])

            if active_item.dot_position[0] < len(ordered_vector_binding):
                vector_component_copy = ordered_vector_binding[active_item.dot_position[0]]
                dot_index = active_item.dot_position[1]
                vector_component_copy.insert(dot_index, '*')

                # Delete everything before the dot
                ordered_vector_binding_representation_parts = []
                for i in range(0, len(ordered_vector_binding)):
                    component = ordered_vector_binding[i]
                    if i == active_item.dot_position[0]:
                        ordered_vector_binding_representation_parts.append(' '.join(component[dot_index:]))
                    elif i > active_item.dot_position[0]:
                        ordered_vector_binding_representation_parts.append(' '.join(component))
                ordered_vector_binding_representation = ','.join(ordered_vector_binding_representation_parts)

            else:
                ordered_vector_binding_representation = '*'


            table_row.append(ordered_vector_binding_representation)

            table_row.append(active_item.token_index+1)
            table_row.append(' '.join(active_item.found_sequence))

            antecedent_id_str = ' ' + ','.join([str(id) for id in active_item.antecedent_ids])
            table_row.append(active_item.action_type + antecedent_id_str)

            vector_binding_string_parts = []
            for i in active_item.range_order:
                part = active_item.symbol + '(' + str(i) + ')' + '= '
                part += ' '.join(active_item.vector_binding[i])
                vector_binding_string_parts.append(part)
            vector_binding_string = ', '.join(vector_binding_string_parts)

            table_row.append(vector_binding_string)

            table.append(table_row)

        print(tabulate(table, headers=headers_row))

    def get_parsing_table(self, active_item_id):
        parsing_table = []
        item = self.chart['all_items'][active_item_id]
        parsing_table.insert(0, item)
        antecedents = copy.copy(item.antecedent_ids)
        while antecedents:
            active_item_id = antecedents[0]
            antecedents = antecedents[1:]
            item = self.chart['all_items'][active_item_id]
            if item in parsing_table:
                continue
            parsing_table.insert(0, item)
            antecedents.extend(item.antecedent_ids)

        return parsing_table