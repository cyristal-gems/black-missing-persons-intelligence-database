import csv
import io
import json
import os
import re
import runpy
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse


PROJECT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT / "data" / "cases.csv"
DOCS_DIR = PROJECT / "docs"
JSON_DIR = PROJECT / "json"
GENERATED_ON = date.today().isoformat()

RELATED_CASES = {
    "BM-0003": [("BM-0004", "Diamond Yvette Bradley")],
    "BM-0004": [("BM-0003", "Tionda Z. Bradley")],
    "BM-0023": [("BM-0024", "Dannette Latonia Millbrook")],
    "BM-0024": [("BM-0023", "Jeannette Latrice Millbrook")],
    "BM-0044": [("BM-0048", "Kristian Dejuan Justice")],
    "BM-0048": [("BM-0044", "Kaylah Neveah Hunter")],
}

AGENCY_COLUMNS = ("primary_agency", "secondary_agency", "tertiary_agency")
PHONE_COLUMNS = (
    "primary_agency_phone",
    "primary_agency_alternate_phone",
    "secondary_agency_phone",
    "tertiary_agency_phone",
)


def clean(value):
    return (value or "").strip()


def iso_missing_date(value):
    raw = clean(value)
    for pattern in ("%m/%d/%y", "%m/%d/%Y"):
        try:
            parsed = datetime.strptime(raw, pattern)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw or None


def split_values(value):
    return [item.strip() for item in clean(value).split(";") if item.strip()]


def split_keywords(value):
    return [item.strip() for item in clean(value).split("|") if item.strip()]


def number_or_none(value, integer=False):
    raw = clean(value)
    if not raw:
        return None
    try:
        return int(raw) if integer else float(raw)
    except ValueError:
        return None


def image_relative_path(row):
    filename = Path(clean(row["image_url"])).name
    return f"../images/{filename}" if filename else None


def source_entries(row):
    entries = []
    if clean(row["primary_source_url"]):
        entries.append({"role": "primary", "url": clean(row["primary_source_url"])})
    if clean(row["secondary_source_url"]):
        entries.append({"role": "secondary", "url": clean(row["secondary_source_url"])})
    return entries


def public_investigation_summary(row):
    detailed_summary = clean(row.get("investigation_summary"))
    if detailed_summary:
        return detailed_summary
    status = clean(row["investigative_status"])
    classification = clean(row["case_classification"])
    return f"The case is currently recorded as {status} and is classified as {classification}."


def normalized_case(row):
    agencies = [clean(row[column]) for column in AGENCY_COLUMNS if clean(row[column])]
    phones = [clean(row[column]) for column in PHONE_COLUMNS if clean(row[column])]
    timeline = json.loads(clean(row["timeline"]))
    if not isinstance(timeline, list) or not timeline:
        raise RuntimeError(f"{clean(row['case_id'])}: timeline must contain at least one event")
    excluded_timeline_labels = {"Case Remains Open", "Last Known Sighting", "Present", "Subsequent development"}
    for event in timeline:
        if not isinstance(event, dict) or set(event) != {"label", "description"}:
            raise RuntimeError(
                f"{clean(row['case_id'])}: every timeline event must contain exactly label and description"
            )
        if not clean(event["label"]) or not clean(event["description"]):
            raise RuntimeError(f"{clean(row['case_id'])}: timeline labels and descriptions cannot be empty")
        if clean(event["label"]) in excluded_timeline_labels:
            raise RuntimeError(f"{clean(row['case_id'])}: timeline uses a generic or routine-status label")

    return {
        "case_id": clean(row["case_id"]),
        "full_name": clean(row["full_name"]),
        "case_status": clean(row["case_status"]),
        "classification": clean(row["classification"]),
        "age_at_missing": number_or_none(row["age_at_missing"], integer=True),
        "missing_date": iso_missing_date(row["missing_date"]),
        "case_classification": clean(row["case_classification"]),
        "last_seen": {
            "city": clean(row["last_seen_city"]),
            "state": clean(row["last_seen_state"]),
            "country": clean(row["last_seen_country"]),
            "latitude": number_or_none(row["latitude"]),
            "longitude": number_or_none(row["longitude"]),
        },
        "case_summary": clean(row["case_summary"]),
        "case_summary_short": clean(row["case_summary_short"]),
        "investigation_summary": public_investigation_summary(row),
        "timeline": [
            {"label": clean(event["label"]), "description": clean(event["description"])}
            for event in timeline
        ],
        "notes": clean(row["notes"]),
        "investigation": {
            "status": clean(row["investigative_status"]),
            "agencies": agencies,
            "phones": phones,
        },
        "sources": source_entries(row),
        "primary_source_type": clean(row["primary_source_type"]),
        "media_prominence": clean(row["media_prominence"]),
        "keywords": split_keywords(row["keywords"]),
        "image_url": clean(row["image_url"]),
        "image_path": image_relative_path(row),
        "document_path": f"/docs/{clean(row['case_id'])}.md",
        "last_verified_date": clean(row["last_verified_date"]) or None,
    }


