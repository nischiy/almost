# make_support_bundle.ps1

Створює **мінімальний архів** із файлами, які мені потрібні для аналізу коду:
- `main.py`
- `requirements*.txt`
- `.env.example` (НЕ `.env`)
- вся Python-логіка з `app/**` та `core/**`
- `docs/readmes/*.md`
- `scripts/tests/run_pytest.ps1`
- (опційно) `tests/**` якщо вказати `-IncludeTests`

Архів кладеться до **батьківської папки** (для `G:\Bot\almost` це `G:\Bot`).

## Використання
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\make_support_bundle.ps1
# або
powershell -ExecutionPolicy Bypass -File .\make_support_bundle.ps1 -IncludeTests
powershell -ExecutionPolicy Bypass -File .\make_support_bundle.ps1 -WhatIf
```
