# Data Dictionary

This dictionary defines every field in `data/cases.csv`, the canonical dataset for the Black Missing Persons Intelligence Database. Markdown documents and JSON integration files are generated from these values.

## Field Definitions

| Field | Type | Required | Description and format |
|---|---|---:|---|
| `case_id` | String | Yes | Permanent project identifier in `BM-0000` format. It is unique and must not be reused. |
| `full_name` | String | Yes | Person's full name as presented by the cited case sources. |
| `case_status` | Controlled string | Yes | High-level outcome: `Missing` or `Presumed Deceased`. |
| `classification` | Controlled string | Yes | Demographic grouping used by the project: `Child`, `Adult Woman`, `Adult Man`, `LGBTQ+`, or `Elder`. |
| `missing_date` | Date | Yes | Recorded date of disappearance. The generator accepts `MM/DD/YY` or `MM/DD/YYYY` and exports ISO `YYYY-MM-DD` dates to JSON. |
| `age_at_missing` | Integer | Yes | Age in completed years on the missing date. |
| `case_classification` | Controlled string | Yes | Circumstance-based classification. Approved values are documented in `classification_guide.md`. |
| `last_seen_city` | String | Yes | City or locality associated with the recorded last-seen location. |
| `last_seen_state` | String | Yes | State or district associated with the recorded last-seen location. |
| `last_seen_country` | String | Yes | Country associated with the recorded last-seen location. |
| `case_summary` | Text | Yes | Detailed six- to eight-sentence canonical case summary containing the principal known facts and context. |
| `case_summary_short` | Text | Yes | Three- or four-sentence overview used for case cards, map-marker hovers, tables, dashboards, and search results. |
| `investigation_summary` | Text | Yes | Reviewed description of the investigative status, agencies, public developments, and tip channels supported by the sources. |
| `timeline` | JSON text | Yes | Ordered JSON array of substantive case events. Every object contains exactly `label` and `description`; a dated event uses a readable date as its label. Routine verification or open-status checks are not timeline events. |
| `notes` | Text | Yes | Case-specific editorial or interpretive notes that do not belong in the factual narrative. Notes must not introduce unsupported claims. |
| `primary_agency` | String | Yes | First investigating agency listed in the reviewed public case material. This ordering does not independently establish command authority. |
| `secondary_agency` | String | No | Second investigating agency listed for the case, when applicable. |
| `tertiary_agency` | String | No | Third investigating agency listed for the case, when applicable. |
| `primary_agency_phone` | String | Yes | Main public telephone number listed for the primary agency. |
| `primary_agency_alternate_phone` | String | No | Additional public telephone number for the primary agency, when applicable. |
| `secondary_agency_phone` | String | No | Public telephone number listed for the secondary agency, when applicable. |
| `tertiary_agency_phone` | String | No | Public telephone number listed for the tertiary agency, when applicable. |
| `primary_source_url` | URL | Yes | Active HTTP or HTTPS link to the principal case source. |
| `secondary_source_url` | URL | Yes | Active HTTP or HTTPS link used to corroborate or supplement the principal source. |
| `primary_source_type` | Controlled string | Yes | Type of primary record. Approved values are documented below. |
| `media_prominence` | Controlled string | Yes | Editorial indicator of public visibility: `well_known`, `moderately_known`, or `obscure_or_limited_coverage`. |
| `keywords` | Delimited string | Yes | Lowercase discovery terms separated with vertical bars (`|`). Definitions are maintained in `keyword_dictionary.md`. |
| `investigative_status` | Controlled string | Yes | Most specific supported description of the investigation's current procedural posture. |
| `image_url` | URL | Yes | Raw GitHub URL for the repository image associated with the matching case ID. |
| `latitude` | Decimal | Yes | Latitude of the generalized last-seen locality in WGS 84 decimal degrees, from `-90` to `90`. |
| `longitude` | Decimal | Yes | Longitude of the generalized last-seen locality in WGS 84 decimal degrees, from `-180` to `180`. |
| `last_verified_date` | Date | Yes | Most recent date on which the record and its cited links were reviewed, in ISO `YYYY-MM-DD` format. |

## Primary Source Types

| Value | Meaning |
|---|---|
| `missing_person_case_profile` | A dedicated missing-person case profile maintained by a case-information organization. |
| `official_missing_child_poster` | A missing-child poster issued by an official or congressionally authorized clearinghouse. |
| `law_enforcement_case_update` | A public update issued by an investigating law-enforcement agency. |
| `official_missing_person_alert` | An official alert requesting public assistance in locating the person. |
| `law_enforcement_case_profile` | A case page maintained by a law-enforcement agency. |
| `official_missing_person_profile` | A profile maintained by an official missing-person system or government body. |
| `official_missing_person_bulletin` | A formal missing-person bulletin issued by an official agency. |

## Null and Formatting Rules

- Required fields must not be blank.
- Unknown information must not be guessed. If the schema later permits a null value, it should be represented consistently and explained in this dictionary.
- Each agency and phone number has its own column; keywords use vertical bars.
- Narrative fields use plain text without Markdown headings. The generator supplies document structure.
- Source and image links must use complete HTTP or HTTPS URLs.
- Coordinates identify the recorded locality and should not be interpreted as an exact disappearance point unless a cited source explicitly establishes that precision.
