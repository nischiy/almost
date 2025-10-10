
# Relocator v2 (README & scripts)

## Що робить
- Переносить **усі README*/PATCH*** файли з кореня у `docs/readmes/`.
- Переносить **усі .ps1** у `scripts/<bucket>/` за евристикою:
  - **tests** → `scripts/tests`
  - **maintenance/clean/organize** → `scripts/maintenance`
  - **release/make/archive/pack** → `scripts/release`
  - **diagnostics/diag/verify/list/find** → `scripts/diagnostics`
  - інакше → `scripts/migrated_root`
- Після виконання корінь **чистий** від README та `.ps1`.
- Є режим **-WhatIf** для попереднього перегляду.

## Команди
```powershell
cd G:\Bot\almost

# Сухий прогон
powershell -ExecutionPolicy Bypass -File .\scripts\maintenance\relocate_docs_and_scripts.ps1 -ProjectRoot . -WhatIf

# Виконати переміщення
powershell -ExecutionPolicy Bypass -File .\scripts\maintenance\relocate_docs_and_scripts.ps1 -ProjectRoot .
```
