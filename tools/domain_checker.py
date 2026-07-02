# tools/domain_checker.py
# Checks the reputation of a domain/source using a known reference list
# and basic heuristics (no paid API needed)

from urllib.parse import urlparse

# A small curated list — you can expand this over time
HIGH_CREDIBILITY_DOMAINS = [
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "npr.org",
    "nature.com", "science.org", "who.int", "cdc.gov", "nih.gov",
    "nytimes.com", "washingtonpost.com", "theguardian.com",
    "wsj.com", "economist.com", "ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov",
    "mayoclinic.org", "clevelandclinic.org", "hopkinsmedicine.org",
    "factcheck.org", "snopes.com", "politifact.com", "fda.gov"
]

LOW_CREDIBILITY_SIGNALS = [
    "blogspot.com", "wordpress.com", "wixsite.com",
    "infowars.com", "naturalnews.com", "beforeitsnews.com"
]


def get_domain(url: str) -> str:
    """Extracts the clean domain from a URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    return domain


def check_domain_reputation(url: str) -> dict:
    """
    Checks a URL's domain against known credibility lists.
    Returns a reputation score and reasoning.
    """

    domain = get_domain(url)

    if any(trusted in domain for trusted in HIGH_CREDIBILITY_DOMAINS):
        return {
            "domain": domain,
            "reputation": "high",
            "score": 9,
            "reason": "Recognized as an established, fact-checked news or research source."
        }

    if any(flagged in domain for flagged in LOW_CREDIBILITY_SIGNALS):
        return {
            "domain": domain,
            "reputation": "low",
            "score": 2,
            "reason": "Domain matches known low-credibility or unmoderated publishing platform."
        }

    # Unknown domain — default to medium, let Gemini investigate further
    return {
        "domain": domain,
        "reputation": "unknown",
        "score": 5,
        "reason": "Domain not in known reference lists — requires further AI analysis."
    }


# Quick test
if __name__ == "__main__":
    test_urls = [
        "https://www.bbc.com/news/some-article",
        "https://randomblog.blogspot.com/2024/fake-news",
        "https://somenewsite.com/article123"
    ]

    for url in test_urls:
        result = check_domain_reputation(url)
        print(f"\nURL: {url}")
        print(f"Domain: {result['domain']}")
        print(f"Reputation: {result['reputation']} (score: {result['score']})")
        print(f"Reason: {result['reason']}")