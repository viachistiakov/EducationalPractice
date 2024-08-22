import re
from z3 import Solver, Bool, Or, And, sat
from graphviz import Digraph
import os
import subprocess


class TreeNode:
    def __init__(self, label, left=None, right=None):
        self.label = label
        self.left = left
        self.right = right

    def __repr__(self):
        if self.left is None and self.right is None:
            return f"Leaf({self.label})"
        return f"Node({self.label}, {self.left}, {self.right})"


def is_valid_regex(expression):
    """Проверяет корректность регулярного выражения."""
    try:
        re.compile(expression)
        return True
    except re.error:
        return False


def validate_empty_groups(expression):
    """Проверяет наличие пустых групп в регулярном выражении."""
    pattern = re.compile(r'\(\s*\)')
    if pattern.search(expression):
        raise ValueError("Ошибка: Пустая группа '()' в регулярном выражении.")


def tokenize(regex):
    tokens = []
    i = 0
    while i < len(regex):
        if regex[i] in {'(', ')', '*', '|'}:
            tokens.append(regex[i])
            i += 1
        else:
            if regex[i] == 'ε':
                tokens.append('ε')
                i += 1
            else:
                tokens.append(regex[i])
                i += 1
    return tokens


def to_rpn(tokens):
    precedence = {'*': 3, '.': 2, '|': 1}
    output = []
    stack = []

    # Добавление явных операторов конкатенации
    i = 0
    result = []
    while i < len(tokens):
        token = tokens[i]
        result.append(token)
        if token not in {'(', '|'} and i + 1 < len(tokens):
            next_token = tokens[i + 1]
            if next_token not in {')', '*', '|'}:
                result.append('.')
        i += 1
    tokens = result

    for token in tokens:
        if token.isalnum() or token == 'ε':
            output.append(token)
        elif token == '(':
            stack.append(token)
        elif token == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()  # Удаляем '('
        else:  # Операторы
            while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence.get(token, 0):
                output.append(stack.pop())
            stack.append(token)

    while stack:
        output.append(stack.pop())

    return output


def build_parse_tree_from_rpn(rpn):
    stack = []
    for token in rpn:
        if token == '*':
            if not stack:
                raise ValueError("Недостаточно операндов для '*'.")
            node = TreeNode('*', left=stack.pop())
            stack.append(node)
        elif token == '.':
            if len(stack) < 2:
                raise ValueError("Недостаточно операндов для '.'.")
            right = stack.pop()
            left = stack.pop()
            node = TreeNode('.', left=left, right=right)
            stack.append(node)
        elif token == '|':
            if len(stack) < 2:
                raise ValueError("Недостаточно операндов для '|'.")
            right = stack.pop()
            left = stack.pop()
            node = TreeNode('|', left=left, right=right)
            stack.append(node)
        else:  # Это буква или пустое слово (ε)
            stack.append(TreeNode(token))

    if len(stack) != 1:
        raise ValueError("Некорректное выражение, стек не пуст после обработки RPN.")

    return stack[0] if stack else None


def display_tree(node, depth=0):
    """Функция для вывода дерева в консоль."""
    indent = "  " * depth
    print(indent + node.label)
    if node.left:
        display_tree(node.left, depth + 1)
    if node.right:
        display_tree(node.right, depth + 1)


def add_nodes_edges(node, graph, node_id=0, parent_id=None):
    """Функция для добавления узлов и рёбер в граф Graphviz."""
    if node is not None:
        current_id = node_id
        node_id += 1

        # Выбор цвета узла в зависимости от метки
        if node.label == '|':
            node_color = 'lightblue'  # Цвет для альтернативы
        elif node.label == '.':
            node_color = 'lightgreen'  # Цвет для конкатенации
        elif node.label == '*':
            node_color = 'lightyellow'  # Цвет для итерации
        else:
            node_color = 'lightgrey'  # Цвет для букв или пустых меток

        # Узлы
        graph.node(f'{current_id}', label=node.label, shape='ellipse', style='filled', color=node_color,
                   fontcolor='black', fontsize='14', width='1.2', height='0.8')

        # Связи
        if parent_id is not None:
            graph.edge(f'{parent_id}', f'{current_id}', color='black', arrowsize='0.7', penwidth='2')

        if node.left:
            node_id = add_nodes_edges(node.left, graph, node_id, current_id)
        if node.right:
            node_id = add_nodes_edges(node.right, graph, node_id, current_id)

    return node_id


