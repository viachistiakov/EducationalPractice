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


def build_parse_tree(expression):
    expression = expression.replace('?', '|')  # Опцию заменяем на альтернативу
    return parse_alternatives(expression)


def parse_alternatives(expression):
    segments = []
    segment = ""
    balance = 0

    for char in expression:
        if char == '(':
            balance += 1
        elif char == ')':
            balance -= 1

        if char == '|' and balance == 0:
            segments.append(segment)
            segment = ""
        else:
            segment += char

    if segment:
        segments.append(segment)

    if len(segments) > 1:
        node = TreeNode('|')
        node.left = parse_alternatives(segments[0])
        node.right = parse_alternatives("|".join(segments[1:]))
        return node

    return parse_concatenations(expression)


def parse_concatenations(expression):
    segments = []
    segment = ""
    balance = 0

    for i, char in enumerate(expression):
        if char == '(':
            balance += 1
        elif char == ')':
            balance -= 1

        if balance == 0 and (i == len(expression) - 1 or expression[i + 1] not in ('|', '*', '(', ')')):
            segment += char
            segments.append(segment)
            segment = ""
        else:
            segment += char

    if segment:
        segments.append(segment)

    if len(segments) > 1:
        node = TreeNode('.')
        node.left = parse_concatenations(segments[0])
        node.right = parse_concatenations("".join(segments[1:]))
        return node

    return parse_iterations(expression)


def parse_iterations(expression):
    if expression.endswith('*'):
        node = TreeNode('*')
        node.left = parse_primary(expression[:-1])
        return node

    return parse_primary(expression)


def parse_primary(expression):
    if expression.startswith('(') and expression.endswith(')'):
        return parse_alternatives(expression[1:-1])

    return TreeNode(expression)


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
        # Узел
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
        print(f"Ассоциативность соблюдается для узла: {node.label}")
    else:
        print(f"Ассоциативность не соблюдается для узла: {node.label}")


if __name__ == "__main__":
    while True:
        # Запрос ввода данных у пользователя
        regex_input = input("Введите регулярное выражение для разбора (или 'quit' для выхода): ").strip()

        if regex_input.lower() == 'quit':
            print("Выход из программы.")
            break

        try:
            # Обработка регулярного выражения
            parse_tree = build_parse_tree(regex_input)
            print("Дерево разбора регулярного выражения:")
            display_tree(parse_tree)  # Вывод в консоль
            graph = create_graph(parse_tree)  # Создание графа
            save_and_open_graph(graph)  # Сохранение и открытие графа
            verify_associativity(parse_tree)

        except Exception as e:
            print(f"Произошла ошибка: {e}")