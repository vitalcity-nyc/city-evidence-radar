"""
City Evidence Radar - source configuration.

All sources are free, no-key APIs/feeds. Each entry is probed and degrades
gracefully: a dead feed logs a warning and is skipped, never crashes the run.
"""

CONTACT = "josh.greenman@gmail.com"
UA = f"CityEvidenceRadar/1.0 (mailto:{CONTACT})"

# ---------------------------------------------------------------------------
# arXiv: quantitative urban / policy / society categories
# econ.GN = general economics, cs.CY = computers & society, stat.AP = applied stats
# ---------------------------------------------------------------------------
ARXIV_CATEGORIES = ["econ.GN", "cs.CY", "stat.AP"]
ARXIV_MAX = 120  # newest N per run

# ---------------------------------------------------------------------------
# NBER working papers (new releases feed)
# ---------------------------------------------------------------------------
NBER_FEED = "https://back.nber.org/rss/new.xml"

# ---------------------------------------------------------------------------
# Peer-reviewed journals via Crossref (query by ISSN, no key)
# Focus: criminology / public safety + urban economics / policy
# ---------------------------------------------------------------------------
JOURNALS = [
    # --- crime / public safety ---
    ("Journal of Quantitative Criminology", "0748-4518", "public_safety"),
    ("Journal of Experimental Criminology", "1573-3750", "public_safety"),
    ("Criminology", "0011-1384", "public_safety"),
    ("Criminology & Public Policy", "1538-6473", "public_safety"),
    ("Justice Quarterly", "0741-8825", "public_safety"),
    ("Journal of Research in Crime and Delinquency", "0022-4278", "public_safety"),
    # --- urban / policy ---
    ("Journal of Urban Economics", "0094-1190", "urban"),
    ("Urban Affairs Review", "1078-0874", "urban"),
    ("Journal of Policy Analysis and Management", "0276-8739", "urban"),
    ("Regional Science and Urban Economics", "0166-0462", "urban"),
    ("Housing Policy Debate", "1051-1482", "urban"),
    ("Journal of Urban Health", "1099-3460", "urban"),
]
CROSSREF_ROWS = 12  # newest N per journal per run

# ---------------------------------------------------------------------------
# Systematic-review & evaluation feeds (RSS)
# ---------------------------------------------------------------------------
RSS_FEEDS = [
    # Campbell Collaboration systematic reviews (crime/justice, social policy)
    ("Campbell Collaboration", "https://onlinelibrary.wiley.com/feed/18911803/most-recent", "review"),
    # Urban Institute research
    ("Urban Institute", "https://www.urban.org/research/rss.xml", "think_tank"),
    # J-PAL (Abdul Latif Jameel Poverty Action Lab)
    ("J-PAL", "https://www.povertyactionlab.org/rss.xml", "think_tank"),
]

# Sources we attempted but that block automated access (logged for transparency)
KNOWN_GAPS = [
    "SSRN (no open RSS/API; much SSRN crime/econ work surfaces via NBER & Crossref)",
    "Brookings, MDRC, RAND, Vera Institute, Manhattan Institute, Arnold Ventures "
    "(feeds 404 or are bot-blocked as of last probe)",
]

# How many days back to keep an item as "recent" for the digest
RECENT_DAYS = 9
