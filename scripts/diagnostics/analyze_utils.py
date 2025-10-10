#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyze 'utils' modules: usage, stubs, overlap, recommendation.
Usage:
    python scripts/diagnostics/analyze_utils.py --root . [--utils utils]
"""
import argparse, os, re, ast, hashlib, json, textwrap, sys
from collections import Counter, defaultdict
from datetime import datetime

def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            b = f.read(65536)
            if not b: break
            h.update(b)
    return h.hexdigest()

def read(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def list_py(root):
    out = []
    for dp,_,files in os.walk(root):
        if ".venv" in dp or dp.endswith(os.sep+"tests"): 
            continue
        for fn in files:
            if fn.endswith(".py"):
                out.append(os.path.join(dp, fn))
    return out

def public_symbols(tree: ast.AST):
    funcs, clss = [], []
    for n in tree.body if hasattr(tree,"body") else []:
        if isinstance(n, ast.FunctionDef) and not n.name.startswith("_"):
            funcs.append(n.name)
        if isinstance(n, ast.ClassDef) and not n.name.startswith("_"):
            clss.append(n.name)
    return funcs, clss

def is_stub_node(node):
    # function/class body consists only of 'pass' or Ellipsis
    body = getattr(node, "body", [])
    if not body: 
        return True
    for stmt in body:
        if isinstance(stmt, ast.Pass): 
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value in (Ellipsis, "..."):
            continue
        # anything else means not stub
        return False
    return True

def file_loc_stats(text):
    lines = text.splitlines()
    total = len(lines)
    blank = sum(1 for l in lines if l.strip()== "")
    comments = sum(1 for l in lines if l.strip().startswith("#"))
    return dict(total=total, blank=blank, comments=comments)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--utils", default="utils")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    utils_dir = os.path.join(root, args.utils)
    if not os.path.isdir(utils_dir):
        print(f"[ERR] Utils dir not found: {utils_dir}", file=sys.stderr)
        return 2

    # Baseline names existing in app/core that could overlap
    overlap_dirs = [os.path.join(root, "core"), os.path.join(root, "app")]
    overlap_names = set()
    for od in overlap_dirs:
        for dp,_,files in os.walk(od):
            for fn in files:
                if fn.endswith(".py"):
                    overlap_names.add(os.path.splitext(fn)[0])

    # collect usage across repo
    py_files = list_py(root)
    usage_counter = Counter()
    for p in py_files:
        t = read(p)
        # from utils import name
        m1 = re.findall(r"(?m)^\s*from\s+utils\s+import\s+([A-Za-z0-9_,\s]+)", t)
        for grp in m1:
            for name in re.split(r"[, ]+", grp.strip()):
                if name: usage_counter[name]+=1
        # import utils.name  OR  utils.name usage
        m2 = re.findall(r"\butils\.([A-Za-z_][A-Za-z0-9_]*)\b", t)
        for name in m2:
            usage_counter[name]+=1

    # analyze each utils module
    rows = []
    for fn in sorted(os.listdir(utils_dir)):
        if not fn.endswith(".py"): 
            continue
        path = os.path.join(utils_dir, fn)
        name = os.path.splitext(fn)[0]
        text = read(path)
        loc = file_loc_stats(text)
        try:
            tree = ast.parse(text)
            funcs, clss = public_symbols(tree)
            stubs = []
            for n in tree.body:
                if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and not n.name.startswith("_"):
                    if is_stub_node(n):
                        stubs.append(n.name)
        except SyntaxError:
            funcs, clss, stubs = [], [], []

        usage = usage_counter.get(name, 0)
        overlap = name in overlap_names and name not in ("__init__",)

        # crude recommendation heuristic
        if usage == 0 and overlap:
            rec = "REMOVE (duplicate name; not referenced)"
        elif usage == 0:
            rec = "REVIEW (unused)"
        elif usage > 0 and overlap:
            rec = "MOVE (merge with existing module)"
        else:
            rec = "KEEP"

        rows.append(dict(
            module=name, path=os.path.relpath(path, root),
            sha1=sha1(path), usage=usage, overlap=overlap,
            public_funcs=",".join(funcs) if funcs else "",
            public_classes=",".join(clss) if clss else "",
            stubs=",".join(stubs) if stubs else "",
            loc_total=loc["total"], loc_blank=loc["blank"], loc_comments=loc["comments"],
            recommendation=rec
        ))

    # write markdown report
    docs_dir = os.path.join(root, "docs", "readmes")
    os.makedirs(docs_dir, exist_ok=True)
    md_path = os.path.join(docs_dir, "UTILS_AUDIT.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Utils Audit ({datetime.utcnow().isoformat()}Z)\n\n")
        f.write("| module | usage | overlap | public_funcs | public_classes | stubs | loc | comments | recommendation |\n")
        f.write("|---|---:|:---:|---|---|---|---:|---:|---|\n")
        for r in rows:
            f.write("|{module}|{usage}|{overlap}|{public_funcs}|{public_classes}|{stubs}|{loc_total}|{loc_comments}|{recommendation}|\n".format(**r))
        f.write("\n> overlap = модуль з такою ж назвою вже існує у `core/` або `app/`.\n")

    # print concise console table (TSV)
    print("module\tusage\toverlap\tloc\trecommendation\tpath")
    for r in rows:
        print(f"{r['module']}\t{r['usage']}\t{r['overlap']}\t{r['loc_total']}\t{r['recommendation']}\t{r['path']}")

    # JSON for tooling
    json_path = os.path.join(docs_dir, "UTILS_AUDIT.json")
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(rows, jf, ensure_ascii=False, indent=2)

    print(f"\n[REPORT] {md_path}")
    print(f"[JSON]   {json_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
