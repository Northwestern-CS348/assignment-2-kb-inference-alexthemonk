import read, copy
from util import *
from logical_classes import *

verbose = 0

class KnowledgeBase(object):
    def __init__(self, facts=[], rules=[]):
        self.facts = facts
        self.rules = rules
        self.ie = InferenceEngine()

    def __repr__(self):
        return 'KnowledgeBase({!r}, {!r})'.format(self.facts, self.rules)

    def __str__(self):
        string = "Knowledge Base: \n"
        string += "\n".join((str(fact) for fact in self.facts)) + "\n"
        string += "\n".join((str(rule) for rule in self.rules))
        return string

    def _get_fact(self, fact):
        """INTERNAL USE ONLY
        Get the fact in the KB that is the same as the fact argument

        Args:
            fact (Fact): Fact we're searching for

        Returns:
            Fact: matching fact
        """
        for kbfact in self.facts:
            if fact == kbfact:
                return kbfact

    def _get_rule(self, rule):
        """INTERNAL USE ONLY
        Get the rule in the KB that is the same as the rule argument

        Args:
            rule (Rule): Rule we're searching for

        Returns:
            Rule: matching rule
        """
        for kbrule in self.rules:
            if rule == kbrule:
                return kbrule

    def kb_add(self, fact_rule):
        """Add a fact or rule to the KB
        Args:
            fact_rule (Fact|Rule) - the fact or rule to be added
        Returns:
            None
        """
        printv("Adding {!r}", 1, verbose, [fact_rule])
        if isinstance(fact_rule, Fact):
            if fact_rule not in self.facts:
                self.facts.append(fact_rule)
                for rule in self.rules:
                    # try to infer anything possible
                    self.ie.fc_infer(fact_rule, rule, self)
            else:
                # input already exists
                if fact_rule.supported_by:
                    # if the input has supported by info
                    # add those to the same one in self.facts
                    ind = self.facts.index(fact_rule)
                    for f in fact_rule.supported_by:
                        self.facts[ind].supported_by.append(f)
                else:
                    ind = self.facts.index(fact_rule)
                    self.facts[ind].asserted = True
        elif isinstance(fact_rule, Rule):
            if fact_rule not in self.rules:
                self.rules.append(fact_rule)
                for fact in self.facts:
                    self.ie.fc_infer(fact, fact_rule, self)
            else:
                if fact_rule.supported_by:
                    ind = self.rules.index(fact_rule)
                    for f in fact_rule.supported_by:
                        self.rules[ind].supported_by.append(f)
                else:
                    ind = self.rules.index(fact_rule)
                    self.rules[ind].asserted = True

    def kb_assert(self, fact_rule):
        """Assert a fact or rule into the KB

        Args:
            fact_rule (Fact or Rule): Fact or Rule we're asserting
        """
        printv("Asserting {!r}", 0, verbose, [fact_rule])
        self.kb_add(fact_rule)

    def kb_ask(self, fact):
        """Ask if a fact is in the KB

        Args:
            fact (Fact) - Statement to be asked (will be converted into a Fact)

        Returns:
            listof Bindings|False - list of Bindings if result found, False otherwise
        """
        print("Asking {!r}".format(fact))
        if factq(fact):
            f = Fact(fact.statement)
            bindings_lst = ListOfBindings()
            # ask matched facts
            for fact in self.facts:
                binding = match(f.statement, fact.statement)
                if binding:
                    bindings_lst.add_bindings(binding, [fact])

            return bindings_lst if bindings_lst.list_of_bindings else []

        else:
            print("Invalid ask:", fact.statement)
            return []

    def kb_delete(self, fact_or_rule):
        # recursively delete the supporting facts or rules
        # after deleting downwards, delete the upper one supporting this fact or rule
        # then remove this item from the knowledge base
        # at this stage all fact_or_rule will be in the database for sure

        is_fact = isinstance(fact_or_rule, Fact)
        is_rule = isinstance(fact_or_rule, Rule)
        if len(fact_or_rule.supported_by) == 0:
            printv("Deleting {!r}", 0, verbose, [fact_or_rule])
            if is_fact:
                self.facts.remove(fact_or_rule)
            if is_rule:
                self.rules.remove(fact_or_rule)
            for fact_to_delete in fact_or_rule.supports_facts:
                print(fact_to_delete)
                for i in fact_to_delete.supported_by:
                    if fact_or_rule in i:
                        fact_to_delete.supported_by.remove(i)
                self.kb_delete(fact_to_delete)

            for rule_to_delete in fact_or_rule.supports_rules:
                print(rule_to_delete)
                for i in rule_to_delete.supported_by:
                    if fact_or_rule in i:
                        rule_to_delete.supported_by.remove(i)
                self.kb_delete(rule_to_delete)


    def kb_retract(self, fact_or_rule):
        """Retract a fact from the KB

        Args:
            fact (Fact) - Fact to be retracted

        Returns:
            None
        """
        printv("Retracting {!r}", 0, verbose, [fact_or_rule])
        ####################################################
        # Student code goes here

        # first need to get the item from the knowledge base

        is_fact = isinstance(fact_or_rule, Fact)
        is_rule = isinstance(fact_or_rule, Rule)
        item_in_kb = None

        if is_fact:
            try:
                index = self.facts.index(fact_or_rule)
                item_in_kb = self.facts[index]
            except:
                print("ERROR: Retract Failed: item not in the knowledge base")
                return
        if is_rule:
            print("ERROR: Cannot retract rule")
            return

        if len(item_in_kb.supported_by) == 0:
            if is_fact:
                self.facts.remove(item_in_kb)

            for fact_to_delete in item_in_kb.supports_facts:
                # print(fact_to_delete)
                for i in fact_to_delete.supported_by:
                    if item_in_kb in i:
                        fact_to_delete.supported_by.remove(i)
                self.kb_delete(fact_to_delete)

            for rule_to_delete in item_in_kb.supports_rules:
                # print(rule_to_delete)
                for i in rule_to_delete.supported_by:
                    if item_in_kb in i:
                        rule_to_delete.supported_by.remove(i)
                self.kb_delete(rule_to_delete)




