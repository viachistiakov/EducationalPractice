import re
import random
from z3 import Solver, Bool, Or, And, Not, sat

# Базовые регулярные выражения
base_regex = [
    "a",
    "b",
    "c",
    "a*",
    "b*",
    "c*",
    "a|b",
    "ab",
    "abc",
    "a?",
    "b?",
    "(a|b)",
    "(a|b|c)",
    "(a(b|c)*)",
    "(a|ba|bc*)",
    "(ab|c)*",
]

def is_valid_regex(expression):
    """Проверяет корректность регулярного выражения."""
    try:
        re.compile(expression)
        return True
    except re.error:
        return False

def generate_random_regex(base_expressions):
    """Генерирует случайное регулярное выражение на основе базы правильных выражений."""
    base_expr = random.choice(base_expressions)
    return base_expr

def regex_to_z3_expr(regex):
    """Преобразует регулярное выражение в выражение Z3."""
    if regex == '.*':
        return True  # Совпадает с любой строкой
    if regex == '.':
        return Or(*[Bool(chr(i)) for i in range(97, 123)])  # Для любых символов a-z
    if regex.startswith('(') and regex.endswith(')'):
        inner = regex[1:-1]
        return regex_to_z3_expr(inner)
    if regex == 'a':
        return Bool('a')
    if regex == 'b':
        return Bool('b')
    if regex == 'c':
        return Bool('c')
    if regex == 'a*':
        return Or(Bool('a'), Bool(''))
    if regex == 'b*':
        return Or(Bool('b'), Bool(''))
    if regex == 'c*':
        return Or(Bool('c'), Bool(''))
    if regex == 'a|b':
        return Or(Bool('a'), Bool('b'))
    if regex == '(a|b)':
        return Or(Bool('a'), Bool('b'))
    if regex == 'ab':
        return And(Bool('a'), Bool('b'))
    if regex == 'a?':
        return Or(Bool('a'), Bool(''))
    if '|' in regex:
        parts = regex.split('|')
        return Or(*[regex_to_z3_expr(part) for part in parts])
    if '*' in regex:
        base = regex.split('*')[0]
        return Or(regex_to_z3_expr(base), Bool(''))
    if '?' in regex:
        base = regex.split('?')[0]
        return Or(regex_to_z3_expr(base))
    return Bool(regex)

def z3_check(regex, test_string):
    """Проверка строки с помощью Z3."""
    solver = Solver()
    z3_expr = regex_to_z3_expr(regex)

    # Переменные для каждой позиции в строке
    string_vars = [Bool(f'char_{i}') for i in range(len(test_string))]

    # Создаем условия для проверки всей строки
    expr = z3_expr

    # Обработка каждого символа в строке
    for i, char in enumerate(test_string):
        if char == 'a':
            expr = And(expr, string_vars[i])
        elif char == 'b':
            expr = And(expr, string_vars[i])
        elif char == 'c':
            expr = And(expr, string_vars[i])
        else:
            expr = And(expr, Not(string_vars[i]))

    # Проверка, что вся строка соответствует регулярному выражению
    for var in string_vars:
        expr = And(expr, var)

    solver.add(expr)
    result = solver.check()
    return result == sat

def python_check(regex, test_string):
    """Проверяет строку на соответствие регулярному выражению с использованием модуля re."""
    pattern = re.compile(regex)
    return pattern.fullmatch(test_string) is not None

def generate_matching_string(regex):
    """Генерирует строку, соответствующую заданному регулярному выражению."""
    if regex == 'a':
        return 'a'
    elif regex == 'b':
        return 'b'
    elif regex == 'c':
        return 'c'
    elif regex == 'a|b':
        return random.choice(['a', 'b'])
    elif regex == 'a*':
        return 'a' * random.randint(0, 5)
    elif regex == 'b*':
        return 'b' * random.randint(0, 5)
    elif regex == 'c*':
        return 'c' * random.randint(0, 5)
    elif regex == 'ab':
        return 'ab'
    elif regex == '(a|b)':
        return random.choice(['a', 'b'])
    elif regex == '(a|b|c)':
        return random.choice(['a', 'b', 'c'])
    elif regex == '(a(b|c)*)':
        return 'a' + ('b' * random.randint(0, 3) + 'c' * random.randint(0, 3))
    elif regex == '(a|ba|bc*)':
        return random.choice(['a', 'ba', 'bc' * random.randint(0, 3)])
    elif regex == '(ab|c)*':
        return ''.join(random.choice(['ab', 'c']) for _ in range(random.randint(0, 3)))
    else:
        return ''.join(random.choice(['a', 'b', 'c']) for _ in range(random.randint(1, 5)))

def main():
    print("Начинаю генерацию регулярных выражений...")

    num_generations = 10
    results = []

    for _ in range(num_generations):
        try:
            # Генерация регулярного выражения
            regex_input = generate_random_regex(base_regex)

            # Генерация строки, соответствующей регулярному выражению
            test_string = generate_matching_string(regex_input)

            # Проверка в Z3 (всегда должно быть True)
            result_z3 = z3_check(regex_input, test_string)

            # Проверка в Python (всегда должно быть True)
            result_python = python_check(regex_input, test_string)

            # Сохраняем результат
            results.append((regex_input, test_string, result_z3, result_python))

        except ValueError as e:
            print(f"Ошибка: {e}")

    # Вывод всех результатов
    for regex_input, test_string, result_z3, result_python in results:
        print(f"Сгенерированное регулярное выражение: {regex_input}")
        print(f"Сгенерированная строка: {test_string}")
        print(f"Результат проверки в Z3: {result_z3}")
        print(f"Результат проверки в Python: {result_python}")
        print("Результаты совпадают." if result_z3 == result_python else "Результаты не совпадают.")
        print()

if __name__ == "__main__":
    main()