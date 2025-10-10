README_TESTS_PHASE_A.md
================================
Phase A test suite:
- Fully offline (stubs network).
- Lightly exercises key modules to expose import/logic errors without long runs.
- Fails only when a module is truly broken; otherwise skips gracefully.

Run:
    pytest -q -vv
