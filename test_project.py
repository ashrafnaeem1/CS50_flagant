"""
Tests for project.py — covers the three GUI-independent data-layer
functions: load_countries, fuzzy_search, get_flag_path.

The GUI (FlagantApp) isn't unit tested here — it needs a real display and
keyboard/click interaction to drive, which pytest can't do.

Run with: pytest test_project.py
"""
# Every test function below takes `countries` as a parameter, which is
# pytest's normal fixture-injection pattern — pylint doesn't recognize
# that pattern and flags it as "redefining" the fixture function itself.
# pylint: disable=redefined-outer-name
import pytest

from project import load_countries, fuzzy_search, get_flag_path


@pytest.fixture(scope="module")
def countries():
    """Loaded using load_countries()."""
    return load_countries()


# --- load_countries ---

def test_load_countries_returns_all_countries(countries):
    """pycountry ships 249 countries/territories as of this project's build.
    Test if load_countries() returns all of them."""
    assert len(countries) == 249


def test_load_countries_entry_shape(countries):
    """Every entry should be a dict with exactly a name and an alpha2 code."""
    for country in countries:
        assert set(country.keys()) == {"name", "alpha2"}
        # country name is a string AND contains some value (not empty.)
        assert isinstance(country["name"], str) and country["name"]
        # over here, the AND followup for empty check is Not strictly needed.
        # as we are already checking for exact length of two.
        assert isinstance(country["alpha2"], str)
        assert len(country["alpha2"]) == 2


def test_load_countries_includes_known_countries(countries):
    """Manual test for a few countries - India, Germany, Japan."""
    names_by_code = {c["alpha2"]: c["name"] for c in countries}
    assert names_by_code["IN"] == "India"
    # Germany's alpha2 comes from 'de'utschland, it's german name.
    assert names_by_code["DE"] == "Germany"
    assert names_by_code["JP"] == "Japan"


# --- fuzzy_search ---

def test_fuzzy_search_empty_query_returns_nothing(countries):
    """Empty string fuzzy search should return empty matches."""
    assert fuzzy_search("", countries) == []
    assert fuzzy_search("   ", countries) == []


def test_fuzzy_search_prefix_match_ranks_first(countries):
    """For fuzzy search, prefix ranking is preffered over pure fuzzy ranking,
    "fra" should surface France first, not some unrelated country that
    only shares a few letters with it."""
    results = fuzzy_search("fra", countries)
    assert results[0]["name"] == "France"


def test_fuzzy_search_typo_tolerance(countries):
    """Should fallback to typo tolerant fuzzy search. For example:
    "jermany" (typo for "germany") should still find Germany, via the
    fuzzy fallback tier rather than the exact substring tier."""
    results = fuzzy_search("jermany", countries)
    assert any(c["name"] == "Germany" for c in results)


def test_fuzzy_search_respects_limit(countries):
    """Limit of top matches can be configured in fuzzy_search()."""
    results = fuzzy_search("united", countries, limit=2)
    assert len(results) <= 2


def test_fuzzy_search_is_case_insensitive(countries):
    """Search must be case insensitive."""
    assert fuzzy_search("germany", countries) == fuzzy_search(
        "GERMANY", countries)


# --- get_flag_path ---

def test_get_flag_path_existing_flag():
    """Note: The success of get_flag_path() depends on directory structure and
    flag availability. As such this test assumes ideal conditions only.
    This test may fail, not only due to failure of get_flag_path(), but also
    due to project structure."""
    path = get_flag_path("DE")
    assert path is not None
    assert path.endswith("de.png")


def test_get_flag_path_is_case_insensitive_on_code():
    """Codes should be handled with case INsensitivity.
    For eg. codes 'de' and 'DE' are one and the same. for get_flag_path()."""
    assert get_flag_path("de") == get_flag_path("DE")


def test_get_flag_path_missing_flag_returns_none():
    """get_flag_path() deals with cases where the flag file is missing
    by returning None which the parent can use to know if the flag is missing.
    This also happens if the passed code is not valid at all, for eg. "ZZ" is
    not a valid alpha2 code as far as the scope of my project goes."""
    assert get_flag_path("ZZ") is None
