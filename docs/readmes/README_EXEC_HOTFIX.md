
# Executor docstring hotfix — UA/EN

## 🇺🇦 Що робить
Виправляє артефакт `"""` у `app\services\execution.py` (SyntaxError). Замінює на звичайні `"""` та зберігає файл.

## ▶️ Команди
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\fix_executor_docstring.ps1 -ProjectRoot .
# Потім:
powershell -ExecutionPolicy Bypass -File .\scripts\tests\run_pytest.ps1
```
