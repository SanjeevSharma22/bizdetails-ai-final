import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.app.normalization import normalize_company_name
import pytest

@pytest.mark.parametrize(
    "original,expected",
    [
        ("Apple Inc.", "Apple"),
        ("Google LLC", "Google"),
        ("Global Innovations pvt ltd", "Global Innovations"),
        ("Nestlé S.A.", "Nestlé"),
        ("Procter & Gamble", "Procter & Gamble"),
        ("A.P. Moller - Maersk", "A.P. Moller - Maersk"),
        ("The Coca-Cola Company", "The Coca-Cola"),
        ("Foo LLP.", "Foo"),
    ],
)
def test_normalize_company_name(original, expected):
    assert normalize_company_name(original) == expected
