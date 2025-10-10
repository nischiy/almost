
# Move stray READMEs

Переносить усі README/PATCH/NOTE-файли з **кореня** в `docs/readmes/`.
Модульні README в підпапках не чіпає.

## Запуск
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\maintenance\move_stray_readmes.ps1 -ProjectRoot .
```
