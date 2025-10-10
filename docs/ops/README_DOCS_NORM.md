# Крок 4: Нормалізація документації в `docs/`

## Що робить скрипт
`scripts/maintenance/normalize_docs.ps1`:
- Знаходить всі `*.md` (і `*.txt`, якщо не вимкнуто) у коренях: `app/`, `core/`, `ml/`, `scripts/`, `tools/`, `tests/`, `README/`, `reports/`, `config/`.
- Переміщує їх у `docs/` за правилами:
  - `README/...` → `docs/readmes/...`
  - `reports/...` → `docs/reports/...`
  - інші шляхи → `docs/imported/<оригінальний шлях>`
- Перед переміщенням **копіює** оригінал у бекап `_normalize_docs_backup_YYYYMMDD_HHMMSS/`.
- Генерує `docs/INDEX.md` (список файлів + розбивка по підтеках).

## Запуск
```powershell
cd G:\Bot\almost
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\maintenance\normalize_docs.ps1 -DryRun   # перегляд плану
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\maintenance\normalize_docs.ps1           # застосувати
```

## Перевірка
```powershell
Get-ChildItem docs -Recurse -File -Include *.md,*.txt | Measure-Object
Get-Content docs\INDEX.md -TotalCount 50
```

## Ролбек
У каталозі `_normalize_docs_backup_*` є копії всіх переміщених файлів. Щоб повернути файл — скопіюйте його назад у початкову локацію.
