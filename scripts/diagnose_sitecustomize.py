
# scripts/diagnose_sitecustomize.py
import sys, importlib, os
def main():
    sc = sys.modules.get("sitecustomize")
    if sc is None:
        try:
            importlib.import_module("sitecustomize")
            sc = sys.modules.get("sitecustomize")
        except Exception as e:
            print("sitecustomize not importable:", e)
            return
    path = getattr(sc, "__file__", "<unknown>")
    print("Active sitecustomize:", path)
    wrapped = getattr(sc, "WRAPPED_FUNCS", None)
    if wrapped:
        print("Wrapped functions:")
        for w in wrapped:
            print(" -", w)
    else:
        print("No wrapped functions recorded.")
if __name__ == "__main__":
    main()
