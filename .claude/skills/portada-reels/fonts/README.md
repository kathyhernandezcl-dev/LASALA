# Fuentes

Copia aquí tus archivos `.ttf` / `.otf` con licencia:

- **Georgia Pro Regular** — p. ej. `GeorgiaPro-Regular.ttf` (viene con Microsoft 365).
- **Owners** — de preferencia `OwnersXWide-Black.otf`, `OwnersWide-Black.otf` u `Owners-Black.otf` (Adobe Fonts / Ohno Type).

El script elige automáticamente por nombre de archivo, en este orden:
Owners XWide Black → Wide Black → Black → Bold.

Si prefieres no subirlas al repo, pasa la ruta con `--serif-font` / `--bold-font`
o con las variables `REEL_SERIF_FONT` / `REEL_BOLD_FONT`.

## Respaldos incluidos (`fallback/`)

Se usan solo si no se encuentran las fuentes reales. Ambas tienen licencia
SIL Open Font License 1.1 (ver `fallback/OFL.txt`):

- `Gelasio-Regular.ttf`, `Gelasio-Italic.ttf` — Gelasio, diseñada con las métricas de Georgia.
- `ArchivoExpanded-Black.ttf` — Archivo, instancia estática ancho 125 / peso 900.
