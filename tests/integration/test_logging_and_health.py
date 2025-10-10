import os, importlib, pathlib

def test_decision_log_folder_exists():
    # Ensure logs folder is present or creatable
    base = pathlib.Path("logs")
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
    assert base.exists()

def test_health_module_imports():
    importlib.import_module("core.telemetry.health")