def markdown_link(label, url):
    return f"[{label}]({url})"


def long_date(value):
    parsed = datetime.strptime(value, "%Y-%m-%d")
    return f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"


def source_name(url):
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    known = {
        "charleyproject.org": "The Charley Project",
        "missingkids.org": "National Center for Missing & Exploited Children",
        "fbi.gov": "Federal Bureau of Investigation",
        "namus.nij.ojp.gov": "National Missing and Unidentified Persons System",
        "blackandmissinginc.com": "Black and Missing Foundation",
        "doenetwork.org": "The Doe Network",
        "dps.texas.gov": "Texas Department of Public Safety",
        "police.fortworthtexas.gov": "Fort Worth Police Department",
    }
    if domain in known:
        return known[domain]
    name = domain.split(".")[0].replace("-", " ").replace("_", " ")
    return name.title()


def split_sentences(text):
    protected = text
    abbreviations = {
        "D.C.": "D§C§",
        "a.m.": "a§m§",
        "p.m.": "p§m§",
        "Jr.": "Jr§",
        "St.": "St§",
        "U.S.": "U§S§",
    }
    for original, token in abbreviations.items():
        protected = protected.replace(original, token)
    protected = re.sub(r"\b([A-Z])\.(?=\s+[A-Z][A-Za-z'’()-]+)", r"\1¤", protected)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", protected)
    restored = []
    for part in parts:
        for original, token in abbreviations.items():
            part = part.replace(token, original)
        part = part.replace("¤", ".")
        if part.strip():
            restored.append(part.strip())
    return restored


def join_words(items):
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def render_case_markdown(row, case):
    location = ", ".join(filter(None, [
        case["last_seen"]["city"],
        case["last_seen"]["state"],
        case["last_seen"]["country"],
    ]))
    missing_date_display = long_date(case["missing_date"])
    last_updated_display = long_date(GENERATED_ON)
    case_summary = case["case_summary"]
    agencies = join_words(case["investigation"]["agencies"])
    investigation = case["investigation_summary"]
    timeline_lines = [
        f"- **{event['label']}** — {event['description']}"
        for event in case["timeline"]
    ]

    primary_sources = [source for source in case["sources"] if source["role"] == "primary"]
    secondary_sources = [source for source in case["sources"] if source["role"] == "secondary"]
    primary_lines = [
        f"- {markdown_link(source_name(source['url']), source['url'])}"
        for source in primary_sources
    ]
    secondary_lines = [
        f"- {markdown_link(source_name(source['url']), source['url'])}"
        for source in secondary_sources
    ]

    related_block = ""
    if case["case_id"] in RELATED_CASES:
        related_lines = [
            f"- [{related_id}]({related_id}.md) — {related_name}"
            for related_id, related_name in RELATED_CASES[case["case_id"]]
        ]
        related_block = f'''\n---

## Related Cases

{chr(10).join(related_lines)}
'''

    image_filename = Path(case["image_path"]).name
    site_image_path = f"/images/{image_filename}"
    physical_description = (
        f"At the time of the disappearance, {case['full_name']} was {case['age_at_missing']} years old. "
        f"This database lists the case in the {case['classification']} category. The image shown above is the one "
        f"used for this record. For height, weight, hair, eyes, clothing, and other identifying details, see the "
        f"linked source profiles below."
    )

    return f'''---
case_id: {json.dumps(case["case_id"])}
title: {json.dumps(case["full_name"])}
classification: {json.dumps(case["classification"])}
case_status: {json.dumps(case["case_status"])}
case_classification: {json.dumps(case["case_classification"])}
missing_date: {json.dumps(case["missing_date"])}
last_seen_city: {json.dumps(case["last_seen"]["city"])}
last_seen_state: {json.dumps(case["last_seen"]["state"])}
image: {json.dumps(site_image_path)}
---

![{case["full_name"]}]({case["image_path"]})

# {case["full_name"]}

**Case ID:** {case["case_id"]}

## Case Summary

{case_summary}

---

## Quick Facts

| Field | Value |
|-------|-------|
| Classification | {case["classification"]} |
| Case Status | {case["case_status"]} |
| Case Classification | {case["case_classification"]} |
| Missing Date | {missing_date_display} |
| Age at Missing | {case["age_at_missing"]} |
| Last Seen | {location} |
| Investigative Status | {case["investigation"]["status"]} |
| Lead Agencies | {agencies} |

---

## Investigation

{investigation}

---

## Timeline

{chr(10).join(timeline_lines)}

---

## Physical Description

{physical_description}
{related_block}

---

## Notes

{case["notes"]}

---

## Sources

### Primary Source

{chr(10).join(primary_lines)}

### Secondary Sources

{chr(10).join(secondary_lines)}

---

## Last Updated

{last_updated_display}
'''


