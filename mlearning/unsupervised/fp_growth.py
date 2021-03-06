"""
    Data Mining: Determines frequent items in a transactional dataset
"""
from dataclasses import dataclass, field
from terminaltables import AsciiTable

from typing import Any, List
import itertools
import operator


@dataclass
class FPGrowth:
    """
        Builds an FP Growth tree, minable for collection
        of frequent dataset items.

        Parameters
        ----------
        min_support: float
            Minimum transaction ratio to deem an item as frequent
    """
    min_support: float = 0.333333
    tree: object = None
    frequent_items: List[int] = field(default_factory=list)
    prefixes: None = field(default_factory=dict, init=False)

    def find_frequents(self, transactions, suffix=None):
        """
            Gets frequent items sets from transactions
        """

        self.transactions = transactions
        self.frequent_items = self.__get_frequents_list(transactions)
        self.root = self.create_tree(transactions, self.frequent_items[:])
        self.summarize()
        self.determine_frequent_item_sets(transactions, suffix=suffix)

        return self.frequent_items

    def determine_frequent_item_sets(self, conditional_db, suffix=None):
        """
            Finds and updates frequent items from the conditional database
        """
        freq_items = self.frequent_items[:]
        tree = self.root

        if suffix:
            tree = self.create_tree(conditional_db, freq_items)
            self.frequent_items += (element + suffix for element in freq_items)

        for item_set in freq_items:
            self.get_prefixes(item_set, tree)
            conditional_db_ = []

            item_set_key = self.get_itemset_key(item_set)
            try:
                for elmnt in self.prefixes.get(item_set_key):
                    for i in range(elmnt['support']):
                        conditional_db_.append(elmnt['prefix'])
            except TypeError:
                pass
            else:
                new_suffix = item_set + suffix if suffix else item_set
                self.determine_frequent_item_sets(conditional_db_, new_suffix)

    def get_itemset_key(self, itset):
        """
            Joins contents of lists with more than a single item
        """
        return '-'.join(itset)

    def __get_frequents_list(self, db: 'list') -> list:
        """
            Gives a list of items whose occurence meets the min_support
        """
        uniques = set(itertools.chain(*db))
        transactions_count = [
            (item, self.get_transactions_count(item, db))
            for item in uniques
        ]

        fq_items = [
            (item, count) for item, count in transactions_count
            if count >= self.min_support]

        fq_items = [fq_item[0] for fq_item in sorted(
            fq_items,
            key=operator.itemgetter(1),
            reverse=True)
        ]

        return fq_items

    def get_prefixes(self, itemset, node, prefixes=None):
        """
            Adds prefixes to the item set by traversing the
            growth tree
        """
        prefixes = [] if not prefixes else prefixes

        if self.is_prefix(itemset, node):
            set_key = self.get_itemset_key(itemset)

            try:
                self.prefixes[set_key].append(
                    {
                        'prefix': prefixes,
                        'support': node.children[itemset[0]].support
                    }
                )
            except AttributeError:
                self.prefixes[set_key] = []

        for child in node.children:
            child = node.children[child]

            self.get_prefixes(itemset, child, prefixes + [child.node])

    def get_transactions_count(self, item, trans):
        """
            Finds the number of transactions in which an item is
            present
        """
        holding_transactions = [count for transaction in trans
                                for count in transaction if item in transaction
                                ]

        return len(holding_transactions)

    def is_prefix(self, itemset, node):
        """
            Asserts the element in the set is a child of the node
            and that all elements are acceisble through the first
        """
        for item in itemset:
            if item not in node.children:
                return False
            node = node.children[item]
        return True

    def create_tree(self, transactions, fq_items):
        """
            Creates the F Pattern growth tree
        """
        root = FPTreeNode()

        for transaction in transactions:
            transac = [item for item in transaction if item in fq_items]
            transac.sort(key=lambda item: fq_items.index(item))
            self.insert_node(root, transac)
        return root

    def insert_node(self, parent, nodes):
        """
            Inserts nodes to tree
        """
        try:
            child_ = nodes[0]
        except IndexError:
            return
        else:
            child = FPTreeNode(node=child_)

            if child_ in parent.children:
                parent.children[child.node].support += 1
            else:
                parent.children[child.node] = child

            self.insert_node(parent.children[child.node], nodes[1:])

    def summarize(self, node=None, indent=0, first_call=True):
        """
            Displayes the FP growth tree
        """
        if first_call:
            print(AsciiTable([['FP Growth Tree']]).table)

        node = self.root if not node else node
        display = f'   ' * indent + f'{node.node}: {node.support}\n'
        print(display)
        for child in node.children:
            self.summarize(node.children[child], indent + 1, False)


@dataclass
class FPTreeNode:
    """
        FP Tree item

        Parameters
        ----------
        node: float
            Value of the node
        support: float
            No. of occurrence in the transaction
        children: dict
            Child nodes in the growth tree
    """
    node: Any = field(default=None)
    support: int = 1
    children: Any = field(default_factory=dict)
