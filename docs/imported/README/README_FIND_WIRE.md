
# Find & Wire Existing .env Parser (Minimal, No Duplicates)

## 1) Знайди твій існуючий парсер `.env`
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\find_env_parser.ps1
```
Подивись Top candidates і вибери потрібний модуль/файл.

## 2) Підключи його до пре-флайту (без дублювання)
Припустимо, у вибраному файлі є функція `load_env()` і python-імпортний шлях `myproj.config.env_loader`.
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\wire_preflight_env_parser.ps1 `
  -ImportPath "myproj.config.env_loader" `
  -FunctionName "load_env"
```

Скрипт підмінить імпорт у `tools/preflight/preflight_all.py`, і **preflight** почне використовувати твій парсер.

## 3) Запусти preflight
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preflight_all.ps1
```

> Ніяких дублікатів логіки: ми просто “підшиваємо” preflight до твоєї реалізації.
