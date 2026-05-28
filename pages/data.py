"""Pre-computed data. Loads once at import time."""
import pandas as pd
import numpy as np
import networkx as nx
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
print("⏳ Loading data...")

_works = pd.read_csv(os.path.join(DATA_DIR, "dataset_merged.csv.gz"), dtype=str).fillna("")
_works["year"] = pd.to_numeric(_works["year"], errors="coerce")
_term_map = pd.read_csv(os.path.join(DATA_DIR, "dataset_term_map.csv"), dtype=str).fillna("")

# Unified timeline: 1960-2025
START_YEAR = 1960
END_YEAR = 2025
ALL_YEARS = list(range(START_YEAR, END_YEAR + 1))

TOTAL_WORKS = len(_works)
CATEGORIES = _works["primary_category"].value_counts().index.tolist()
NUM_CATEGORIES = len(CATEGORIES)

COLORS = {
    "Psychology": "#60a5fa", "Western Philosophy": "#a78bfa",
    "Existentialism & Phenomenology": "#c084fc", "Islamic Thought": "#34d399",
    "Buddhist Thought": "#fbbf24", "Hindu Thought": "#fb923c",
    "Confucian & Chinese Thought": "#f87171", "Christian Theology": "#818cf8",
    "Jewish Thought": "#38bdf8", "African Philosophy": "#e89b6a",
    "Indigenous & Latin American Thought": "#4ade80",
    "Japanese & East Asian Cultural Concepts": "#f472b6",
    "Anthropology": "#d4a574", "Sociology & Political Economy": "#94a3b8",
    "Health & Medical Sciences": "#22d3ee", "Neuroscience & Cognitive Science": "#a5b4fc",
}

DARK_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="'IBM Plex Sans', sans-serif", color="#cbd5e1", size=12),
    margin=dict(l=50, r=30, t=40, b=40), hovermode="closest",
)
DARK_AXIS = dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.06)")

# Yearly
_ydf = _works[_works["year"].between(START_YEAR, END_YEAR)].copy()
_ydf["year"] = _ydf["year"].astype(int)
YEARLY_COUNTS = _ydf.groupby(["year", "primary_category"]).size().reset_index(name="count")

YEARLY_TRACES = {}
for cat in CATEGORIES:
    cd = YEARLY_COUNTS[YEARLY_COUNTS["primary_category"] == cat].set_index("year")["count"]
    vals = pd.Series([cd.get(y, 0) for y in ALL_YEARS]).rolling(3, center=True, min_periods=1).mean().tolist()
    YEARLY_TRACES[cat] = vals

# Countries
import pycountry
ISO2_TO_ISO3 = {c.alpha_2: c.alpha_3 for c in pycountry.countries}
ISO3_TO_NAME = {c.alpha_3: c.name for c in pycountry.countries}

_cr = []
for _, row in _works.iterrows():
    c = row.get("countries", "")
    if c:
        for code in c.split("|"):
            code = code.strip()
            if code: _cr.append({"iso2": code, "cat": row["primary_category"], "year": row["year"]})
COUNTRY_DF = pd.DataFrame(_cr)
COUNTRY_DF["iso3"] = COUNTRY_DF["iso2"].map(ISO2_TO_ISO3)
COUNTRY_DF = COUNTRY_DF.dropna(subset=["iso3"])
COUNTRY_DF["name"] = COUNTRY_DF["iso3"].map(ISO3_TO_NAME)
NUM_COUNTRIES = COUNTRY_DF["iso3"].nunique()
COUNTRY_COUNTS = COUNTRY_DF["iso3"].value_counts().reset_index()
COUNTRY_COUNTS.columns = ["iso3", "count"]
COUNTRY_COUNTS["name"] = COUNTRY_COUNTS["iso3"].map(ISO3_TO_NAME)

# Network
print("⏳ Computing network...")
EDGE_COUNTS = {}
multi = _works[_works["secondary_category"].str.len() > 0]
for _, row in multi.iterrows():
    a, b = row["primary_category"], row["secondary_category"]
    if a and b and a != b:
        k = tuple(sorted([a, b]))
        EDGE_COUNTS[k] = EDGE_COUNTS.get(k, 0) + 1
classified = _works[["work_id", "primary_category"]]
merged = _term_map.merge(classified, on="work_id", how="inner")
for cats in merged.groupby("work_id")["primary_category"].apply(set):
    cats = list(cats)
    for i in range(len(cats)):
        for j in range(i + 1, len(cats)):
            k = tuple(sorted([cats[i], cats[j]]))
            EDGE_COUNTS[k] = EDGE_COUNTS.get(k, 0) + 1

GRAPH = nx.Graph()
CAT_SIZES = _works["primary_category"].value_counts().to_dict()
for cat, sz in CAT_SIZES.items(): GRAPH.add_node(cat, size=sz)
for (a, b), w in EDGE_COUNTS.items():
    if w >= 10: GRAPH.add_edge(a, b, weight=w)
GRAPH_POS = nx.spring_layout(GRAPH, k=2.5, iterations=100, seed=42, weight="weight")

INSULARITY = _works.groupby("primary_category").apply(
    lambda g: (g["secondary_category"].str.len() == 0).mean()).sort_values(ascending=False)
MULTI_LABEL_RATE = (_works["secondary_category"].str.len() > 0).mean()

# Top bridge papers: papers that appear under multiple traditions
_bridge_papers = _works[_works["secondary_category"].str.len() > 0][
    ["work_id", "title", "primary_category", "secondary_category", "journal", "year"]
].copy()
_bridge_papers["year"] = _bridge_papers["year"].astype(int, errors="ignore")

def get_bridge_papers(cat1, cat2, n=8):
    """Get papers bridging two traditions."""
    mask = (
        ((_bridge_papers["primary_category"] == cat1) & (_bridge_papers["secondary_category"] == cat2)) |
        ((_bridge_papers["primary_category"] == cat2) & (_bridge_papers["secondary_category"] == cat1))
    )
    return _bridge_papers[mask].head(n).to_dict("records")

def get_tradition_papers(cat, n=10):
    """Get top papers for a tradition."""
    return _works[_works["primary_category"] == cat][
        ["work_id", "title", "journal", "year"]
    ].head(n).to_dict("records")

TERM_WITH_CAT = _term_map.merge(_works[["work_id", "primary_category"]], on="work_id", how="inner")
WORKS = _works
TERM_MAP = _term_map

# Load full term list for live feed
import json
_terms_path = os.path.join(DATA_DIR, "master_terms_final.json")
if os.path.exists(_terms_path):
    with open(_terms_path) as f:
        ALL_TERMS = [t["search_query"] for t in json.load(f)]
else:
    ALL_TERMS = ["meaning in life", "eudaimonia", "flourishing", "well-being", "ikigai"]

print(f"✓ Ready. {TOTAL_WORKS:,} works, {NUM_CATEGORIES} traditions, {NUM_COUNTRIES} countries.")
