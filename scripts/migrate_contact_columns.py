#!/usr/bin/env python3
"""Align agency phone columns with the agencies they belong to."""

import csv
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT / "data" / "cases.csv"

MULTI_AGENCY_PHONE_COUNTS = {
    "BM-0003": [1, 1],
    "BM-0004": [1, 1],
    "BM-0005": [1, 1],
    "BM-0006": [1, 1],
    "BM-0007": [1, 1],
    "BM-0012": [1, 1],
    "BM-0013": [2, 1],
    "BM-0021": [1, 1],
    "BM-0061": [1, 1, 1],
    "BM-0062": [1, 0],
    "BM-0063": [1, 1, 1],
    "BM-0066": [1, 0],
}

OLD_CONTACT_FIELDS = {
    "primary_agency", "secondary_agency", "tertiary_agency",
    "primary_agency_phone", "secondary_agency_phone", "tertiary_agency_phone",
}
NEW_CONTACT_FIELDS = [
    "primary_agency", "primary_agency_phone", "primary_agency_alternate_phone",
    "secondary_agency", "secondary_agency_phone", "tertiary_agency", "tertiary_agency_phone",
]


def clean(value):
    return (value or "").strip()


def main():
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        old_fields = list(reader.fieldnames or [])

    if all(field in old_fields for field in NEW_CONTACT_FIELDS):
        print("Contact columns are already aligned.")
        return

    insert_at = old_fields.index("primary_agency")
    new_fields = (
        old_fields[:insert_at]
        + NEW_CONTACT_FIELDS
        + [field for field in old_fields[insert_at:] if field not in OLD_CONTACT_FIELDS]
    )

    for row in rows:
        agencies = [
            clean(row.get(column))
            for column in ("primary_agency", "secondary_agency", "tertiary_agency")
            if clean(row.get(column))
        ]
        phones = [
            clean(row.get(column))
            for column in ("primary_agency_phone", "secondary_agency_phone", "tertiary_agency_phone")
            if clean(row.get(column))
        ]

        if len(agencies) == 1:
            grouped_phones = [phones]
        else:
            counts = MULTI_AGENCY_PHONE_COUNTS.get(clean(row.get("case_id")))
            if counts is None or len(counts) != len(agencies) or sum(counts) != len(phones):
                raise ValueError(f"{row.get('case_id')}: agency-phone grouping is not defined")
            grouped_phones = []
            phone_index = 0
            for count in counts:
                grouped_phones.append(phones[phone_index:phone_index + count])
                phone_index += count

        primary_phones = grouped_phones[0]
        secondary_phones = grouped_phones[1] if len(grouped_phones) > 1 else []
        tertiary_phones = grouped_phones[2] if len(grouped_phones) > 2 else []
        if len(primary_phones) > 2 or len(secondary_phones) > 1 or len(tertiary_phones) > 1:
            raise ValueError(f"{row.get('case_id')}: contact schema needs additional phone columns")

        row["primary_agency_phone"] = primary_phones[0] if primary_phones else ""
        row["primary_agency_alternate_phone"] = primary_phones[1] if len(primary_phones) > 1 else ""
        row["secondary_agency_phone"] = secondary_phones[0] if secondary_phones else ""
        row["tertiary_agency_phone"] = tertiary_phones[0] if tertiary_phones else ""

    temp_path = CSV_PATH.with_suffix(".csv.tmp")
    with temp_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=new_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temp_path.replace(CSV_PATH)
    print(f"Aligned contact columns for {len(rows)} cases.")


if __name__ == "__main__":
    main()