def ordered_counts(values):
    return dict(sorted(Counter(values).items(), key=lambda item: (-item[1], item[0])))


raw_csv = CSV_PATH.read_bytes()
try:
    csv_text = raw_csv.decode("utf-8-sig")
    source_encoding = "utf-8"
except UnicodeDecodeError:
    csv_text = raw_csv.decode("mac_roman")
    source_encoding = "mac_roman"
rows = list(csv.DictReader(io.StringIO(csv_text, newline="")))

required_columns = {
    "case_id", "full_name", "case_status", "classification", "missing_date",
    "age_at_missing", "case_classification", "last_seen_city", "last_seen_state",
    "last_seen_country", "case_summary", "case_summary_short",
    "investigation_summary", "timeline", "notes",
    "primary_source_url", "secondary_source_url",
    "primary_source_type", "media_prominence", "keywords", "investigative_status",
    "image_url", "latitude", "longitude", "last_verified_date",
}
required_columns.update(AGENCY_COLUMNS)
required_columns.update(PHONE_COLUMNS)
optional_fields = {
    "secondary_agency", "tertiary_agency",
    "primary_agency_alternate_phone", "secondary_agency_phone", "tertiary_agency_phone",
}
required_values = required_columns.difference(optional_fields)
missing_columns = required_columns.difference(rows[0].keys() if rows else set())
if missing_columns:
    raise RuntimeError(f"Missing required CSV columns: {sorted(missing_columns)}")

case_ids = [clean(row["case_id"]) for row in rows]
if len(case_ids) != len(set(case_ids)):
    raise RuntimeError("Duplicate case_id values were found")
if any(not re.fullmatch(r"BM-\d{4}", case_id) for case_id in case_ids):
    raise RuntimeError("One or more case_id values do not match BM-0000 format")

