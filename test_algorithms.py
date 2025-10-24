
import math
from algorithms import levenshtein, fuzzy_match, quality_component, compute_priorities

def test_lev_cases():
    assert levenshtein('строка','строка') == 0
    assert levenshtein('','') == 0
    assert levenshtein('строка','строкаа') == 1
    assert levenshtein('кот','кит') == 1
    assert levenshtein('строка','собака') == 3
    assert levenshtein('строка','вафля') >= 6

def test_fuzzy_match():
    assert fuzzy_match('Строка Тест','login','строка') is True
    assert fuzzy_match('Иванов Иван','ivanov','строка') is False
    assert fuzzy_match('Иванов Иван','ivanov','иванов') is True
    assert fuzzy_match('','petrov','петров') is True
    assert fuzzy_match('Пупкин','pupkin','') is True

def test_quality_component():
    assert quality_component([0,0,0],[0,0,0]) == 0.0
    assert math.isclose(quality_component([1,1,1],[1,1,1]), 1.0, rel_tol=1e-6)
    assert math.isclose(quality_component([1,0.5,0.0],[0.5,0.5,1.0]), (1*0.5+0.5*0.5+0*1.0)/3.0, rel_tol=1e-6)
    assert math.isclose(quality_component([1,0.5],[0.5,0.5,0.5]), (1*0.5+0.5*0.5)/3.0, rel_tol=1e-6)
    assert quality_component(None, [1,1,1]) == 0.0

def test_priorities_operational_rule():
    users = [{'id': 1, 'L': 5, 'A': 3, 'sp':0.2,'so':0.2,'ss':0.2},
             {'id': 2, 'L': 7, 'A': 0, 'sp':0.1,'so':0.1,'ss':0.1}]
    cand, meta = compute_priorities(users, [0.3,0.3,0.3], 0.33,0.33,0.34)
    assert cand[0]['id'] == 2