def create_graph(node):
    """Функция для создания графа с помощью Graphviz."""
    graph = Digraph(comment='Parse Tree')
    graph.attr(size='10,10', rankdir='TB', fontsize='16', fontname='Arial', dpi='300')  # Настройки графа
    add_nodes_edges(node, graph)
    return graph


def save_and_open_graph(graph, filename='parse_tree'):
    """Функция для сохранения и открытия графа."""
    graph.render(filename, format='png', cleanup=True)
    image_path = f'{filename}.png'
    if os.path.exists(image_path):
        subprocess.run(['start', image_path], shell=True)  # Открывает изображение в Windows


def verify_associativity(node):
    """Функция для проверки ассоциативности регулярных выражений."""
    solver = Solver()

    def add_constraints(node, level=0):
        if node.label == '|':
            if node.left:
                add_constraints(node.left, level + 1)
            if node.right:
                add_constraints(node.right, level + 1)
            left_expr = Bool(f'left_{level}')
            right_expr = Bool(f'right_{level}')
            solver.add(Or(left_expr, right_expr))
        elif node.label == '.':
            if node.left:
                add_constraints(node.left, level + 1)
            if node.right:
                add_constraints(node.right, level + 1)
            left_expr = Bool(f'left_{level}')
            right_expr = Bool(f'right_{level}')
            solver.add(And(left_expr, right_expr))
        elif node.label == '*':
            if node.left:
                add_constraints(node.left, level + 1)
            expr = Bool(f'expr_{level}')
            solver.add(expr)
        else:
            expr = Bool(f'expr_{level}')
            solver.add(expr)

    add_constraints(node)

    if solver.check() == sat:
        print(f"Associativity is satisfied for node: {node.label}")
    else:
        print(f"Associativity is not satisfied for node: {node.label}")


class SMT2Converter:
    def __init__(self, root):
        self.root = root

    def convert(self):
        return self._convert_node(self.root)

    def _convert_node(self, node):
        # Если это оператор объединения
        if node.label == '|':
            return f"(re.union {self._convert_node(node.left)} {self._convert_node(node.right)})"
        # Если это оператор конкатенации
        elif node.label == '.':
            left = self._convert_node(node.left)
            right = self._convert_node(node.right)

            # Объединяем строки, если оба потомка - листы с одиночными символами или строками
            if left.startswith('(str.to_re "') and right.startswith('(str.to_re "'):
                # Извлекаем содержимое строк
                left_str = left[len('(str.to_re "'): -2]
                right_str = right[len('(str.to_re "'): -2]
                # Возвращаем объединенную строку
                return f'(str.to_re "{left_str + right_str}")'
            else:
                # В случае более сложных выражений, просто объединяем их через re.++
                return f"(re.++ {left} {right})"
        # Если это оператор замыкания Клини
        elif node.label == '*':
            return f"(re.* {self._convert_node(node.left)})"
        # Лист дерева - отдельный символ
        else:
            return f'(str.to_re "{node.label}")'




def main():
    while True:
        regex = input("Введите регулярное выражение для разбора (или 'quit' для выхода): ").strip()
        if regex.lower() == 'quit':
            break

        if not is_valid_regex(regex):
            print("Некорректное регулярное выражение. Попробуйте еще раз.")
            continue

        try:
            validate_empty_groups(regex)
            tokens = tokenize(regex)
            rpn = to_rpn(tokens)
            parse_tree = build_parse_tree_from_rpn(rpn)
            print("Дерево разбора регулярного выражения:")
            display_tree(parse_tree)
            verify_associativity(parse_tree)
            converter = SMT2Converter(parse_tree)
            smt2_repr = converter.convert()
            print("SMT2 представление для выражения:")
            print(smt2_repr)
            graph = create_graph(parse_tree)
            save_and_open_graph(graph)
        except ValueError as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()