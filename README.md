# Black Missing Persons Intelligence Database

## Summary

The Black Missing Persons Intelligence Database brings source-backed information about missing Black people together in one public, searchable collection. Its main CSV file is used to generate case profiles, maps, statistics, and JSON files for research, public awareness, and future integrations.

## Key Features

- A canonical `data/cases.csv` dataset that serves as the single source of truth.
- Individual Markdown and website profiles with consistent overviews, facts, circumstances, investigations, timelines, descriptions, notes, and active sources.
- Short narrative summaries designed for dashboards, cards, maps, and other compact interfaces.
- Structured JSON records for websites, APIs, applications, and future integrations.
- GeoJSON point features for mapping each case by last-seen coordinates.
- Automatically calculated statistics covering case status, classification, state, media prominence, and missing-person decade.
- State-level aggregates containing case totals, classifications, statuses, geographic centers, and case IDs.
- A reusable dashboard configuration with filters, search fields, sorting options, map settings, and accessibility preferences.
- A repeatable generator that rebuilds all derived files from the canonical CSV.
- Splunk-ready data for search, monitoring, visualization, and investigative analysis.
- A responsive static website with an interactive map, charts, search, filters, and 75 permanent case routes.
- GitHub and Vercel configuration for automatic production deployments.
- A complete local rebuild using `python3 scripts/generate_assets.py` and local preview using `python3 -m http.server 8000`.

## Tech Stack

- **CSV:** Stores the canonical case dataset that powers every generated document and integration file.
- **Python 3:** Validates the source data and automatically generates the Markdown documentation and JSON datasets.
- **Markdown:** Provides readable, version-controlled case profiles that render directly on GitHub.
- **JSON:** Supplies structured case, statistics, state, and dashboard configuration data for web applications and APIs.
- **GeoJSON:** Represents last-seen locations as map-ready geographic features with linked case metadata.
- **Splunk:** Ingests the canonical CSV for searching, filtering, dashboards, monitoring, and investigative analysis.
- **HTML5:** Provides semantic, accessible structure for the public dashboard, directory, case profiles, and reference pages.
- **CSS3:** Creates the responsive dark interface, charts, map presentation, and mobile layouts without a frontend dependency.
- **JavaScript:** Loads generated JSON, renders the interactive dashboard, and powers case search, filtering, sorting, maps, and charts.
- **GitHub:** Stores the version-controlled canonical data, generated assets, website source, and project history.
- **Vercel:** Hosts the static production website and automatically redeploys changes pushed to the connected GitHub repository.

## View Database Here

[https://black-missing-person-database.vercel.app](https://black-missing-person-database.vercel.app)

## Connect With Me

- **LinkedIn:** [linkedin.com/in/cyristalj](https://www.linkedin.com/in/cyristalj)
- **GitHub:** [github.com/cyristal-gems](https://github.com/cyristal-gems)
- **Email:** [cyrisjoseph@outlook.com](mailto:cyrisjoseph@outlook.com)
