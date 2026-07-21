"""Nielsen DMA reference for Datalogix DMA Code."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.intelligence.datalogix_engine import preserve_datalogix_value
from app.reference.nielsen_dma import DMA_BY_CODE, DMA_MARKETS, dma_market_name, lookup_dma, normalize_dma_code


def test_dma_reference_has_210_markets():
    assert len(DMA_MARKETS) == 210
    assert len(DMA_BY_CODE) == 210


def test_lookup_known_texas_dma_codes():
    dallas = lookup_dma("623")
    assert dallas is not None
    assert dallas.market_name == "Dallas-Fort Worth"
    assert dallas.rank_2024_25 == 4

    houston = lookup_dma("618")
    assert houston is not None
    assert houston.market_name == "Houston"

    phoenix = lookup_dma("753")
    assert phoenix is not None
    assert phoenix.market_name == "Phoenix (Prescott)"
    assert phoenix.rank_2024_25 == 12


def test_normalize_dma_code():
    assert normalize_dma_code("623") == "623"
    assert normalize_dma_code("53") == "053"
    assert normalize_dma_code("XXXX") == "XXXX"
    assert normalize_dma_code("x") is None
    assert dma_market_name("635") == "Austin"


def test_preserve_datalogix_dma_and_county_codes():
    assert preserve_datalogix_value("dma_code", "623") == "623"
    assert preserve_datalogix_value("dma_code", "XXXX") == "XXXX"
    assert preserve_datalogix_value("county_code", "a") == "A"
    assert preserve_datalogix_value("county_code", "XXXX") is None


if __name__ == "__main__":
    test_dma_reference_has_210_markets()
    test_lookup_known_texas_dma_codes()
    test_normalize_dma_code()
    test_preserve_datalogix_dma_and_county_codes()
    print("PASS: DMA reference")
