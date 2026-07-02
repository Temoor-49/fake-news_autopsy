# tools/timeline_builder.py
# Organizes articles chronologically to help trace how a story spread

from datetime import datetime


def parse_date(date_str: str) -> datetime:
    """
    Safely parses various date formats into a datetime object.
    Returns datetime.min if parsing fails (so it sorts to the bottom).
    """
    if not date_str:
        return datetime.min

    # NewsAPI format: 2024-05-01T12:30:00Z
    formats_to_try = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for fmt in formats_to_try:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return datetime.min


def build_timeline(news_results: list[dict]) -> list[dict]:
    """
    Takes a list of news articles (with published_at field)
    and returns them sorted chronologically, oldest first.

    This helps identify which article appeared FIRST — 
    a strong signal of the origin point of a story.
    """

    # Filter out articles with no date info
    dated_articles = [a for a in news_results if a.get("published_at")]

    # Sort chronologically — oldest first
    sorted_articles = sorted(
        dated_articles,
        key=lambda a: parse_date(a["published_at"])
    )

    # Add a sequence number to make the spread pattern clear
    timeline = []
    for i, article in enumerate(sorted_articles):
        timeline.append({
            "sequence": i + 1,
            "title": article["title"],
            "source": article["source"],
            "published_at": article["published_at"],
            "url": article["url"],
            "is_likely_origin": i == 0  # first one chronologically
        })

    return timeline


# Quick test with fake sample data
if __name__ == "__main__":
    sample_articles = [
        {"title": "Story B", "source": "Site B", "published_at": "2024-05-03T10:00:00Z", "url": "url-b"},
        {"title": "Story A", "source": "Site A", "published_at": "2024-05-01T08:00:00Z", "url": "url-a"},
        {"title": "Story C", "source": "Site C", "published_at": "2024-05-05T14:00:00Z", "url": "url-c"},
    ]

    timeline = build_timeline(sample_articles)
    for item in timeline:
        marker = "🟢 ORIGIN" if item["is_likely_origin"] else f"#{item['sequence']}"
        print(f"{marker} | {item['published_at']} | {item['source']}: {item['title']}")