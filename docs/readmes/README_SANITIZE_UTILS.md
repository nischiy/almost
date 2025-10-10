
# Sanitize `utils`

## Що робить
- `sanitize_utils.ps1` переносить **не-Python** файли з `utils/` у правильні місця:
  - `*.ps1` → `scripts/release/`
  - `*NOTE*.txt`, `*PATCH*.txt`, `*.md`, `*README*` → `docs/readmes/`
- `list_unused_utils.ps1` показує файли `utils/*.py`, які **ніде не імпортуються** (нічого не видаляє).

## Команди
```powershell
cd G:\Bot\almost

# 1) Прибрати сміття з utils (якщо твій шлях інший, додай -UtilsRel "app\utils")
powershell -ExecutionPolicy Bypass -File .\scripts\maintenance\sanitize_utils.ps1 -ProjectRoot .

# 2) Продіагностувати невикористані модулі в utils
powershell -ExecutionPolicy Bypass -File .\scripts\diagnostics\list_unused_utils.ps1 -ProjectRoot .
```
