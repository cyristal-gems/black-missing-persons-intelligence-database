#!/usr/bin/env python3
"""Generate static case routes and deployment metadata from generated case JSON."""

import html
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


PROJECT = Path(__file__).resolve().parents[1]
CASES_PATH = PROJECT / "json" / "cases.json"
CASE_ROUTES = PROJECT / "cases"
SITE_URL = "https://black-missing-person-database.vercel.app"
ASSET_VERSION = "20260805b"

RELATED_CASES = {
    "BM-0003": [("BM-0004", "Diamond Yvette Bradley")],
    "BM-0004": [("BM-0003", "Tionda Z. Bradley")],
    "BM-0023": [("BM-0024", "Dannette Latonia Millbrook")],
    "BM-0024": [("BM-0023", "Jeannette Latrice Millbrook")],
    "BM-0044": [("BM-0048", "Kristian Dejuan Justice")],
    "BM-0048": [("BM-0044", "Kaylah Neveah Hunter")],
}

# Phone counts are explicit for every case with multiple agencies. This prevents
# a rebuild from guessing how semicolon-delimited CSV values should be grouped.
MULTI_AGENCY_PHONE_COUNTS = {
    "BM-0003": [1, 1],
    "BM-0004": [1, 1],
    "BM-0005": [1, 1],
    "BM-0006": [1, 1],
    "BM-0007": [1, 1],
    "BM-0012": [1, 1],
    "BM-0013": [2, 1],
    "BM-0021": [1, 1],
    "BM-0061": [1, 0, 0],
    "BM-0062": [1, 0],
    "BM-0063": [1, 0, 0],
    "BM-0066": [1, 0],
}


def esc(value):
    return html.escape(str(value or ""), quote=True)


def display_date(value):
    parsed = datetime.strptime(value, "%Y-%m-%d")
    return f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"


def group_agency_phones(case_id, agencies, phones):
    if len(agencies) == 1:
        return [phones]
    phone_counts = MULTI_AGENCY_PHONE_COUNTS.get(case_id)
    if phone_counts is None:
        raise ValueError(f"Add an explicit agency/phone grouping for {case_id}")
    if len(phone_counts) != len(agencies) or sum(phone_counts) != len(phones):
        raise ValueError(f"Agency/phone grouping no longer matches source data for {case_id}")
    grouped = []
    phone_index = 0
    for phone_count in phone_counts:
        grouped.append(phones[phone_index:phone_index + phone_count])
        phone_index += phone_count
    return grouped


def source_name(url):
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    names = {
        "charleyproject.org": "The Charley Project",
        "missingkids.org": "National Center for Missing & Exploited Children",
        "fbi.gov": "Federal Bureau of Investigation",
        "namus.nij.ojp.gov": "National Missing and Unidentified Persons System",
        "blackandmissinginc.com": "Black and Missing Foundation",
        "doenetwork.org": "The Doe Network",
    }
    return names.get(domain, domain or "Case source")


def header():
    return '''<a class="skip-link" href="#main-content">Skip to content</a>
<header class="site-header"><div class="shell nav-wrap">
  <a class="brand" href="/"><span class="brand-title">Black Missing Persons Intelligence Database</span></a>
  <nav class="primary-nav" aria-label="Primary navigation"><a href="/">Dashboard</a><a href="/methodology/">Methodology</a><a href="/reference/">Reference</a></nav>
  <a class="button button-small" href="/cases/">Browse cases</a>
</div></header>'''


def footer():
    return '''<footer class="site-footer case-page-footer"><div class="shell footer-grid">
  <div><a class="brand footer-brand" href="/"><span class="brand-title">Black Missing Persons Intelligence Database</span></a><p>Mapping the Missing. Preserving Every Story.</p></div>
  <div><h2>Explore</h2><a href="/">Dashboard</a><a href="/cases/">Case directory</a><a href="/about/">About</a><a href="/methodology/">Methodology</a></div>
</div><div class="shell footer-bottom"><p>Submit tips directly to the investigating agency.</p><p>© 2026 Black Missing Persons Intelligence Database</p></div></footer>'''


