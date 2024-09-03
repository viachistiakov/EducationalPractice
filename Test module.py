import re
from z3 import Solver, Bool, Or, And, Not, sat
import random


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
        if regex[i] in {'(', ')', '*', '|', '?'}:
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
            if next_token not in {')', '*', '|', '?'}:
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
                raise ValueError(f"Недостаточно операндов для '.'. Операнды: {stack}")
            right = stack.pop()
            left = stack.pop()
            node = TreeNode('.', left=left, right=right)
            stack.append(node)
        elif token == '|':
            if len(stack) < 2:
                raise ValueError(f"Недостаточно операндов для '|'. Операнды: {stack}")
            right = stack.pop()
            left = stack.pop()
            node = TreeNode('|', left=left, right=right)
            stack.append(node)
        else:  # Это буква или пустое слово (ε)
            stack.append(TreeNode(token))

    if len(stack) != 1:
        raise ValueError(f"Некорректное выражение, стек не пуст после обработки RPN. Содержимое стека: {stack}")

    return stack[0] if stack else None


def display_tree(node, depth=0):
    """Функция для вывода дерева в консоль."""
    indent = "  " * depth
    print(indent + node.label)
    if node.left:
        display_tree(node.left, depth + 1)
    if node.right:
        display_tree(node.right, depth + 1)


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
        elif node.label == '?':
            if node.left:
                add_constraints(node.left, level + 1)
            expr = Bool(f'expr_{level}')
            solver.add(Or(expr, Bool('ε')))  # Закрыта скобка

    add_constraints(node)

    if solver.check() == sat:
        print(f"Ассоциативность соблюдается для узла: {node.label}")
    else:
        print(f"Ассоциативность не соблюдается для узла: {node.label}")


def generate_random_regex():
    operators = ['*', '.', '|']
    alphabet = ['a', 'b', 'c', '1', '2', '3']
    regex = []

    # Стартовый случайный символ
    regex.append(random.choice(alphabet))

    # Добавление случайных операторов и символов
    for _ in range(random.randint(1, 5)):
        operator = random.choice(operators)
        if operator in ['*', '?']:
            regex.append(operator)
        elif operator in ['.', '|']:
            regex.append(random.choice(alphabet))
            regex.append(operator)
        else:
            regex.append(random.choice(alphabet))

    # Завершающий символ
    regex.append(random.choice(alphabet))

    return ''.join(regex)


def generate_test_string():
    alphabet = ['a', 'b', 'c', '1', '2', '3']
    length = random.randint(1, 5)
    return ''.join(random.choice(alphabet) for _ in range(length))


def generate_random_string(alphabet, length=5):
    """Генерация случайной строки из алфавита."""
    return ''.join(random.choice(alphabet) for _ in range(length))


def python_check(regex, test_string):
    """Проверка строки с помощью Python."""
    try:
        return re.fullmatch(regex, test_string) is not None
    except re.error:
        return False


def z3_check(regex, test_string):
    """Проверка строки с помощью Z3."""
    solver = Solver()

    def regex_to_z3_expr(regex):
        if regex == 'a':
            return Bool('a')
        if regex == 'a*':
            return Or(Bool('a'), Bool(''))
        if regex == 'a|b':
            return Or(Bool('a'), Bool('b'))
        if regex == 'a.b':
            return And(Bool('a'), Bool('b'))
        if regex == 'a?':
            return Or(Bool('a'), Bool(''))
        return None

    z3_expr = regex_to_z3_expr(regex)
    if z3_expr is None:
        return False

    test_string_var = Bool('test_string')
    solver.add(z3_expr == test_string_var)
    solver.add(test_string_var == test_string)

    result = solver.check()
    return result == sat


if __name__ == "__main__":
    while True:
        # Генерация случайных данных
        regex_input = generate_random_regex()
        test_string = generate_random_string('abc123')

        print(f"Generated regular expression: {regex_input}")
        print(f"Generated test string: {test_string}")

        if not is_valid_regex(regex_input):
            print(f"Ошибка: Некорректное регулярное выражение '{regex_input}'.")
            continue

        try:
            # Проверка на пустые группы
            validate_empty_groups(regex_input)

            tokens = tokenize(regex_input)
            rpn = to_rpn(tokens)
            parse_tree = build_parse_tree_from_rpn(rpn)
            print("Дерево разбора регулярного выражения:")
            display_tree(parse_tree)  # Вывод в консоль
            verify_associativity(parse_tree)

            # Проверка соответствия с помощью Python и Z3
            python_result = python_check(regex_input, test_string)
            z3_result = z3_check(regex_input, test_string)
            print(f"Python result: {python_result}")
            print(f"Z3 result: {z3_result}")

            if python_result == z3_result:
                print("Результаты проверки совпадают.")
            else:
                print("Результаты проверки не совпадают.")

        except Exception as e:
            print(f"Произошла ошибка: {e}")

        if input("Enter 'quit' to exit or press Enter to continue: ").strip().lower() == 'quit':
            print("Выход из программы.")
            break
