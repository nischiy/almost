
from pathlib import Path

def main():
    cwd = Path.cwd()
    repo_root = Path(__file__).resolve().parents[1] if (Path(__file__).parents) else cwd
    print("[env-diag] Current dir      :", cwd)
    print("[env-diag] .env here?       :", (cwd/".env").exists())
    print("[env-diag] .env.example here:", (cwd/".env.example").exists())
    print("[env-diag] Files here (.env*):", [p.name for p in cwd.glob(".env*")])
    print()
    print("[env-diag] Repo root (guess):", repo_root)
    print("[env-diag] .env at root?    :", (repo_root/".env").exists())
    print("[env-diag] .env.example root:", (repo_root/".env.example").exists())
    print("[env-diag] Files root (.env*):", [p.name for p in repo_root.glob(".env*")])

if __name__ == "__main__":
    main()