def render_case(case):
    case_id = case["case_id"]
    full_name = case["full_name"]
    location = ", ".join(filter(None, [case["last_seen"]["city"], case["last_seen"]["state"], case["last_seen"]["country"]]))
    image_name = Path(urlparse(case["image_url"]).path).name
    status_class = " presumed" if case["case_status"] == "Presumed Deceased" else ""
    agencies = case["investigation"]["agencies"]
    phones = case["investigation"]["phones"]
    timeline = "".join(
        f'<li><strong>{esc(event["label"])}</strong><span>{esc(event["description"])}</span></li>'
        for event in case["timeline"]
    )
    source_items = "".join(
        f'<li><a href="{esc(source["url"])}" rel="noopener noreferrer">{esc(source_name(source["url"]))} <span aria-hidden="true">↗</span></a></li>'
        for source in case["sources"]
    )
    agency_contacts = group_agency_phones(case_id, agencies, phones)
    contact_items = "".join(
        '<li><strong>{agency}</strong>{phones}</li>'.format(
            agency=esc(agency),
            phones="".join(
                f'<a href="tel:{re.sub(r"[^0-9+]", "", phone)}">{esc(phone)}</a>'
                for phone in agency_contacts[index]
            ) or '<span>Phone number not listed</span>',
        )
        for index, agency in enumerate(agencies)
    )
    related = ""
    if case_id in RELATED_CASES:
        items = "".join(f'<li><a href="/cases/{esc(related_id)}/">{esc(related_id)} — {esc(name)}</a></li>' for related_id, name in RELATED_CASES[case_id])
        related = f'<section><h2>Related Cases</h2><ul class="related-list">{items}</ul></section>'
    description = esc(case["case_summary_short"][:155])
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{description}"><meta name="theme-color" content="#111018">
  <meta property="og:title" content="{esc(full_name)} | Black Missing Persons Intelligence Database"><meta property="og:description" content="{description}"><meta property="og:type" content="article"><meta property="og:image" content="{SITE_URL}/images/{esc(image_name)}">
  <title>{esc(full_name)} | Black Missing Persons Intelligence Database</title>
  <link rel="canonical" href="{SITE_URL}/cases/{esc(case_id)}/"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/styles.css?v={ASSET_VERSION}"><script src="/assets/site.js?v={ASSET_VERSION}" defer></script>
</head>
<body data-page="case-detail">{header()}
<main id="main-content">
  <section class="case-detail-hero"><div class="shell"><a class="back-link" href="/cases/">← Back to case directory</a><div class="case-detail-grid">
    <div class="case-portrait"><img src="/images/{esc(image_name)}" alt="{esc(full_name)}" width="600" height="750"></div>
    <div class="case-detail-copy"><div class="case-detail-meta"><span class="case-id">{esc(case_id)}</span><span class="status-pill{status_class}">{esc(case["case_status"])}</span><span class="status-pill">{esc(case["classification"])}</span></div><h1>{esc(full_name)}</h1><p>{esc(case["overview"])}</p></div>
  </div></div></section>
  <section class="case-content"><div class="shell case-content-grid"><article class="case-story">
    <section><h2>Circumstances</h2><p>{esc(case["circumstances"])}</p></section>
    <section><h2>Investigation</h2><p>{esc(case["investigation_summary"])}</p></section>
    <section><h2>Timeline</h2><ol class="timeline">{timeline}</ol></section>
    <section><h2>Physical Description</h2><p>At the time of the disappearance, {esc(full_name)} was {esc(case["age_at_missing"])} years old. The record is categorized as {esc(case["classification"])}. Additional physical identifiers should be confirmed through the active source profiles.</p></section>
    <section><h2>Notes</h2><p>{esc(case["notes"])}</p></section>{related}
  </article><aside class="case-sidebar">
    <section class="facts-card"><h2>Quick Facts</h2><dl class="facts-list"><div><dt>Case ID</dt><dd>{esc(case_id)}</dd></div><div><dt>Missing date</dt><dd>{esc(display_date(case["missing_date"]))}</dd></div><div><dt>Age at missing</dt><dd>{esc(case["age_at_missing"])}</dd></div><div><dt>Last seen</dt><dd>{esc(location)}</dd></div><div><dt>Classification</dt><dd>{esc(case["case_classification"])}</dd></div><div><dt>Investigation</dt><dd>{esc(case["investigation"]["status"])}</dd></div></dl></section>
    <section class="tip-card"><h2>Have information?</h2><p>Contact the listed investigating agency directly. Do not submit tips to this website.</p><ul class="agency-contact-list">{contact_items}</ul></section>
    <section class="sources-card"><h2>Sources</h2><ul class="source-list">{source_items}</ul><p class="verified-date">Record last verified {esc(display_date(case["last_verified_date"]))}</p></section>
  </aside></div></section>
</main>{footer()}</body></html>'''


def write_sitemap(cases):
    routes = ["/", "/cases/", "/about/", "/methodology/", "/reference/"]
    routes.extend(f'/cases/{case["case_id"]}/' for case in cases)
    urls = "\n".join(f"  <url><loc>{SITE_URL}{route}</loc></url>" for route in routes)
    (PROJECT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n',
        encoding="utf-8",
    )


def main():
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases = payload["cases"]
    expected_ids = {case["case_id"] for case in cases}
    for path in CASE_ROUTES.iterdir():
        if path.is_dir() and re.fullmatch(r"BM-\d{4}", path.name) and path.name not in expected_ids:
            shutil.rmtree(path)
    for case in cases:
        route = CASE_ROUTES / case["case_id"]
        route.mkdir(parents=True, exist_ok=True)
        (route / "index.html").write_text(render_case(case), encoding="utf-8")
    write_sitemap(cases)
    print(json.dumps({"site_case_pages": len(cases), "site_url": SITE_URL}, indent=2))


if __name__ == "__main__":
    main()
