# Websites Review acceptance checks

Test basis: [Spec Driven Development document (SDD)](spec_driven_development.md), WEB-01–WEB-12, version 1
Test item: Administration read contracts, category mutation, and Websites interface
Approach and exit criteria: [Test Plan (TP)](test_plan.md)

## Coverage and setup

Use an isolated database and browser environment. Seed active category C, another active category C2, a deleted category, two administrators, and a non-administrator. Give cited fixtures one citation in an isolated edition and refresh aggregates through the existing fixture helper used by `admin-websites-page-keyset.test.ts:66–70` via `cache_registry.refresh_command`. M1 is the classifier/reader migration in the [Implementation Plan (IP)](implementation_plan.md#2-add-central-classification-and-compatible-readers).

Use stored reason values from the shared confirmation-rule fixture, rather than abbreviations, when seeding:

| Key | Domain ending | Status | Category | Attempts / reason | Cited | Active | Expected classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V | org | verified | C | 0 / none | Yes | Yes | Neither |
| P | org | pending | None | 0 / none | Yes | Yes | Pending |
| PC | org | pending | C | 0 / none | No | Yes | Pending |
| U0 | org | unverified | C | 0 / page does not identify the site | Yes | Yes | Pending |
| U2H | cn | unverified | C | 2 / host answered 404 | Yes | Yes | Pending |
| U3 | org | unverified | C | 3 / page does not identify the site | Yes | Yes | Review |
| U3H | cn | unverified | C | 3 / host answered 404 | No | Yes | Review |
| User Story (US) | co.uk | unverified | C | 1 / site answered 200 and its own page does not identify the site | Yes | Yes | Review |
| UD | org | unverified | C | 3 / host answered 404 | Yes | No | Review, excluded from active lists |

The active fixture has three Review rows, four Pending rows, and six rows in the existing All population. These totals differ intentionally. Classification still returns Review for UD even though active lists exclude it.

Use domain names with the `__test_wrs-` prefix, the lowercase fixture key, and the table's ending: for example, `__test_wrs-u3.org` and `__test_wrs-u3h.cn`. Assign deterministic creation times and unique IDs for pagination. Namespace all fixture domains and associated rows. Separate functional fixtures from the larger dataset used in T20.

## Read and authorization cases

| ID / requirement | Preconditions and action/input | Expected outcome |
| --- | --- | --- |
| T01 / WEB-01 | Evaluate the classifier for all nine rows, plus one supported status outside pending/unverified | Results match the fixture; the extra status returns null |
| T02 / WEB-01 | Capture confirmation readers before M1; install it and compare the same fixture | Waiting-for-confirm remains U0/U2H; active parked readers remain U3/U3H/User Story (US); no duplicate parked rule is introduced |
| T03 / WEB-02 | Read active Review, Pending, and All without extra filters | Review = U3/U3H/User Story (US); Pending = P/PC/U0/U2H; All = V/P/U0/U2H/U3/User Story (US); UD is absent |
| T04 / WEB-03 | On Review, apply `cn`, `.CN`, ` cn `, `cn.`, `co.uk`, `uk`, and empty input separately | The first four select U3H; co.uk/uk select User Story (US); empty input restores all three |
| T05 / WEB-03 | Combine domain search, category, and ending; separately submit `c%n`, `*.cn`, and unsupported queue `other` | Combined results satisfy every filter; invalid inputs return `22023` without a broad fallback |
| T06 / WEB-04 | For each queue and a combined-filter subset, compare list IDs, count, and matching-ID selection | IDs are identical as sets, count equals set size, and empty populations agree |
| T07 / WEB-04 | Traverse a stable multi-page fixture with equal sort values; change tab/filter midway | No duplicate or missing IDs in stable traversal; changed context starts with a fresh cursor; Pending/Review default to Added descending |
| T08 / WEB-05 | Call administration reads and mutation directly as anonymous and non-administrator identities; inspect rows/history | Access is denied; mutation returns `42501`; no data change or successful-change journal entry appears |

## Editing and mutation cases

Reset the functional fixture before each independent case. Inspect persisted values through a fresh connection rather than only browser state.

| ID / requirement | Preconditions and action/input | Expected outcome |
| --- | --- | --- |
| T09 / WEB-06 | Assign C2 from each tab; exercise Enter, save, Escape, cancel, and a second row while editing | One row edits at a time; save submits once; cancel makes no request; saving state prevents another submission |
| T10 / WEB-06 | Reject an inline save after a new category is selected | Error is shown; row remains in edit mode with that selection; no success confirmation appears |
| T11 / WEB-07 | Administrator assigns C2 to U3 and User Story (US); inspect fresh rows and journal | Return count 2; category C2, verified/high, attempts 0, manual reason/time, `user:<UUID>` actor; both leave Review and have attributable history |
| T12 / WEB-07 | Two administrator sessions commit different categories for one row in a controlled order | Last committed category is current; both committed changes retain the correct actors |
| T13 / WEB-08 | Clear U3 using `__clear__`; separately assign and clear UD | U3 has no category, Pending status, attempts 0, and cleared verification metadata; UD remains unchanged and returns 0 changed rows |
| T14 / WEB-09 | Submit 0, 500, and 501 IDs, including repeated IDs; submit unknown/deleted categories | Empty authorized request returns 0; 500 is accepted; 501 supplied IDs is rejected before writes; invalid categories return `22023` |
| T15 / WEB-09 | Force a journal failure during an otherwise valid multi-row request | The request fails; all website changes and journal inserts from that request roll back |
| T16 / WEB-09 | Select 1,001 active rows. Run success, second-batch rejection, and second-batch post-commit response-loss variants | Success uses 500/500/1. Rejection stops after batch 2 with 500 confirmed changes and 501 IDs remaining. Response loss stops with 500 confirmed, 500 unresolved, and 1 unattempted; reconciliation finds actual state before an explicit retry |
| T17 / WEB-10 | Assign/clear a Review row and repeat after partial bulk completion | Confirmed rows and all affected counts refresh; assignment leaves Review, clear enters Pending; partial/uncertain work is not labeled fully successful |

## Interface, compatibility, and performance cases

| ID / requirement | Preconditions and action/input | Expected outcome |
| --- | --- | --- |
| T18 / WEB-11 | Inspect all tabs at 1,280/1,600 px with long labels; apply and close More filters | Ending field is in More filters with active indication; Review shows reason and hides Check category; school/citation/Add New controls remain All-only; old Review filter is absent |
| T19 / WEB-11 | Run existing callers without new optional arguments during the compatibility release | Existing All population and old supported calls retain their contract; generated TypeScript signatures match database functions |
| T20 / WEB-12 | On the recorded production-shaped snapshot, record query text, sort, schema/index definitions, dataset, and cache conditions; measure both default first pages, a 500-row mutation with journaling, and concurrent-index builds | Each query ≤1,000 ms and ≤5,000 shared-buffer hits plus reads; mutation <8 seconds; indexes valid with build duration/size recorded |

## Procedure and cleanup

Confirm build, schema, roles, helper version, and fixture revision before a run. Run T01–T08 before dependent UI checks. Use isolated test interception to distinguish rejection before commit from response loss after commit. Preserve the actual sequence of requests for T16.

Record actual results outside this specification. If a required interception point or production-shaped dataset is unavailable, mark the case blocked; do not substitute a smaller or different check and call it passed. Reset changed rows between variants, remove isolated fixtures afterward, and verify cleanup.
