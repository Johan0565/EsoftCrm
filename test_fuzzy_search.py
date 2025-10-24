
import pytest
from algorithms import fuzzy_match

def test_exact_match_returns_true():
    # Полное совпадение — расстояние 0 ≤ порога
    assert fuzzy_match("Иван Иванов", "ivanov", "иван") is True

def test_under_threshold_is_true():
    # Разница в 1–2 символа проходит при max_dist=2
    assert fuzzy_match("Строка Тест", "stroka", "стрка", max_dist=2) is True

def test_over_threshold_is_false():
    # Слишком далеко от ФИО и от логина — не проходит
    assert fuzzy_match("Строка Тест", "stroka", "вафля", max_dist=2) is False

def test_query_compares_with_login_too():
    # Совпадение может быть по логину, даже если ФИО далеко
    assert fuzzy_match("Пользователь Тестовый", "ivanov", "ivann", max_dist=2) is True

def test_empty_query_always_true_and_case_insensitive():
    # Пустой запрос — True; регистр/пробелы игнорируются
    assert fuzzy_match("ПЕТРОВ ПЁТР", "petrov", "  пеТр  ", max_dist=2) is True
    assert fuzzy_match("Кто Угодно", "any", "", max_dist=0) is True
