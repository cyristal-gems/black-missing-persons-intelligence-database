#!/usr/bin/env python3
"""Populate source-backed physical details and clean generic timeline labels.

This is intentionally a one-time editorial utility. It writes the verified
results into the CSV so normal site builds never depend on a live website.
"""

import argparse
import csv
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT / "data" / "cases.csv"

CHARLEY_FIELDS = (
    "Height and Weight",
    "Clothing/Jewelry Description",
    "Medical Conditions",
    "Distinguishing Characteristics",
)
BAM_FIELDS = (
    "Gender",
    "Race",
    "Complexion",
    "Height",
    "Weight",
    "Hair Color",
    "Hair Length",
    "Eye Color",
    "Last Seen Wearing",
    "Identifying Marks or Characteristics",
)

# Source-specific details for records without a Charley Project or Black and
# Missing Foundation profile. Every value below is copied or conservatively
# normalized from one of the case's URLs in data/cases.csv.
MANUAL_PHYSICAL = {
    "BM-0018": {
        "Height and weight": "3'0\"; 28 pounds",
        "Hair and eyes": "Black hair; brown eyes",
        "Clothing/jewelry": "Knee-length flowered nightshirt and tan barrettes in her hair",
        "Distinguishing characteristics": "Scar on her upper right leg, brown birthmark on her face, and decayed upper teeth. Her nickname is Grammy-Boo.",
    },
    "BM-0045": {
        "Height and weight": "5'2\"; 105 pounds",
        "Hair and eyes": "Black hair; brown eyes",
        "Distinguishing characteristics": "Her ears are pierced.",
    },
    "BM-0048": {
        "Race": "Black or African American",
        "Hair and eyes": "Black hair; brown eyes",
        "Distinguishing characteristics": "He had curls in his hair.",
    },
    "BM-0049": {
        "Height and weight": "Approximately 2'6\"; approximately 25 pounds",
        "Hair and eyes": "Black hair; brown eyes",
    },
    "BM-0050": {
        "Sex and race": "Female; Black",
        "Height and weight": "5'8\"; 200 pounds",
        "Hair and eyes": "Black hair; brown eyes",
    },
    "BM-0065": {
        "Sex and race": "Male; Black",
        "Height and weight": "6'9\"; 300 pounds",
        "Hair and eyes": "Black hair; brown eyes",
    },
    "BM-0073": {
        "Height and weight": "5'8\"; 130 pounds",
        "Hair and eyes": "Black hair; brown eyes",
        "Clothing/jewelry": "Gray sweatpants, a black jacket, and a black scarf",
        "Distinguishing characteristics": "Both ears pierced; tattoos on both arms; a birthmark on the left side of the abdomen.",
    },
    "BM-0074": {
        "Sex and race": "Male; Black",
        "Height and weight": "5'8\"; 165 pounds",
        "Hair and eyes": "Black hair; brown eyes",
        "Distinguishing characteristics": "Born without his right hand and lower right forearm.",
    },
    "BM-0063": {
        "Height and weight": "5'8\" to 6'0\"; 160 to 175 pounds",
        "Hair and eyes": "Sandy brown hair; brown eyes",
        "Clothing/jewelry": "Short-sleeved button-down shirt, blue jeans, brown Timberland boots, diamond earrings, and a watch with white stones around the face and a silver metal band",
        "Distinguishing characteristics": "Long dreadlocks; pierced ears; scars on the right shoulder and right hand; a dark birthmark on the abdomen; three tattoos; and two gold-capped upper front teeth.",
    },
    "BM-0066": {
        "Height and weight": "5'11\"; 195 pounds",
        "Hair and eyes": "Black hair; brown eyes",
        "Distinguishing characteristics": "Tattoos on both arms and scars on his right hand, right shoulder, right foot, right forearm, left arm, face, and chest.",
    },
    "BM-0068": {
        "Height and weight": "5'7\"; 195 pounds",
        "Hair and eyes": "Brown hair; brown eyes",
        "Clothing/jewelry": "Blue sweatshirt with cut-off sleeves and blue jean shorts",
        "Distinguishing characteristics": "Wears eyeglasses or contact lenses.",
    },
}


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        value = " ".join(data.split())
        if value:
            self.parts.append(value)


