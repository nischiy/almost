
==============================
WITHOUTTRAH QUICK PATCH BUNDLE
==============================

Що всередині
------------
- scripts/patch_project.py  — безпечний патчер. Акуратно виправляє проблеми з тестів:
    * повертає фікстури root/internet/dummy_params у tests/conftest.py (якщо їх нема);
    * виправляє .env.example — додає відсутні ключі;
    * коментує багаторядковий self.log.info(... "Decision" ...) у app/run.py, щоб прибрати IndentationError;
    * вимикає поламані скрипти (apply_patches_round2.py, fix_failures_round3.py) шляхом перейменування у .bak;
    * обеззброює *.bak*.py у app/, щоб pytest не імпортував бекапи.

Як застосувати
--------------
1) Розпакуйте ZIP прямо в корінь проєкту (там, де папки app/, core/, tests/, scripts/).
   Має з'явитися файл: scripts/patch_project.py

2) Запустіть патч:
     (.venv) PS> python scripts\patch_project.py

3) Перевірте тести:
     (.venv) PS> pytest -s tests

Скрипт ідемпотентний — його можна запускати повторно; він нічого не "ламає", лише виправляє.
