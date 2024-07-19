from z3 import *


class Node:
    def __init__(self, label, left=None, right=None):
        self.label = label
        self.left = left
        self.right = right


def build_parse_tree(regex):
    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

    stack = []
    index = 0

    def parse_expression():
        nonlocal index
        node = None

        while index < len(regex):
            if regex[index] in alphabet or regex[index] == '':
                node = Node('char', regex[index])
                index += 1
            elif regex[index] == '(':
                index += 1
                node = parse_expression()
            elif regex[index] == '|':
                node = Node('op', '|', left=stack[-1], right=parse_expression())
            elif regex[index] == '*':
                node = Node('op', '*', left=stack[-1])
            elif regex[index] == '?':
                node = Node('op', '?', left=stack[-1])

            if node is not None:
                stack.append(node)

        return stack.pop()

    parse_tree = parse_expression()
    return parse_tree


# Example usage
regex = "a|ba|bc*a"
parse_tree = build_parse_tree(regex)


# Output the parse tree
def print_tree(node, level=0):
    if node:
        print(" " * level + str(node.label))
        level += 1
        print_tree(node.left, level)
        print_tree(node.right, level)


print_tree(parse_tree)