validation_errors = []
for row_number, row in enumerate(rows, start=2):
    case_id = clean(row["case_id"]) or f"CSV row {row_number}"
    for field in required_values:
        if not clean(row.get(field)):
            validation_errors.append(f"{case_id}: required field '{field}' is blank")

    case_summary_sentences = len(split_sentences(clean(row["case_summary"])))
    if not 6 <= case_summary_sentences <= 8:
        validation_errors.append(f"{case_id}: case_summary must contain six to eight sentences")

    short_summary_sentences = len(split_sentences(clean(row["case_summary_short"])))
    if not 3 <= short_summary_sentences <= 4:
        validation_errors.append(f"{case_id}: case_summary_short must contain three to four sentences")

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", iso_missing_date(row["missing_date"]) or ""):
        validation_errors.append(f"{case_id}: missing_date is invalid")
    try:
        datetime.strptime(clean(row["last_verified_date"]), "%Y-%m-%d")
    except ValueError:
        validation_errors.append(f"{case_id}: last_verified_date must use YYYY-MM-DD")

    agencies = [clean(row[column]) for column in AGENCY_COLUMNS if clean(row[column])]
    phones = [clean(row[column]) for column in PHONE_COLUMNS if clean(row[column])]
    if not agencies or not phones:
        validation_errors.append(f"{case_id}: at least one lead agency and contact number are required")

    for field in ("primary_source_url", "secondary_source_url", "image_url"):
        parsed = urlparse(clean(row[field]))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            validation_errors.append(f"{case_id}: {field} must be a complete HTTP or HTTPS URL")

    image_name = Path(urlparse(clean(row["image_url"])).path).name
    if Path(image_name).stem != case_id or not (PROJECT / "images" / image_name).is_file():
        validation_errors.append(f"{case_id}: matching image file was not found in images/")

    latitude = number_or_none(row["latitude"])
    longitude = number_or_none(row["longitude"])
    if latitude is None or not -90 <= latitude <= 90:
        validation_errors.append(f"{case_id}: latitude is invalid")
    if longitude is None or not -180 <= longitude <= 180:
        validation_errors.append(f"{case_id}: longitude is invalid")

if validation_errors:
    raise RuntimeError("CSV validation failed:\n- " + "\n- ".join(validation_errors))

cases = [normalized_case(row) for row in rows]
DOCS_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)

for row, case in zip(rows, cases):
    (DOCS_DIR / f"{case['case_id']}.md").write_text(
        render_case_markdown(row, case),
        encoding="utf-8",
    )

if os.environ.get("DOCS_ONLY") == "1":
    print(f"Generated {len(cases)} Markdown case files in {DOCS_DIR}")
    raise SystemExit(0)

cases_payload = {
    "schema_version": "1.0.0",
    "generated_on": GENERATED_ON,
    "source": "/data/cases.csv",
    "source_encoding": source_encoding,
    "total_cases": len(cases),
    "cases": cases,
}

features = []
for case in cases:
    latitude = case["last_seen"]["latitude"]
    longitude = case["last_seen"]["longitude"]
    if latitude is None or longitude is None:
        continue
    features.append({
        "type": "Feature",
        "id": case["case_id"],
        "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
        "properties": {
            "case_id": case["case_id"],
            "full_name": case["full_name"],
            "case_status": case["case_status"],
            "classification": case["classification"],
            "case_classification": case["case_classification"],
            "missing_date": case["missing_date"],
            "city": case["last_seen"]["city"],
            "state": case["last_seen"]["state"],
            "case_summary_short": case["case_summary_short"],
            "image_url": case["image_url"],
            "document_path": case["document_path"],
        },
    })

geojson_payload = {
    "type": "FeatureCollection",
    "name": "black_missing_person_cases",
    "metadata": {
        "schema_version": "1.0.0",
        "generated_on": GENERATED_ON,
        "source": "/json/cases.json",
        "feature_count": len(features),
        "coordinate_order": "longitude, latitude",
    },
    "features": features,
}

years = [int(case["missing_date"][:4]) for case in cases if case["missing_date"]]
decades = [f"{year // 10 * 10}s" for year in years]
statistics_payload = {
    "schema_version": "1.0.0",
    "generated_on": GENERATED_ON,
    "source": "/json/cases.json",
    "total_cases": len(cases),
    "geocoded_cases": len(features),
    "cases_without_coordinates": len(cases) - len(features),
    "missing_date_range": {
        "earliest_year": min(years) if years else None,
        "latest_year": max(years) if years else None,
    },
    "by_case_status": ordered_counts(case["case_status"] for case in cases),
    "by_classification": ordered_counts(case["classification"] for case in cases),
    "by_case_classification": ordered_counts(case["case_classification"] for case in cases),
    "by_state": ordered_counts(case["last_seen"]["state"] for case in cases),
    "by_media_prominence": ordered_counts(case["media_prominence"] for case in cases),
    "by_missing_decade": ordered_counts(decades),
}

