1) Prompt for Writing New Code (optimize CSA, ID, BPS)
Prompt:

You are writing Python code that will be analyzed using three metrics:

CSA (complexity / symbol usage),

ID (indirection depth / call graph complexity),

BPS (branching/condition penalty; complex conditions reduce the score).

Write code that optimizes all three metrics:

Keep functions small, single-purpose, and avoid deep call chains (low ID).

Minimize external symbol usage and keep dependencies localized (low CSA).

Keep if conditions simple; avoid chained boolean logic and function calls inside conditions (high BPS).

Precompute values before conditionals, and use helper functions to isolate logic.

Prefer clear, flat control flow (early returns) over nested branches.

Produce clean, readable, and maintainable code that adheres to these constraints.




2) Prompt for Refactoring Existing Code (improve CSA, ID, BPS)
Prompt:

You are refactoring existing Python code to improve CSA, ID, and BPS metrics:

CSA improves by reducing external symbol usage and simplifying symbol dependencies.

ID improves by shortening call chains and reducing indirection depth.

BPS improves by simplifying conditional expressions and removing calls inside conditions.

Refactor the code while preserving behavior:

Extract complex condition logic into small helpers and precompute values outside if statements.

Split large functions into smaller ones only if it does not create deeper call chains.

Reduce dependency on external symbols by localizing logic and data.

Flatten control flow and avoid unnecessary layers of abstraction.

Keep the output behavior identical, add tests only when needed, and explain how the changes improve CSA, ID, and BPS.