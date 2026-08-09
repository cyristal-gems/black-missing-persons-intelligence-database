# Methodology

## Purpose and Scope

The Black Missing Persons Intelligence Database is a public, source-backed collection designed to improve the visibility, organization, and accessibility of missing-person case information concerning Black individuals. The project supports research, public awareness, data exploration, and future technical integrations. It is not a law-enforcement system and does not make determinations of guilt.

## Canonical Data Model

`data/cases.csv` is the project's single source of truth. Case documents and integration datasets are generated from that file:

```text
data/cases.csv
├── docs/BM-0001.md through docs/BM-0110.md
├── json/cases.json
├── json/geojson.json
├── json/dashboard-config.json
├── json/statistics.json
└── json/states.json
```

Changes should be made in the CSV first. Direct edits to generated Markdown or JSON files will be overwritten the next time the generators run.

## Case Identification and Inclusion

Each record receives a permanent sequential project ID in `BM-0000` format. A record is included when public sources provide enough information to identify the person, establish a missing-person case, and cite at least a principal and secondary source. Inclusion does not imply that all available facts are complete or that every jurisdiction uses the same terminology.

## Source Selection

The dataset prioritizes dedicated missing-person profiles, government or law-enforcement bulletins, missing-child posters, official alerts, and established case-information organizations. A secondary source is used to corroborate or supplement the principal record. Source links are stored in the canonical CSV and rendered as active links in every case document.

When sources disagree, the record should:

1. Prefer current official information for status and investigative posture.
2. Preserve material uncertainty rather than selecting an unsupported version.
3. Attribute investigative theories to authorities or the source that stated them.
4. Avoid repeating allegations that are irrelevant, unsupported, or presented as fact without sufficient evidence.

## Narrative Standards

All case writing uses a neutral, factual style. Confirmed events, official statements, investigative theories, and unresolved questions must remain distinguishable. Language must not imply guilt, death, abduction, or homicide unless the cited record supports that characterization.

The CSV contains five reviewed narrative fields:

- `case_summary` provides a six- to eight-sentence canonical account of the known facts and circumstances.
- `case_summary_short` provides a compact three- or four-sentence version for case cards, map-marker hovers, tables, and dashboards.
- `investigation_summary` describes supported investigative activity and status.
- `timeline` stores ordered, substantive developments as structured JSON. Every event contains exactly `label` and `description`; dated events use a readable date as the label. Routine verification and unchanged open-status checks are excluded.
- `notes` records case-specific context that does not belong in the principal narrative.

## Classification and Keywords

Status, demographic classification, circumstance classification, and investigative status are maintained as separate concepts. Definitions appear in `classification_guide.md`. Keywords are controlled discovery terms defined in `keyword_dictionary.md`; they do not override structured fields.

## Location Data

Latitude and longitude represent the generalized recorded last-seen locality in WGS 84 decimal degrees. They support mapping and geographic aggregation but should not be interpreted as an exact disappearance location unless a cited source establishes that precision. Public records should avoid publishing sensitive residential coordinates when a city-level location is sufficient.

## Images

Each case record points to a repository image whose filename matches the case ID. Images are used for identification and public-awareness purposes. The Markdown generator converts the stored image URL into a repository-relative path so the case pages can render on GitHub and compatible web applications.

## Generation Workflow

Run the documentation-only generator after narrative or metadata edits that affect case pages:

```bash
python3 scripts/generate_docs.py
```

Run the full generator whenever the canonical CSV changes and all derived files need to be synchronized:

```bash
python3 scripts/generate_assets.py
```

The full generator validates required columns and case ID formatting, writes all case documents, and rebuilds the JSON, GeoJSON, statistics, state, and dashboard configuration files.

## Quality Review

Before publishing an update:

1. Confirm the person's identity, missing date, age, and last-seen locality against the cited records.
2. Verify that both source URLs open and still support the associated claims.
3. Reconcile classification and investigative-status changes across every relevant CSV field.
4. Review narrative wording for neutrality, clarity, and unsupported conclusions.
5. Validate timeline JSON and confirm that events appear in the intended order.
6. Confirm the repository image matches the case ID.
7. Update `last_verified_date` only after the record and links have been reviewed.
8. Run the full generator and confirm all generated files parse and render correctly.

## Corrections and Updates

Corrections should be evidence-based and made in the canonical CSV. A substantive update should include the supporting source, revised narrative or classification fields, and a new `last_verified_date`. Generated files must then be rebuilt so the public documents and integrations remain synchronized.

## Limitations

Public missing-person information can be incomplete, inconsistent, delayed, or removed. Media prominence is inherently editorial and can change over time. Coordinates are generalized, classifications reflect the best supported public record at the time of verification, and absence from this database does not indicate that a case is less important or no longer active.
