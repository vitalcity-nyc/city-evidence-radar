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
    ("Criminal Justice and Behavior", "0093-8548", "public_safety"),
    ("Police Quarterly", "1098-6111", "public_safety"),
    ("Journal of Criminal Justice", "0047-2352", "public_safety"),
    ("Injury Prevention", "1353-8047", "public_safety"),
    # --- urban / policy / economics ---
    ("Journal of Urban Economics", "0094-1190", "urban"),
    ("Urban Affairs Review", "1078-0874", "urban"),
    ("Journal of Urban Affairs", "0735-2166", "urban"),
    ("Journal of Policy Analysis and Management", "0276-8739", "urban"),
    ("Regional Science and Urban Economics", "0166-0462", "urban"),
    ("Journal of Public Economics", "0047-2727", "urban"),
    ("American Economic Journal: Applied Economics", "1945-7782", "urban"),
    ("American Economic Journal: Economic Policy", "1945-7731", "urban"),
    ("Journal of Human Resources", "0022-166X", "urban"),
    # --- housing / transit ---
    ("Housing Policy Debate", "1051-1482", "urban"),
    ("Housing Studies", "0267-3037", "urban"),
    ("Transportation Research Part A", "0965-8564", "urban"),
    # --- health ---
    ("Journal of Urban Health", "1099-3460", "health"),
    ("American Journal of Public Health", "0090-0036", "health"),
    ("American Journal of Preventive Medicine", "0749-3797", "health"),
    ("Prevention Science", "1389-4986", "health"),
    ("Health Affairs", "0278-2715", "health"),
    # --- education ---
    ("Educational Evaluation and Policy Analysis", "0162-3737", "education"),
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

# ---------------------------------------------------------------------------
# World Bank Policy Research Working Papers (Documents & Reports API, no key)
# ---------------------------------------------------------------------------
WORLDBANK_API = ("https://search.worldbank.org/api/v3/wds?format=json&rows=60"
                 "&srt=docdt&order=desc&fl=display_title,docdt,url,abstracts,authr"
                 "&docty=Policy Research Working Paper")

# ---------------------------------------------------------------------------
# OSF preprints — SocArXiv (open social-science working papers, no key)
# ---------------------------------------------------------------------------
OSF_API = ("https://api.osf.io/v2/preprints/?filter[provider]=socarxiv"
           "&page[size]=50&sort=-date_published")

# Sources we attempted but that block automated access (logged for transparency)
KNOWN_GAPS = [
    "SSRN (no open RSS/API; much SSRN crime/econ work surfaces via NBER, Crossref and SocArXiv)",
    "IZA discussion papers and the Cochrane Library (feeds returned nothing on last probe)",
    "Brookings, MDRC, RAND, Vera Institute, Manhattan Institute and Arnold Ventures "
    "(feeds 404 or are bot-blocked as of last probe)",
]

# Human-readable source summary shown in the app footer
SOURCE_SUMMARY = ("NBER, arXiv, 28 peer-reviewed journals (criminology, urban economics, "
                  "policy, housing, transit, health and education), Campbell Collaboration "
                  "systematic reviews, World Bank policy research working papers, SocArXiv "
                  "preprints, the Urban Institute and J-PAL")

# How many days back to keep an item as "recent" for the digest
RECENT_DAYS = 9

# ---------------------------------------------------------------------------
# Editorial themes (narrative bundles). The model assigns each idea its single
# best-fit theme key; the label + blurb drive the "group by theme" view.
# Seed list (Josh's bundles) plus emergent public-safety / urban themes.
# ---------------------------------------------------------------------------
THEMES = [
    ("alcohol-addiction", "Alcohol and addiction",
     "Cutting the harm that flows from alcohol and drugs, from outlet density and pricing to medication for opioid use disorder."),
    ("reentry-employment", "Reentry and reemployment",
     "Smoothing the path home from jail and prison, including health coverage, benefits and a real shot at a job."),
    ("lead-environment", "Lead and environmental exposure",
     "Removing the environmental insults, lead chief among them, that quietly shape violence, health and learning."),
    ("domestic-violence", "Domestic and intimate-partner violence",
     "Better ways to interrupt and respond to a category of harm that has stayed stubbornly sticky in New York City."),
    ("schools-pipeline", "Schools and the school-to-prison pipeline",
     "Keeping young people in class and out of the justice system by rethinking discipline, attendance and support."),
    ("gun-violence", "Gun and community violence intervention",
     "Concentrating help and deterrence on the small networks of people and places that drive most shootings."),
    ("behavioral", "Behavioral and cognitive programs",
     "Low-cost programs, from cognitive behavioral therapy to summer jobs and mentoring, that shift behavior at the margin."),
    ("place-environment", "Place and the built environment",
     "Treating physical space, lighting, vacant lots, greening and design, as a lever on safety."),
    ("policing-courts", "Policing, courts and enforcement",
     "How police, prosecutors and courts deploy their tools, from diversion and sentencing to body cameras."),
    ("housing-homelessness", "Housing and homelessness",
     "Stable housing and homelessness response as upstream public-safety and public-health infrastructure."),
    ("health-overdose", "Health and overdose response",
     "Public-health responses, including naloxone, treatment and crisis care, that save lives and reduce harm."),
    ("youth-family", "Youth and family supports",
     "Early and family-centered investments that pay off in safety and mobility years later."),
    ("economic-security", "Jobs and economic security",
     "Income, work and economic stability as foundations for safer, healthier neighborhoods."),
    ("other", "Other ideas",
     "Promising ideas that do not yet fit one of the bundles above."),
]
THEME_KEYS = [k for k, _, _ in THEMES]
