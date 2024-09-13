import re
import random
import keyboard
from z3 import Solver, Bool, Or, And, Not, sat

# База правильных регулярных выражений
base_regex = [
    "a*.",
    ".a?b?",
    "(a|b)*",
    "a?b",
    "c*",
    "a.b|c",
    "c|d*",
    "|a*|",
    "c*.*",
    ".(a|b)*?",
    "c|d.*",
    "c*.|",
    "a?b()",
    "(a|b)*.?",
    ".*c*",
    "a*|.",
    "a?b.*",
    "(a|b)*..",
    ".?c*",
    "(a|b)*?.",
    ".|a.b|c"
]

def is_valid_regex(expression):
    """Проверяет корректность регулярного выражения."""
    try:
        re.compile(expression)
        return True
    except re.error:
        return False

def generate_random_regex(base_expressions, num_modifications=2):
    """Генерирует случайное регулярное выражение на основе базы правильных выражений."""
    base_expr = random.choice(base_expressions)
    regex_parts = [base_expr]

    for _ in range(num_modifications):
        modification_type = random.choice(['operator', 'group'])

        if modification_type == 'operator':
            operator = random.choice(['*', '.', '|', '?'])
            if random.choice([True, False]):
                # Вставка оператора в случайное место
                insert_position = random.randint(0, len(regex_parts) - 1)
                regex_parts.insert(insert_position, operator)
            else:
                # Применение оператора к случайной части
                apply_position = random.randint(0, len(regex_parts) - 1)
                regex_parts[apply_position] += operator
        elif modification_type == 'group':
            group_type = random.choice(['(', ')'])
            insert_position = random.randint(0, len(regex_parts))
            regex_parts.insert(insert_position, group_type)

    generated_regex = ''.join(regex_parts)

    if not is_valid_regex(generated_regex):
        return generate_random_regex(base_expressions, num_modifications)

    return generated_regex

def regex_to_z3_expr(regex):
    """Преобразует регулярное выражение в выражение Z3."""
    # Простой пример преобразования регулярного выражения в выражение Z3
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
    if '|' in regex:
        parts = regex.split('|')
        return Or(*[regex_to_z3_expr(part) for part in parts])
    if '.' in regex:
        parts = regex.split('.')
        return And(*[regex_to_z3_expr(part) for part in parts])
    if '*' in regex:
        base = regex.split('*')[0]
        return Or(regex_to_z3_expr(base), Bool(''))
    if '?' in regex:
        base = regex.split('?')[0]
        return Or(regex_to_z3_expr(base), Bool(''))
    return Bool(regex)  # Для простоты

def z3_check(regex, test_string):
    """Проверка строки с помощью Z3."""
    solver = Solver()
    z3_expr = regex_to_z3_expr(regex)

    # Переменные для каждой позиции в строке
    string_vars = [Bool(f'char_{i}') for i in range(len(test_string))]

    # Создаем условия для проверки строки
    expr = z3_expr
    for i, char in enumerate(test_string):
        if char == 'a':
            expr = And(expr, string_vars[i])
        else:
            expr = And(expr, Not(string_vars[i]))

    solver.add(expr)
    result = solver.check()
    return result == sat

def python_check(regex, test_string):
    """Проверка строки с помощью Python."""
    try:
        pattern = re.compile(regex)
        return bool(pattern.fullmatch(test_string))
    except re.error:
        return False

def generate_random_string():
    """Генерирует случайную строку для проверки регулярного выражения."""
    alphabet = ['a', 'b', 'c', '1', '2', '3']
    length = random.randint(1, 5)
    return ''.join(random.choice(alphabet) for _ in range(length))

def main():
    print("Начинаю генерацию регулярных выражений...")

    num_generations = 50
    matching_results = 0

    for _ in range(num_generations):
        try:
            # Генерация регулярного выражения
            regex_input = generate_random_regex(base_regex)

            # Генерация строки
            test_string = generate_random_string()

            # Проверка в Z3
            result_z3 = z3_check(regex_input, test_string)

            # Проверка в Python
            result_python = python_check(regex_input, test_string)

            # Сравнение результатов
            if result_z3 == result_python:
                matching_results += 1
                print(f"Сгенерированное регулярное выражение: {regex_input}")
                print(f"Сгенерированная строка: {test_string}")
                print(f"Результат проверки в Z3: {result_z3}")
                print(f"Результат проверки в Python: {result_python}")
                print("Результаты совпадают.")
                print()

        except ValueError as e:
            print(f"Ошибка: {e}")

    print(f"Количество совпадающих результатов: {matching_results}")

if __name__ == "__main__":
    main()