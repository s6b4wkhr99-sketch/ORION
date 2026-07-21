"""Data Commons ZIP income client tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.geo.datacommons_client import _parse_observation_response, _pick_observation


def test_pick_observation_prefers_acs_facet():
    entity_payload = {
        "orderedFacets": [
            {
                "facetId": "inflation",
                "observations": [{"date": "2024", "value": 999999}],
            },
            {
                "facetId": "acs",
                "observations": [{"date": "2022", "value": 119388}],
            },
        ]
    }
    facets = {
        "inflation": {"importName": "CensusACS5YearSurvey_SubjectTables_S1901"},
        "acs": {"importName": "CensusACS5YearSurvey"},
    }
    income, source = _pick_observation(entity_payload, facets)
    assert income == 119388
    assert source == "CensusACS5YearSurvey"


def test_parse_observation_response_maps_zip_entities():
    payload = {
        "byVariable": {
            "Median_Income_Household": {
                "byEntity": {
                    "zip/19063": {
                        "orderedFacets": [
                            {
                                "facetId": "acs",
                                "observations": [{"date": "2022", "value": 119388}],
                            }
                        ]
                    },
                    "zip/90210": {
                        "orderedFacets": [
                            {
                                "facetId": "acs",
                                "observations": [{"date": "2022", "value": 172285}],
                            }
                        ]
                    },
                }
            }
        },
        "facets": {"acs": {"importName": "CensusACS5YearSurvey"}},
    }
    result = _parse_observation_response(payload)
    assert result == {"19063": 119388.0, "90210": 172285.0}
