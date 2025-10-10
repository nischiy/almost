import importlib

def test_app_services_aux_modules_import():
    modules = [
        "app.services.notifications",
        "app.services.order_adapter",
        "app.services.order_service",
        "app.services.exit_adapter",
    ]
    for m in modules:
        importlib.import_module(m)
