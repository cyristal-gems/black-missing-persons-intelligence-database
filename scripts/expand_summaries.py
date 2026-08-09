#!/usr/bin/env python3
"""Expand canonical case summaries without introducing facts outside the CSV."""

import csv
import re
from datetime import datetime
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT / "data" / "cases.csv"

ABBREVIATIONS = {
    "D.C.": "D§C§",
    "a.m.": "a§m§",
    "p.m.": "p§m§",
    "Jr.": "Jr§",
    "St.": "St§",
    "U.S.": "U§S§",
}


def clean(value):
    return (value or "").strip()


def split_sentences(text):
    protected = clean(text)
    for original, token in ABBREVIATIONS.items():
        protected = protected.replace(original, token)
    protected = re.sub(r"\b([A-Z])\.(?=\s+[A-Z][A-Za-z'’()-]+)", r"\1¤", protected)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", protected)
    sentences = []
    for part in parts:
        for original, token in ABBREVIATIONS.items():
            part = part.replace(token, original)
        part = part.replace("¤", ".")
        if clean(part):
            sentences.append(clean(part))
    return sentences


def display_date(value):
    raw = clean(value)
    for pattern in ("%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(raw, pattern)
            return f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"
        except ValueError:
            continue
    raise ValueError(f"Unsupported date: {raw}")


def location(row, include_country=False):
    values = []
    for value in (clean(row["last_seen_city"]), clean(row["last_seen_state"])):
        if value and value not in values:
            values.append(value)
    if include_country:
        country = clean(row["last_seen_country"])
        if country and country not in values:
            values.append(country)
    return ", ".join(value for value in values if value)


def expanded_case_summary(row):
    original = split_sentences(row["case_summary"])
    if 6 <= len(original) <= 8:
        return " ".join(original)

    name = clean(row["full_name"])
    sentences = [
        f"{name} was {clean(row['age_at_missing'])} years old when the disappearance was reported on {display_date(row['missing_date'])}.",
        f"The recorded last-seen location is {location(row, include_country=True)}.",
    ]
    status_pattern = re.compile(
        r"^The current case status is (.*?), and the disappearance is classified as (.*?)\.$"
    )
    for sentence in original[1:]:
        match = status_pattern.match(sentence)
        if match:
            sentences.append(f"The current case status is {match.group(1)}.")
            sentences.append(f"The disappearance is classified as {match.group(2)}.")
        else:
            sentences.append(sentence)

    if len(sentences) < 6:
        sentences.append(f"The current investigative status is {clean(row['investigative_status'])}.")
    if len(sentences) < 6:
        agencies = [
            clean(row[column])
            for column in ("primary_agency", "secondary_agency", "tertiary_agency")
            if clean(row[column])
        ]
        sentences.append(f"The public record lists {'; '.join(agencies)} as investigating agencies.")

    if not 6 <= len(sentences) <= 8:
        raise ValueError(f"{row['case_id']}: generated {len(sentences)} case-summary sentences")
    return " ".join(sentences)


def preferred_name(full_name):
    parenthetical = re.search(r"\(([^)]+)\)", full_name)
    if parenthetical:
        return parenthetical.group(1)
    return full_name.split()[0]


def subject_complete(sentence, full_name):
    sentence = clean(sentence)
    name = preferred_name(full_name)
    if not sentence:
        return sentence
    if sentence.startswith((full_name, name + " ", "He ", "She ", "They ", "Her ", "His ", "Their ", "The ", "A ", "An ", "Authorities ", "Investigators ", "Police ", "Witnesses ", "Multiple ", "No ", "Neither ")):
        return sentence
    if sentence.startswith("Last seen "):
        return f"{name} was {sentence[0].lower() + sentence[1:]}"
    return f"{name} {sentence[0].lower() + sentence[1:]}"


def expanded_short_summary(row):
    name = clean(row["full_name"])
    original = split_sentences(row["case_summary_short"])
    if not original:
        raise ValueError(f"{row['case_id']}: case_summary_short is blank")
    if 3 <= len(original) <= 4:
        return " ".join(original)
    sentences = [
        f"At age {clean(row['age_at_missing'])}, {name} disappeared from {location(row)} on {display_date(row['missing_date'])}.",
        subject_complete(original[0], name),
    ]
    sentences.extend(original[1:2])
    sentences.append(f"The disappearance is classified as {clean(row['case_classification'])}.")
    if not 3 <= len(sentences) <= 4:
        raise ValueError(f"{row['case_id']}: generated {len(sentences)} short-summary sentences")
    return " ".join(sentences)


def main():
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    for row in rows:
        row["case_summary"] = expanded_case_summary(row)
        row["case_summary_short"] = expanded_short_summary(row)

    temp_path = CSV_PATH.with_suffix(".csv.tmp")
    with temp_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temp_path.replace(CSV_PATH)
    print(f"Expanded summary fields for {len(rows)} cases.")


if __name__ == "__main__":
    main()