class InferenceEngine(object):
    def fc_infer(self, fact, rule, kb):
        """Forward-chaining to infer new facts and rules

        Args:
            fact (Fact) - A fact from the KnowledgeBase
            rule (Rule) - A rule from the KnowledgeBase
            kb (KnowledgeBase) - A KnowledgeBase

        Returns:
            Nothing
        """
        printv('Attempting to infer from {!r} and {!r} => {!r}', 1, verbose,
            [fact.statement, rule.lhs, rule.rhs])
        ####################################################
        # Student code goes here

        binding = match(fact.statement, rule.lhs[0])
        if binding:
            # print('Attempting to infer from %s and %s => %s' % (fact.statement, rule.lhs, rule.rhs))
            # fact matches to the lhs statement
            if len(rule.lhs) == 1:
                # if there is only one statement on lhs, then just asser the instantiated rhs
                # creating a new fact using instantiated rhs
                new_fact = Fact(instantiate(rule.rhs, binding))
                if new_fact in kb.facts:
                    new_fact = kb.facts[kb.facts.index(new_fact)]
                if [fact, rule] not in new_fact.supported_by:
                    new_fact.supported_by.append([fact, rule])
                fact.supports_facts.append(new_fact)
                rule.supports_facts.append(new_fact)
                # print("Adding fact by inference: ", new_fact)
                if new_fact not in kb.facts:
                    kb.kb_add(new_fact)
            else:
                # if multiple statements on lhs, remove the first one and instantiate the rest
                # creating a new rule list
                # parse that rule list to rule object
                rule_list = [[], None]
                for lhs_statement in rule.lhs[1:]:
                    rule_list[0].append(instantiate(lhs_statement, binding))
                rule_list[1] = instantiate(rule.rhs, binding)
                new_rule = Rule(rule_list)
                if new_rule in kb.rules:
                    new_rule = kb.rules[kb.rules.index(new_rule)]
                if [fact, rule] not in new_rule.supported_by:
                    new_rule.supported_by.append([fact, rule])
                fact.supports_rules.append(new_rule)
                rule.supports_rules.append(new_rule)
                # print("Adding rule by inference: ", new_rule)
                if new_rule not in kb.rules:
                    kb.kb_add(new_rule)
