

https://github.com/rahmanshanq/tmol

# The Meaning of Life Across Scholarly Disciplines

An interactive dashboard mapping 129,672 scholarly works about living a meaningful life across 16 intellectual traditions and 170+ countries.

Built with Dash and Plotly. Data from OpenAlex.

**Rahman Alshanqeeti**  
DIGS 30004 Data Visualization for the Humanities · Instructor: Brooke Luetgert · Spring 2026

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:8050

## Repository Structure

```
├── app.py                          # Main Dash application
├── requirements.txt                # Python dependencies
├── project_writeup.pdf             # Project narrative (2 pages)
├── collaboration_statement.pdf     # AI usage and self-assessment
├── data/
│   ├── dataset_merged.csv          # 129,672 works with custom classification
│   ├── dataset_term_map.csv        # Which search terms found which works
│   ├── classifier_config_final.json # 16-category classifier configuration
│   └── master_terms_final.json     # 245 search terms
├── pages/
│   ├── data.py                     # Pre-computed data (loads once at startup)
│   ├── overview.py                 # Treemap, bridges, insularity
│   ├── network.py                  # Constellation graph, heatmap, paper links
│   ├── timeline.py                 # Streamgraph, bar chart race, share chart
│   ├── geography.py                # Choropleths, time slider
│   ├── live.py                     # Real-time feed from OpenAlex API
│   └── explore.py                  # Sunburst, filtered search, paper links
└── assets/
    ├── style.css                   # Dark scholarly theme
    └── favicon.svg                 # Constellation favicon
```

## Dashboard Pages

**Overview** — Treemap of tradition sizes. Top cross-tradition bridges. Insularity scores.

**Network** — Force-directed constellation graph. Click nodes to see connections. Click edges or connection bars to see bridging papers with links to OpenAlex.

**Timeline** — Streamgraph with annotated events. Animated bar chart race (1960–2025, year by year). Share-of-conversation stacked area.

**Geography** — Research volume choropleth. Dominant tradition by country. Yearly time slider showing how the map changes from 1960 to 2025.

**Live Feed** — Pulls recent papers from OpenAlex in real time. Samples 30 of 245 search terms per refresh. Clickable paper links. Keyword and field breakdowns.

**Explore** — Filter by tradition or search term. Concept sunburst. Top journals and countries. Clickable paper list.

## Methodology

245 search terms across 16 traditions, curated through manual brainstorming and two rounds of vector-space discovery (sentence-transformers, all-MiniLM-L6-v2). Data from OpenAlex API, 500 works per term, 129,672 unique after deduplication. Custom embedding-based classifier replaced OpenAlex's field labels, which misclassified non-Western traditions. Content weighted 70%, journal name 30%, with fallback to content-only when journal metadata is unreliable.
