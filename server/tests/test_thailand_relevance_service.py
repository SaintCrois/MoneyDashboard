"""Thailand relevance classification tests."""

from app.services.thailand_relevance_service import (
    INTERNATIONAL,
    THAILAND_FOCUSED,
    THAILAND_RELATED,
    UNCERTAIN,
    classify_thailand_relevance,
)


def test_thailand_focused_article():
    """Explicit Thailand domestic/business reference -> Thailand-focused."""
    result = classify_thailand_relevance(
        "PTT announces new investment in Thailand's energy infrastructure",
        "PTT Public Company Limited will invest in new facilities in Bangkok.",
        None,
    )
    assert result.classification == THAILAND_FOCUSED
    assert result.reason


def test_thailand_focused_by_thailand_reference():
    result = classify_thailand_relevance(
        "Thailand tourism arrivals surge in Phuket",
        "Bangkok officials reported higher visitor numbers across Thailand.",
        None,
    )
    assert result.classification == THAILAND_FOCUSED


def test_thailand_related_international_article():
    """Mentions Thailand/Thai entity in international context -> Thailand-related."""
    result = classify_thailand_relevance(
        "Oil prices rise globally, Thailand braces for higher fuel costs",
        "Global crude markets moved higher; Thai consumers may face higher prices.",
        None,
    )
    assert result.classification in (THAILAND_FOCUSED, THAILAND_RELATED)
    assert result.reason


def test_thailand_related_thai_company_indicator():
    result = classify_thailand_relevance(
        "Global investors watch SCB digital banking expansion",
        "Kasikorn and other Thai banks expand regional services.",
        None,
    )
    assert result.classification == THAILAND_RELATED


def test_unrelated_international_article():
    """No Thailand/Thai entity references -> International."""
    result = classify_thailand_relevance(
        "UK civil servants face new pension policy",
        "The United Kingdom announced changes to civil servant pensions in London.",
        "Government officials in Britain discussed reforms.",
    )
    assert result.classification == INTERNATIONAL
    assert result.reason


def test_uncertain_article():
    """Insufficient/ambiguous signals -> Uncertain."""
    result = classify_thailand_relevance(
        "New framework discussed at conference",
        "Experts shared views on a new framework.",
        None,
    )
    assert result.classification == UNCERTAIN
    assert result.reason


def test_empty_text_uncertain():
    result = classify_thailand_relevance(None, None, None)
    assert result.classification == UNCERTAIN
    assert "Insufficient text" in result.reason


def test_thai_publisher_alone_not_thailand_related():
    """Coming from Thai publisher must not by itself make it Thailand-related.

    Classification is based on article text, not source name; this test ensures
    unrelated international text stays International.
    """
    result = classify_thailand_relevance(
        "US Federal Reserve holds interest rates steady",
        "The Fed kept rates unchanged amid inflation concerns in the United States.",
        None,
    )
    assert result.classification == INTERNATIONAL
