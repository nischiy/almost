This hotfix ensures `from __future__ import annotations` stays at the very top
(after optional encoding line and docstring) in `tests/test_pipeline_end_to_end.py`,
and only then adds pytest markers for `slow` and `integration`.
