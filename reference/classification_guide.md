# Classification Guide

This guide defines the controlled classifications used in `data/cases.csv`. Classifications summarize the available record; they do not determine criminal liability and must not be treated as findings beyond what cited sources support.

## Case Status

| Value | Use |
|---|---|
| `Missing` | The person has not been located and the dataset does not record an official or sufficiently supported presumption of death. |
| `Presumed Deceased` | The available official or court-supported record indicates that the person is believed to be deceased although their remains have not been recovered or identified. |

## Demographic Classification

| Value | Use |
|---|---|
| `Child` | The person was younger than 18 on the recorded missing date. |
| `Adult Woman` | The adult is categorized as a woman in the source record. |
| `Adult Man` | The adult is categorized as a man in the source record. |
| `LGBTQ+` | The person's LGBTQ+ identity is documented by a cited source and is relevant to the project's discovery or coverage analysis. |
| `Elder` | The record is grouped for age-related visibility because the person was an older adult at disappearance. |

`classification` is a project navigation field. It should not be inferred from a name, photograph, or stereotype. When a source-supported identity overlaps with another demographic grouping, use the value that best reflects the project's documented categorization and explain important context in the narrative when relevant.

## Case Classification

| Value | Use |
|---|---|
| `Endangered Missing` | Authorities or established case sources indicate that age, health, circumstances, vulnerability, or elapsed time may place the person at elevated risk. |
| `Missing Under Mysterious Circumstances` | The disappearance is unresolved and the known circumstances are unusual, incomplete, or unexplained, without a more specific supported classification. |
| `Suspected Homicide` | Authorities, court records, or the cited case record identify homicide as a suspected explanation. This does not imply that a person has been charged or convicted. |
| `Stranger Abduction` | The supported case record identifies or strongly classifies the disappearance as an abduction by a non-family member. |
| `Suspected Abduction` | The supported record indicates possible abduction but does not establish the abductor's relationship or a conclusive abduction finding. |

## Investigative Status

The `investigative_status` field records procedural posture separately from `case_status` and `case_classification`.

| Value | Meaning |
|---|---|
| `Open / Unresolved — Missing-Person Investigation` | The person remains missing and the case is presented as an unresolved missing-person investigation. |
| `Open / Unresolved — Abduction Investigation` | The case remains unresolved and is investigated or officially presented as an abduction. |
| `Homicide Conviction — Remains Unrecovered` | A homicide conviction has occurred, but the person's remains have not been recovered. |
| `Cold Case — Unresolved` | The disappearance remains unresolved and is publicly treated as a cold case. |
| `Open / Unresolved — Suspected Homicide` | The case remains open or unresolved and homicide is an officially supported theory. |
| `Cold Case — Suspected Homicide` | The matter is treated as a cold case and homicide remains an officially supported theory. |
| `Open / Unresolved — Homicide Investigation` | Authorities publicly describe the active or unresolved matter as a homicide investigation. |

## Media Prominence

| Value | Meaning |
|---|---|
| `well_known` | The case has sustained or broad public and media recognition. |
| `moderately_known` | The case has meaningful coverage but not sustained broad recognition. |
| `obscure_or_limited_coverage` | The case has comparatively limited, local, intermittent, or difficult-to-locate coverage. |

Media prominence is an editorial discovery aid, not a measure of a case's importance. Every case should receive the same factual and sourcing standards.

## Classification Rules

1. Base every classification on the current cited record.
2. Prefer the most specific value that the sources support.
3. Do not convert a theory into a confirmed fact.
4. Keep demographic, circumstance, outcome, and investigative fields separate.
5. When official language changes, update the CSV, narrative, keywords, and verification date together, then regenerate derived files.