def fetch_parts(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        body = response.read().decode("utf-8", "ignore")
    parser = TextParser()
    parser.feed(body)
    return parser.parts


def next_value(parts, label):
    for index, value in enumerate(parts[:-1]):
        if value.strip().rstrip(":") == label:
            candidate = parts[index + 1].strip()
            if candidate and candidate not in {"Unknown", "N/A", "Not Available"}:
                return candidate
    return ""


def charley_details(parts):
    details = {}
    for label in CHARLEY_FIELDS:
        value = next_value(parts, label)
        if value:
            details[label] = value
    return details


def bam_details(parts):
    details = {}
    for label in BAM_FIELDS:
        value = next_value(parts, label)
        if value:
            details[label] = value
    return details


def physical_source(row):
    if row["case_id"] in MANUAL_PHYSICAL:
        return row["primary_source_url"], "manual"
    urls = (row["primary_source_url"], row["secondary_source_url"])
    for domain in ("charleyproject.org", "blackandmissinginc.com"):
        for url in urls:
            if domain in url:
                return url, domain
    return row["primary_source_url"], "manual"


def development_label(description):
    text = description.lower()
    rules = (
        (r"backpack.*recover", "Backpack recovered"),
        (r"vehicle.*(recover|found)|car.*found", "Vehicle recovered"),
        (r"mother.*convicted|convicted.*murder|conviction", "Murder conviction"),
        (r"blood.*sim|sim card|evidence.*found", "Evidence recovered"),
        (r"body.*found|found deceased|remains.*found", "Related death confirmed"),
        (r"fbi.*reward|reward", "Reward announced"),
        (r"homicide investigation|suspected homicide|foul play", "Investigation reclassified"),
        (r"highway cameras|camera", "Vehicle captured on camera"),
        (r"gps signal", "Phone signal lost"),
        (r"witness.*(vehicle|pushed)", "Witness account reported"),
        (r"search", "Search conducted"),
        (r"illegal adoption", "Investigative theory reported"),
        (r"belongings|money.*left", "Personal belongings recovered"),
    )
    for pattern, label in rules:
        if re.search(pattern, text):
            return label
    return ""


def clean_timeline(raw):
    events = json.loads(raw)
    cleaned = []
    for event in events:
        label = event["label"].strip()
        description = event["description"].strip()
        if label != "Subsequent development":
            cleaned.append({"label": label, "description": description})
            continue
        specific = development_label(description)
        if specific:
            cleaned.append({"label": specific, "description": description})
    return cleaned


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="update data/cases.csv")
    args = parser.parse_args()

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    for field in ("physical_description", "physical_description_source_url"):
        if field not in fieldnames:
            fieldnames.append(field)

    failures = []
    counts = {"scraped": 0, "manual": 0, "timeline_removed": 0, "timeline_relabeled": 0}
    scraped_details = {}
    scrape_jobs = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        for row in rows:
            source_url, source_type = physical_source(row)
            if source_type != "manual":
                future = executor.submit(fetch_parts, source_url)
                scrape_jobs[future] = (row["case_id"], source_url, source_type)
        for future in as_completed(scrape_jobs):
            case_id, source_url, source_type = scrape_jobs[future]
            try:
                parts = future.result()
                scraped_details[case_id] = (
                    charley_details(parts)
                    if source_type == "charleyproject.org"
                    else bam_details(parts)
                )
            except Exception as error:
                failures.append(f"{case_id}: {error}")

    for row in rows:
        case_id = row["case_id"]
        source_url, source_type = physical_source(row)
        if source_type == "manual":
            details = MANUAL_PHYSICAL.get(case_id, {})
            counts["manual"] += 1
        else:
            details = scraped_details.get(case_id, {})
            counts["scraped"] += 1
        if not details:
            failures.append(f"{case_id}: no physical details extracted")
        row["physical_description"] = json.dumps(details, ensure_ascii=False, separators=(",", ":"))
        row["physical_description_source_url"] = source_url

        before = json.loads(row["timeline"])
        after = clean_timeline(row["timeline"])
        counts["timeline_removed"] += len(before) - len(after)
        counts["timeline_relabeled"] += sum(
            old.get("label") == "Subsequent development"
            for old in before
        ) - (len(before) - len(after))
        row["timeline"] = json.dumps(after, ensure_ascii=False, separators=(",", ":"))

    print(json.dumps({"cases": len(rows), **counts, "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)
    if args.write:
        with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
