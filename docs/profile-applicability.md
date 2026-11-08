# Evidence-bearing applicability

Each criterion may contain `applicable_when`, an AND-list of comparisons. An omitted or empty list preserves unconditional criteria; it does not verify their scope. The engine is region-independent and does not infer building type, legal applicability or code edition from the jurisdiction label.

Example shape (illustrative, **not a regulatory rule**):

```json
{
  "applicable_when": [
    {"fact": "use", "operator": "==", "value": "office"},
    {"fact": "internal_area", "operator": ">", "value": 15, "unit": "m2"}
  ]
}
```

Supply facts as the optional MCP `evaluate_profile` argument `context`, or a JSON file passed to CLI `criteria-check --context`:

```json
{
  "use": {"value": "office", "evidence": "Project brief, room A"},
  "internal_area": {"value": 24, "unit": "m2", "evidence": "Verified room A boundary drawing"}
}
```

Numeric comparisons require matching units; the evaluator does not convert units or accept booleans as numbers. Equality also supports strings and booleans with matching types. Every used fact requires a nonempty evidence string, which is a reference supplied by the caller, not independent verification of its contents.

All conditions met: evaluate the measured criterion. A known false condition with all inputs evidenced: report `not_applicable` and retain the checked facts. Any missing, ill-typed or unevidenced condition: report `unverified`, even if another condition is false. This conservative behavior prevents partial context from establishing an exemption. An entire profile with no applicable criteria is `unverified`, never a vacuous pass.

A rule pack author must encode all required scope conditions and exceptions; the evaluator cannot detect an omitted legal exception. Complex OR conditions, formula-based requirements and comprehensive code coverage are not implemented. Hong Kong source extraction remains separate from adopting a verified rule pack.
