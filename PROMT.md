You are a refactoring agent for a Python static-analysis tool.

I will provide:
1) A report JSON (schema_version 1.0) produced by the tool.
2) The tool’s repository is available locally.

The JSON must be treated as an observation of the tool’s current behavior, not something to edit or fix directly.

Goal
Improve the tool so that future reports have lower noise and higher semantic accuracy, while keeping the exact same JSON schema (same keys, same types).

What to do
- Use the JSON only to understand how the tool currently behaves.
- Identify weaknesses in the analysis logic (signal inflation, missing resolution, overly generic symbol tracking).
- Modify the tool code to address those weaknesses.
- Do not add new features unrelated to the reported metrics.
- Do not change the report schema or naming.

Required analysis improvements
- `unresolved_calls` must not include Python builtins (derive the builtin set dynamically from the `builtins` module).
- `csa_main` must not be incremented by builtins; optionally also ignore standard-library symbols (e.g. ast, os, sys, json, argparse, logging).
- Improve call-graph resolution for indirection metrics at least for:
  - calls to functions defined in the same module
  - calls of the form `self.foo()` where `foo` is defined in the same class

Constraints
- The analyzed project is unknown and must not be special-cased.
- The JSON is assumed to be structurally correct and semantically valid for the current implementation.
- Changes must affect how the tool computes metrics, not how results are post-processed.

Wait for the JSON, then start.
