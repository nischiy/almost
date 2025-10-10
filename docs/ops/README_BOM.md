# Крок 2: Прибирання UTF-8 BOM + захист у майбутньому

## Варіант A — Git hooks (без зовнішніх залежностей)
1) Скопіюйте `.githooks/pre-commit` у корінь репозиторію.
2) Увімкніть директорію хуків:
   ```bash
   git config core.hooksPath .githooks
   ```
3) Перевірка спрацює автоматично під час `git commit`.
   - Щоб перевірити вручну:  
     ```powershell
     scripts\maintenance\strip_bom.ps1 -Check
     ```
   - Щоб виправити всі знайдені:  
     ```powershell
     scripts\maintenance\strip_bom.ps1 -Write
     ```

## Варіант B — pre-commit framework
1) Встановіть пакет:
   ```powershell
   pip install pre-commit
   ```
2) Додайте `.pre-commit-config.yaml` у корінь (із цього архіву).
3) Активуйте:
   ```powershell
   pre-commit install
   pre-commit run --all-files
   ```

## Скрипти
- `scripts/maintenance/strip_bom.py` — детектор/ремувер BOM.
- `scripts/maintenance/strip_bom.ps1` — обгортка для Windows PowerShell.
- `.githooks/pre-commit` — Bash-хук для Git (Windows Git Bash підтримується).

## Очікуваний результат
- Після одноразового `-Write` у репозиторії не лишається `.py` з BOM.
- Хук блокує повернення BOM у майбутніх комітах.
