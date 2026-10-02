"""S4 is furniture / FDA Class I — not Class II V Series (ceragemus.com)."""

from app.intelligence.product_ladders import CERAGEM_PRODUCT_LADDERS
from app.reference.registry import (
    FDA_CLASS_2_PRODUCTS,
    FURNITURE_DESIGN_PRODUCTS,
    V_SERIES_PRODUCTS,
    is_fda_class_2,
    product_family,
    product_line,
    regulatory_class,
)


def test_s4_is_not_fda_class_2():
    assert "Master S4" not in FDA_CLASS_2_PRODUCTS
    assert "Master S4" not in V_SERIES_PRODUCTS
    assert is_fda_class_2("Master S4") is False
    assert is_fda_class_2("Pause S4") is False
    assert is_fda_class_2("Master V4") is False


def test_v_series_is_fda_class_2_only():
    assert FDA_CLASS_2_PRODUCTS == frozenset({"Master V5", "Master V6", "Master V7", "Master V9"})
    assert V_SERIES_PRODUCTS == FDA_CLASS_2_PRODUCTS
    assert is_fda_class_2("Master V5") is True
    assert regulatory_class("Master V5") == "class_ii_510k"


def test_s4_is_furniture_class_i():
    assert "Master S4" in FURNITURE_DESIGN_PRODUCTS
    assert product_line("Master S4") == "S"
    assert product_line("Pause S4") == "S"
    assert product_family("Master S4") == "furniture_design"
    assert regulatory_class("Master S4") == "class_i_registered"


def test_low_pain_ladder_puts_v5_before_s4():
    assert CERAGEM_PRODUCT_LADDERS["Low+ · Pain Index"][0] == "Master V5"
    assert CERAGEM_PRODUCT_LADDERS["Low+ · Pain Index"][1] == "Master S4"
