# Validation Results: Context-Aware vs. Diff-Only Review

Test repo: sqlparse (~2500 lines, external, not authored by us).
Method: 3 deliberate bugs introduced; each function reviewed twice --
once with full context (dependency graph + semantic retrieval), once
with only the changed function itself (diff-only baseline).

## Summary

| Function changed | Context-aware caught | Diff-only caught |
|---|---|---|
| `grouping.group` | 1 issue (missing input validation) | 0 issues |
| `sql.Token.has_ancestor` | 2 issues (NameError + contract mismatch) | 1 issue (NameError only) |
| `sql.TokenList.flatten` | 2 issues, including **high-severity cross-file breakage** naming `__str__` and `get_token_at_offset` as broken callers | 1 issue (unrelated local bug, no mention of broken callers) |

## Key finding

On `flatten`, the diff-only baseline missed the return-type change entirely --
it flagged a different, lower-severity local issue instead. Only the
context-aware version, using the dependency graph to see `flatten`'s real
callers, correctly identified that the change breaks `__str__` and
`get_token_at_offset`. This is the core failure mode context-aware review
is designed to catch: a change that looks safe in isolation but breaks
something elsewhere.

On the self-contained `NameError` bug, both approaches caught the core
issue -- confirming context-aware review doesn't sacrifice basic
detection to gain cross-file awareness.

## Caveats (worth stating honestly)

- Sample size is small (3 changes, 1 repo) -- a real limitation, not hidden.
- Diff-only still catches real, valid issues (not false positives) --
  it's not "wrong," just blind to a specific category of cross-file risk.
- No formal false-positive rate measured; all issues reported above were
  manually reviewed and judged genuine, not fabricated.
