---
name: portada-reels
description: Diseña portadas (covers) para reels de Instagram/TikTok en formato 1080x1920 con el estilo editorial "serif pequeña + palabra gigante": Georgia Pro para la frase de entrada y Owners (sans ancha y negra, en mayúsculas) para la palabra clave. Úsalo siempre que se pida una portada, cover, miniatura o thumbnail para un reel o video vertical, "pon el título sobre esta foto", "saca un frame del video para la portada", o se comparta una imagen o video y se pida titularlo en este estilo — aunque no se nombren las fuentes.
---

# Portada de reels — Georgia Pro + Owners

Crea la portada de un reel a partir de **una imagen** que comparta la persona o de **un frame** sacado del video original, y le pone el título con la combinación Georgia Pro + Owners.

## El estilo (lo que hay que reproducir)

Referencias: "combina estas / TIPOGRAFÍAS … para / tus reels" y "Georgia / OWNERS".

- **Frase de entrada** en Georgia Pro Regular, minúsculas o tipo oración, tamaño chico (≈ 6–7 % del ancho). Ej.: `combina estas`, `para`, `cómo`.
- **Palabra clave** en Owners Black/Wide, **MAYÚSCULAS**, enorme, casi de lado a lado (hasta ~88 % del ancho), tracking apretado. Ej.: `TIPOGRAFÍAS`, `OWNERS`.
- Variante para cerrar: una frase grande en Georgia Pro (`serif-xl`), minúsculas, ej. `tus reels`.
- Todo **blanco**, centrado, con una **sombra suave** para que se lea sobre fondos claros. Sin cajas, sin colores extra.
- La entrada va **pegada** encima de la palabra grande: forman un solo bloque.
- El bloque principal va en el **tercio superior** (≈ 15 % desde arriba), encima de la cabeza; el rostro queda libre.
- Opcional: un segundo bloque más abajo (≈ 55–60 %), sobre el torso, nunca sobre la cara.
- Máximo 2 bloques y ~6 palabras en total. Si el título es largo, quedarse con la idea y la palabra fuerte.

## Flujo

### 1. Fondo

**Si comparten una imagen:** usarla directo.

**Si comparten un video:** extraer candidatos y elegir mirando la hoja de contactos.

```bash
python3 .claude/skills/portada-reels/scripts/portada.py frames VIDEO.mp4 --n 12 --out frames/
```

Abre `frames/contact_sheet.jpg` con Read y elige el frame donde la persona:
mira a cámara, tiene ojos abiertos y boca cerrada o neutra, manos quietas (no movidas), y hay espacio libre arriba de la cabeza para el título. La marca `*` indica el más nítido, pero manda el criterio visual. Si ningún frame sirve, vuelve a correr con `--max-pos 1` o más `--n`.

### 2. Título

Si la persona no dio el texto exacto, propone 2–3 opciones con la estructura **entrada corta + palabra clave** y elige la más fuerte (o pregunta si no es obvio). La palabra clave es el sustantivo/promesa del reel, no un conector.

### 3. Render

```bash
python3 .claude/skills/portada-reels/scripts/portada.py render \
  --input frames/frame_05.jpg \
  --line "serif|combina estas" \
  --line "bold|tipografías" \
  --line "break|0.57" \
  --line "serif|para|left" \
  --line "serif-xl|tus reels" \
  --guides --out portada.png
```

Sintaxis de `--line` (en orden de arriba a abajo):

| Línea | Qué hace |
|---|---|
| `serif\|texto` | Georgia Pro chica (frase de entrada) |
| `bold\|texto` | Owners en mayúsculas, gigante |
| `serif-xl\|texto` | Georgia Pro grande (cierre) |
| `...\|texto\|left` o `\|right` | alinea esa línea al borde del bloque (por defecto centrada) |
| `break\|0.57` | empieza un nuevo bloque a esa altura (fracción del alto) |
| `...\|texto\|\|#C6963C` | color de esa línea (4.º campo; el 3.º es la alineación, puede ir vacío) |

Con un video se puede pasar el video directo: `--input VIDEO.mp4 --time 3.2`.

Ajustes útiles:
- `--y 0.15` altura del primer bloque. Bajar si la cabeza está muy abajo; subir si tapa la frente.
- `--scale 0.9` achica todo el texto.
- `--focus-y 0.35` mueve el recorte vertical cuando la foto no es 9:16.
- `--scrim 0.35` oscurece suavemente la parte de arriba si el fondo es muy claro; `--darken 0.15` oscurece toda la foto.
- `--shadow 0.6` sombra más marcada (0 la quita).
- `--overlay-color "#1A1614" --darken 0.45` capa de color translúcida sobre toda la foto.
- `--depth` pone a la persona **delante** del título (como en "TIPOGRAFÍAS", donde la cabeza tapa parte de la palabra). Necesita `pip install rembg`; si no está o falla, el script sigue sin el efecto.

### 4. Revisar antes de entregar

Abre `portada.png` y `portada_guias.png` con Read y revisa:
- El título está **dentro del rectángulo rojo** (recorte 3:4 de la grilla del perfil) y fuera de la franja amarilla (zona de la interfaz abajo).
- El texto no tapa ojos ni boca.
- Se lee bien; si el fondo es claro, sube `--shadow` o usa `--scrim`.
- Las tildes de mayúsculas (Í, Á, Ó) se ven completas.

Itera hasta que se vea como las referencias y entrega `portada.png` (1080×1920) con SendUserFile.

## Paleta de marca (vigente)

| Color | HEX | Uso en portada |
|---|---|---|
| Crema lima | `#ECFEB2` | palabra clave en Owners sobre foto oscurecida (color de firma) |
| Marfil | `#F5EDE0` | texto serif sobre foto oscurecida |
| Cobalto | `#1E3FA0` | títulos sobre fondos claros (crema lima o marfil) |
| Frambuesa | `#9C2F5A` | acento sobre fondos claros |
| Cálido negro | `#1A1614` | capa translúcida sobre la foto (en vez de negro puro) |

Cobalto y Frambuesa son oscuros: sobre una foto oscurecida no se leen, úsalos solo sobre fondos claros. Evita la capa en Cobalto sobre fotos con personas: tiñe la piel.

Receta probada sobre foto: capa Cálido negro al 45 %, serif en Marfil y palabra Owners en Crema lima:

```bash
--darken 0.45 --overlay-color "#1A1614" \
--line "serif|no seguía mi cuenta, pero||#F5EDE0" --line "bold|me leía||#ECFEB2"
```

## Fuentes

Georgia Pro y Owners son fuentes con licencia y **no vienen en el repo**. El script las busca en `.claude/skills/portada-reels/fonts/`, en las carpetas de fuentes del sistema, o en las rutas de `--serif-font` / `--bold-font` (o las variables `REEL_SERIF_FONT` / `REEL_BOLD_FONT`). Ver `fonts/README.md`.

Si no las encuentra usa respaldos libres parecidos (Gelasio ≈ Georgia, Archivo Expanded Black ≈ Owners) y lo avisa en consola. En ese caso **dile a la persona** que la portada usa fuentes de respaldo y que, para el resultado final, suba sus archivos de Georgia Pro y Owners a `fonts/`.
