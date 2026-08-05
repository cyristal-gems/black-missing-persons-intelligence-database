# Keyword Dictionary

Keywords support filtering and discovery. They supplement the structured classification fields and must not be used to make unsupported factual claims. In `data/cases.csv`, multiple keywords are separated with a vertical bar (`|`).

## Current Keywords

| Keyword | Meaning |
|---|---|
| `adult` | The person was 18 or older on the recorded missing date. |
| `child` | The person was younger than 18 on the recorded missing date. |
| `woman` | The case record categorizes the missing adult as a woman. |
| `man` | The case record categorizes the missing adult as a man. |
| `endangered_missing` | The structured case classification is Endangered Missing. |
| `endangered` | A cited record describes the person as endangered or identifies circumstances creating elevated risk. |
| `missing` | General missing-person discovery term used when a more specific keyword alone would not provide sufficient search coverage. |
| `non-family_abduction` | The supported record describes an abduction by a person who was not a family member. |
| `lgbtq_plus_source_documented` | An LGBTQ+ identity or related context is expressly documented by a cited source. It must never be inferred. |
| `endangered_/_involuntary_/_other` | Legacy source-category label combining endangered, involuntary, or other circumstances. Retained for source fidelity and compatibility. |
| `other` | A source taxonomy uses an Other category that is not represented by a more precise current keyword. |
| `endangered_runaway` | A cited record combines runaway terminology with an endangered designation. The term reflects source language and should not be used to minimize risk. |
| `endangered_/_involuntary` | Legacy source-category label combining endangered or involuntary circumstances. Retained for source fidelity and compatibility. |
| `cold_case` | Authorities or the cited case record publicly identify the investigation as a cold case. |
| `endangered_missing_/_homicide_investigation` | The record combines an endangered-missing classification with an officially supported homicide investigation. |

## Keyword Rules

- Use lowercase terms.
- Use underscores instead of spaces for new keywords.
- Do not add identity, crime, relationship, or outcome keywords based on inference.
- Keep legacy slash-delimited terms only where compatibility with the source taxonomy or existing integrations requires them.
- Prefer structured CSV fields for primary filtering; keywords provide additional discovery context.
- Add a new keyword to this dictionary before using it in the dataset.
- When replacing a legacy term, update the CSV, dashboard configuration, documentation, and downstream integrations in the same change.

