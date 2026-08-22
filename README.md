ContextGuard is an AI-powered code review assistant that reasons about changes using their surrounding context, not just the visible diff. Instead of only checking the lines that changed, it maps a change's dependencies across the codebase, retrieves the most relevant related code, and uses an LLM to flag real, cross-file risks a diff-only review would miss. Built for the KPIT Sparkle 2027 "AI-Driven Contextual Reasoning for Software Engineering" track, targeting safety-critical/embedded software workflows where an isolated-looking change can silently break something elsewhere. Currently in active development — Phase 1 (automatic diff-to-function mapping) is complete.

## How change-detection works (Phase 1)
Before ContextGuard can reason about a code change, it first needs to know,
precisely, what changed. This is handled in three steps:
Reading the diff (`day9_diff_to_functions.py`) — runs `git diff -U0`
and parses its unified-diff hunk headers to get the exact line numbers
that changed in each modified file, using the new (current) version's
line numbers.
Understanding the file's structure (`day8_function_calls.py`) —
parses each changed file into an abstract syntax tree (AST) rather than
treating it as plain text. This finds every function definition, its
parameters, its line range (start and end), and which other functions
it calls.
Mapping lines to functions (`Function.contains_line()` in
`day3_function_class.py`) — for each changed line, checks which
function's start/end line range contains it, so the tool can say
precisely which function(s) a change actually touched.
The result: given any uncommitted change in a repository, ContextGuard can
answer "which function(s) did this touch?" automatically, with no manual
input -- the foundation everything else in the project builds on.
Known current limitations (to be addressed in later phases):
Calls to built-in functions or external libraries aren't yet
distinguished from calls to functions defined in the same codebase.
Only single-file, same-repository changes are analyzed; cross-file
dependency resolution comes in the next phase.
