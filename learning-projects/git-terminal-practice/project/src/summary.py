# Читает текстовый файл и выводит краткую сводку.
# Невелика програма, яка читає текстовий файл і друкує зведення про нього.
# У цій практичній вона потрібна не заради самої програми, а щоб було що
# версіонувати: ви змінюватимете її в різних гілках і зливатимете зміни.

import sys


def read_words(path):
    """Повертає список слів із файлу."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    words = []
    current = ""
    for ch in text:
        if ch.isalpha() or ch in "'’ʼ":
            current = current + ch
        else:
            if current:
                words.append(current)
                current = ""
    if current:
        words.append(current)
    return words


def count_lines(path):
    """Повертає кількість рядків у файлі."""
    with open(path, encoding="utf-8") as f:
        return len(f.readlines())


def collect_stats(path):
    """Рахує всі показники одразу й складає їх у словник."""
    words = read_words(path)
    longest = ""
    total_length = 0
    for w in words:
        total_length = total_length + len(w)
        if len(w) > len(longest):
            longest = w
    average = total_length / len(words) if words else 0
    return {
        "lines": count_lines(path),
        "words": len(words),
        "longest": longest,
        "average": round(average, 2),
    }


def print_summary(stats):
    """Друкує зведення. САМЕ ЦЮ ФУНКЦІЮ ви змінюватимете у двох гілках."""
    print("=" * 30)
    print("Зведення")
    print("Рядків:", stats["lines"])
    print("Слів:", stats["words"])
    print("Найдовше слово:", stats["longest"])
    print("Середня довжина слова:", stats["average"])
    print("=" * 30)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../data/sample.txt"
    print_summary(collect_stats(path))
