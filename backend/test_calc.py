import pytest

from agents.data import calc


def test_basic():
    assert calc("2 + 2 * 3") == 8
    assert calc("(1500000 - 900000) / 12") == 50000
    assert calc("10,5 * 2") == 21
    assert calc("2^10") == 1024


@pytest.mark.parametrize("bad", ["__import__('os')", "open('x')", "2**1000", "[1]", "a+1"])
def test_rejects(bad):
    with pytest.raises(Exception):
        calc(bad)
