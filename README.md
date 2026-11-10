# Шум-Удавы

Браузерная игра (уровень «Офис»). Готовая статическая сборка лежит в `docs/` — её достаточно
выложить на любой хостинг (GitHub Pages: Settings → Pages → Deploy from a branch → папка `/docs`).

- `docs/` — игра: `index.html`, арт, звуки (`docs/audio`, источники и лицензия — `docs/audio/CREDITS.md`).
- `tools/vendor/` — исходная тестовая сборка (proto14), от которой сделана игра.
- `tools/build_sounds.py` — собирает звуки из записей CC0.
- `tools/patch_bundle.py` + `tools/fx.css` + `docs/assets/fx.js` — новые звуки и недостающие анимации поверх сборки.

Пересборка: `python3 tools/build_sounds.py && python3 tools/patch_bundle.py`.
Локальный запуск: `python3 -m http.server -d docs 8000`.