state_cases = defaultdict(list)
for case in cases:
    state_cases[case["last_seen"]["state"]].append(case)

states = []
for state_name in sorted(state_cases):
    items = state_cases[state_name]
    coordinates = [
        (item["last_seen"]["latitude"], item["last_seen"]["longitude"])
        for item in items
        if item["last_seen"]["latitude"] is not None and item["last_seen"]["longitude"] is not None
    ]
    center = None
    if coordinates:
        center = {
            "latitude": round(sum(point[0] for point in coordinates) / len(coordinates), 6),
            "longitude": round(sum(point[1] for point in coordinates) / len(coordinates), 6),
        }
    states.append({
        "state": state_name,
        "case_count": len(items),
        "geocoded_case_count": len(coordinates),
        "center": center,
        "case_status_counts": ordered_counts(item["case_status"] for item in items),
        "classification_counts": ordered_counts(item["classification"] for item in items),
        "case_ids": [item["case_id"] for item in items],
    })

states_payload = {
    "schema_version": "1.0.0",
    "generated_on": GENERATED_ON,
    "source": "/json/cases.json",
    "total_states_and_districts": len(states),
    "states": states,
}

latitudes = [feature["geometry"]["coordinates"][1] for feature in features]
longitudes = [feature["geometry"]["coordinates"][0] for feature in features]
dashboard_payload = {
    "schema_version": "1.0.0",
    "app": {
        "name": "Black Missing Persons Intelligence Database",
        "description": "A searchable database of missing Black people and unresolved disappearances.",
        "base_path": "/",
    },
    "data_sources": {
        "cases": "/json/cases.json",
        "geojson": "/json/geojson.json",
        "statistics": "/json/statistics.json",
        "states": "/json/states.json",
        "case_documents": "/docs/",
    },
    "default_view": "map",
    "map": {
        "center": {
            "latitude": round(sum(latitudes) / len(latitudes), 6) if latitudes else 39.5,
            "longitude": round(sum(longitudes) / len(longitudes), 6) if longitudes else -98.35,
        },
        "zoom": 4,
        "cluster_markers": True,
        "geojson_source": "/json/geojson.json",
    },
    "filters": [
        {"field": "case_status", "label": "Case Status", "type": "multi_select", "options": sorted({case["case_status"] for case in cases})},
        {"field": "classification", "label": "Classification", "type": "multi_select", "options": sorted({case["classification"] for case in cases})},
        {"field": "case_classification", "label": "Case Classification", "type": "multi_select", "options": sorted({case["case_classification"] for case in cases})},
        {"field": "last_seen.state", "label": "State", "type": "multi_select", "options_source": "/json/states.json"},
        {"field": "missing_date", "label": "Missing Date", "type": "date_range"},
    ],
    "search_fields": ["case_id", "full_name", "last_seen.city", "last_seen.state", "keywords"],
    "card_fields": ["full_name", "case_summary_short", "missing_date", "last_seen", "case_status", "image_url"],
    "sort_options": [
        {"value": "missing_date_desc", "label": "Newest cases", "field": "missing_date", "direction": "desc"},
        {"value": "missing_date_asc", "label": "Oldest cases", "field": "missing_date", "direction": "asc"},
        {"value": "full_name_asc", "label": "Name A–Z", "field": "full_name", "direction": "asc"},
    ],
    "accessibility": {
        "require_image_alt_text": True,
        "announce_filter_result_count": True,
        "respect_reduced_motion": True,
    },
}

payloads = {
    "cases.json": cases_payload,
    "geojson.json": geojson_payload,
    "dashboard-config.json": dashboard_payload,
    "statistics.json": statistics_payload,
    "states.json": states_payload,
}
for filename, payload in payloads.items():
    (JSON_DIR / filename).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

site_builder = Path(__file__).with_name("build_site.py")
if site_builder.exists() and os.environ.get("SKIP_SITE_BUILD") != "1":
    runpy.run_path(str(site_builder), run_name="__main__")

print(json.dumps({
    "case_documents": len(list(DOCS_DIR.glob("BM-*.md"))),
    "json_files": sorted(payloads),
    "geojson_features": len(features),
    "states_and_districts": len(states),
}, indent=2))
