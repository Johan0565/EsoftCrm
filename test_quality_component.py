
import math
from algorithms import quality_component

def test_basic_dot_over_three():
    s = [1.0, 0.5, 0.0]
    r = [0.5, 0.5, 1.0]
    expected = (1.0*0.5 + 0.5*0.5 + 0.0*1.0) / 3.0
    assert math.isclose(quality_component(s, r), expected, rel_tol=1e-9)

def test_clipped_to_first_three_components_when_longer():
    # Берём только первые 3 компоненты
    s = [1, 1, 1, 1, 1]
    r = [0.2, 0.2, 0.2, 0.2]
    expected = (1*0.2 + 1*0.2 + 1*0.2) / 3.0
    assert math.isclose(quality_component(s, r), expected, rel_tol=1e-9)

def test_min_length_less_than_three_penalizes_by_dividing_by_three():
    # Если векторы короче трёх — деление всё равно на 3
    s = [1.0, 0.0]   # длина 2
    r = [1.0, 1.0]   # длина 2
    expected = (1.0*1.0 + 0.0*1.0) / 3.0
    assert math.isclose(quality_component(s, r), expected, rel_tol=1e-9)

def test_accepts_strings_and_floats_and_bounds_0_1():
    s = ["0.7", 0.2, "0.1"]    # допускаются строки — в коде есть float()
    r = [1, "0.5", 0.0]
    q = quality_component(s, r)
    expected = (0.7*1.0 + 0.2*0.5 + 0.1*0.0) / 3.0
    assert 0.0 <= q <= 1.0
    assert math.isclose(q, expected, rel_tol=1e-9)

def test_empty_or_none_vectors_return_zero():
    assert quality_component([], [1, 1, 1]) == 0.0
    assert quality_component([1, 1, 1], []) == 0.0
    assert quality_component(None, [1, 1, 1]) == 0.0
    assert quality_component([1, 1, 1], None) == 0.0
