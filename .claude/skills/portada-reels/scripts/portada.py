#!/usr/bin/env python3
"""Portadas de reels: frame de video o imagen + título Georgia Pro / Owners.

Subcomandos:
  frames  VIDEO            extrae frames candidatos + hoja de contactos
  render  --input IMG|VID  compone la portada 1080x1920

Ejemplo:
  python3 portada.py render --input foto.jpg \
      --line "serif|combina estas" --line "bold|tipografías" \
      --line "break|0.56" --line "serif|para|left" --line "serif-xl|tus reels" \
      --out portada.png
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat

W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.normpath(os.path.join(HERE, "..", "fonts"))

# Orden de búsqueda: fuente real primero, luego respaldos libres incluidos.
FONT_CANDIDATES = {
    "serif": [
        "GeorgiaPro-Regular.*", "Georgia Pro Regular.*", "GeorgiaPro*Regular*.*",
        "georgiapro*regular*.*", "Georgia.ttf", "georgia.ttf",
        "fallback/Gelasio-Regular.ttf",
    ],
    "bold": [
        "OwnersXWide-Black.*", "Owners XWide Black.*", "OwnersWide-Black.*",
        "Owners Wide Black.*", "Owners-Black.*", "Owners Black.*",
        "OwnersXWide-Bold.*", "OwnersWide-Bold.*", "Owners-Bold.*",
        "Owners*Black*.*", "Owners*Bold*.*", "owners*.*",
        "fallback/ArchivoExpanded-Black.ttf",
    ],
}
SYSTEM_FONT_DIRS = [
    FONTS_DIR,
    os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "/System/Library/Fonts",
    os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts"),
    "/usr/share/fonts", "/usr/local/share/fonts", "C:/Windows/Fonts",
]
FONT_EXT = (".ttf", ".otf", ".ttc")


def find_font(kind, override=None):
    env = os.environ.get("REEL_SERIF_FONT" if kind == "serif" else "REEL_BOLD_FONT")
    for p in (override, env):
        if p:
            if not os.path.isfile(p):
                sys.exit(f"No existe la fuente: {p}")
            return p
    for pattern in FONT_CANDIDATES[kind]:
        for d in SYSTEM_FONT_DIRS:
            if not os.path.isdir(d):
                continue
            hits = [h for h in glob.glob(os.path.join(d, "**", pattern), recursive=True)
                    if h.lower().endswith(FONT_EXT)]
            if hits:
                return sorted(hits)[0]
    sys.exit(f"No encontré fuente para '{kind}'.")


# ---------------------------------------------------------------- frames

def probe_duration(video):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", video], capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        sys.exit(f"No pude leer la duración de {video}")


def grab_frame(video, t, out_path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", video,
                    "-frames:v", "1", "-q:v", "2", out_path], check=True)
    return out_path


def sharpness(img):
    g = ImageOps.grayscale(img)
    g.thumbnail((360, 640))
    edges = g.filter(ImageFilter.FIND_EDGES)
    return ImageStat.Stat(edges).var[0]


def cmd_frames(a):
    os.makedirs(a.out, exist_ok=True)
    dur = probe_duration(a.video)
    start, end = dur * 0.03, dur * a.max_pos
    n = max(2, a.n)
    rows = []
    for i in range(n):
        t = start + (end - start) * i / (n - 1)
        p = grab_frame(a.video, t, os.path.join(a.out, f"frame_{i:02d}.jpg"))
        img = Image.open(p).convert("RGB")
        rows.append({"idx": i, "time": round(t, 2), "path": p, "sharpness": round(sharpness(img), 1)})
    best = max(rows, key=lambda r: r["sharpness"])
    # Hoja de contactos para elegir a ojo (mirada a cámara, ojos abiertos, boca cerrada).
    cols = 4
    tw, th = 270, 480
    sheet = Image.new("RGB", (cols * tw, ((n + cols - 1) // cols) * th), "black")
    d = ImageDraw.Draw(sheet)
    label_font = ImageFont.truetype(find_font("bold"), 26)
    for r in rows:
        im = ImageOps.fit(Image.open(r["path"]).convert("RGB"), (tw, th))
        x, y = (r["idx"] % cols) * tw, (r["idx"] // cols) * th
        sheet.paste(im, (x, y))
        tag = f"{r['idx']}  {r['time']}s" + ("  *" if r is best else "")
        d.rectangle([x, y, x + tw, y + 40], fill=(0, 0, 0))
        d.text((x + 10, y + 6), tag, font=label_font, fill="white")
    sheet_path = os.path.join(a.out, "contact_sheet.jpg")
    sheet.save(sheet_path, quality=88)
    with open(os.path.join(a.out, "frames.json"), "w") as f:
        json.dump({"duration": dur, "frames": rows, "sharpest": best["idx"]}, f, indent=2)
    print(f"Hoja de contactos: {sheet_path}")
    print(f"Más nítido: #{best['idx']} ({best['time']}s) -> {best['path']}")
    for r in rows:
        print(f"  #{r['idx']:02d} t={r['time']:>6}s nitidez={r['sharpness']}")


# ---------------------------------------------------------------- texto

def tracked_width(font, text, tracking):
    return font.getlength(text) + tracking * max(0, len(text) - 1)


def render_line(text, font, tracking, color):
    """Devuelve una capa RGBA recortada a la tinta del texto."""
    asc, desc = font.getmetrics()
    pad = int(font.size * 0.4)
    w = int(tracked_width(font, text, tracking)) + 2 * pad
    h = asc + desc + 2 * pad
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if tracking == 0:
        d.text((pad, pad), text, font=font, fill=color)
    else:
        for i, ch in enumerate(text):
            x = pad + font.getlength(text[:i]) + tracking * i
            d.text((x, pad), ch, font=font, fill=color)
    bbox = layer.getbbox()
    return layer.crop(bbox) if bbox else layer


STYLES = {
    # tamaño (fracción del ancho), ancho máximo (fracción), tracking (em), mayúsculas
    "serif":    dict(font="serif", size=0.068, max_w=0.86, track=0.0,   upper=False),
    "serif-xl": dict(font="serif", size=0.170, max_w=0.86, track=-0.01, upper=False),
    "bold":     dict(font="bold",  size=0.150, max_w=0.88, track=-0.02, upper=True),
}


def make_line(style, text, fonts, scale, color):
    st = STYLES[style]
    if st["upper"]:
        text = text.upper()
    size = int(W * st["size"] * scale)
    max_w = W * st["max_w"]
    while True:
        font = ImageFont.truetype(fonts[st["font"]], size)
        track = st["track"] * size
        if tracked_width(font, text, track) <= max_w or size <= 20:
            break
        size = int(size * 0.97)
    return render_line(text, font, track, color)


def parse_lines(raw):
    """'style|texto|align'  o  'break|0.58' para empezar otro bloque a esa altura."""
    blocks = [{"y": None, "lines": []}]
    for item in raw:
        parts = item.split("|")
        style = parts[0].strip()
        if style == "break":
            blocks.append({"y": float(parts[1]), "lines": []})
            continue
        if style not in STYLES:
            sys.exit(f"Estilo desconocido '{style}'. Usa: {', '.join(STYLES)} o break")
        text = parts[1] if len(parts) > 1 else ""
        align = parts[2].strip() if len(parts) > 2 else "center"
        blocks[-1]["lines"].append((style, text, align))
    return [b for b in blocks if b["lines"]]


def compose_block(lines, fonts, scale, color, gap):
    layers = [(make_line(s, t, fonts, scale, color), a) for s, t, a in lines]
    bw = max(l.width for l, _ in layers)
    bh = sum(l.height for l, _ in layers) + gap * (len(layers) - 1)
    block = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    y = 0
    for l, align in layers:
        x = {"left": 0, "right": bw - l.width}.get(align, (bw - l.width) // 2)
        block.alpha_composite(l, (x, y))
        y += l.height + gap
    return block


def add_shadow(text_layer, strength):
    if strength <= 0:
        return text_layer
    alpha = text_layer.getchannel("A")
    sh = Image.new("RGBA", text_layer.size, (0, 0, 0, 0))
    sh.putalpha(alpha.point(lambda v: int(v * strength)))
    sh = sh.filter(ImageFilter.GaussianBlur(W * 0.012))
    out = Image.new("RGBA", text_layer.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, int(W * 0.004)))
    out.alpha_composite(text_layer)
    return out


def top_scrim(img, amount):
    if amount <= 0:
        return img
    grad = Image.linear_gradient("L").resize((W, H))  # 0 arriba -> 255 abajo
    grad = grad.point(lambda v: int(255 * amount * max(0, 1 - v / 255 / 0.55)))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    black.putalpha(grad)
    out = img.copy()
    out.alpha_composite(black)
    return out


def person_mask(img):
    try:
        from rembg import remove
    except Exception:
        print("Aviso: --depth necesita 'pip install rembg'; sigo sin efecto de profundidad.")
        return None
    try:
        return remove(img.convert("RGB"), only_mask=True).convert("L")
    except Exception as e:
        print(f"Aviso: falló la segmentación ({e}); sigo sin efecto de profundidad.")
        return None


def load_background(a):
    src = a.input
    if src.lower().endswith((".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi")):
        t = a.time if a.time is not None else probe_duration(src) * 0.25
        tmp = os.path.join(tempfile.mkdtemp(), "frame.jpg")
        src = grab_frame(src, t, tmp)
    img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    return ImageOps.fit(img, (W, H), method=Image.LANCZOS,
                        centering=(0.5, a.focus_y)).convert("RGBA")


def draw_guides(img):
    g = img.copy()
    d = ImageDraw.Draw(g)
    crop_top = (H - 1440) // 2  # recorte 3:4 de la grilla del perfil
    d.rectangle([0, crop_top, W - 1, crop_top + 1440], outline=(255, 60, 60), width=4)
    d.rectangle([0, int(H * 0.80), W, H], outline=(255, 200, 0), width=3)  # zona UI inferior
    return g


def cmd_render(a):
    fonts = {"serif": find_font("serif", a.serif_font), "bold": find_font("bold", a.bold_font)}
    print(f"Serif: {fonts['serif']}\nBold:  {fonts['bold']}")
    if "fallback" in fonts["serif"] or "fallback" in fonts["bold"]:
        print("Aviso: usando fuente de respaldo. Pon Georgia Pro / Owners en "
              f"{FONTS_DIR} para el resultado final.")

    bg = load_background(a)
    bg = top_scrim(bg, a.scrim)
    if a.darken > 0:
        bg = Image.blend(bg, Image.new("RGBA", bg.size, (0, 0, 0, 255)), a.darken)

    color = a.color
    gap = int(W * a.gap)
    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, b in enumerate(parse_lines(a.line)):
        block = compose_block(b["lines"], fonts, a.scale, color, gap)
        y = b["y"] if b["y"] is not None else a.y
        text_layer.alpha_composite(block, ((W - block.width) // 2, int(H * y)))
    text_layer = add_shadow(text_layer, a.shadow)

    out = bg.copy()
    out.alpha_composite(text_layer)
    if a.depth:
        mask = person_mask(bg)
        if mask is not None:
            out.paste(bg, (0, 0), mask)

    out = out.convert("RGB")
    out.save(a.out, quality=95)
    print(f"Portada: {a.out}")
    if a.guides:
        gp = os.path.splitext(a.out)[0] + "_guias.png"
        draw_guides(out).save(gp)
        print(f"Guías:   {gp}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("frames", help="extrae frames candidatos de un video")
    f.add_argument("video")
    f.add_argument("--n", type=int, default=12)
    f.add_argument("--max-pos", type=float, default=0.6, help="hasta qué fracción del video mirar")
    f.add_argument("--out", default="frames")
    f.set_defaults(fn=cmd_frames)

    r = sub.add_parser("render", help="compone la portada")
    r.add_argument("--input", required=True, help="imagen o video")
    r.add_argument("--time", type=float, help="segundo del frame si --input es video")
    r.add_argument("--line", action="append", required=True,
                   help="'serif|texto', 'bold|texto', 'serif-xl|texto', align opcional "
                        "'|left' o '|right', y 'break|0.58' para un segundo bloque")
    r.add_argument("--y", type=float, default=0.15, help="altura del primer bloque (fracción)")
    r.add_argument("--gap", type=float, default=0.018, help="espacio entre líneas (fracción del ancho)")
    r.add_argument("--scale", type=float, default=1.0, help="escala global del texto")
    r.add_argument("--color", default="#FFFFFF")
    r.add_argument("--shadow", type=float, default=0.45, help="0 = sin sombra")
    r.add_argument("--scrim", type=float, default=0.0, help="oscurecer la parte de arriba (0-1)")
    r.add_argument("--darken", type=float, default=0.0, help="oscurecer toda la foto (0-1)")
    r.add_argument("--focus-y", type=float, default=0.4, help="centro vertical del recorte (0-1)")
    r.add_argument("--depth", action="store_true", help="persona delante del título (requiere rembg)")
    r.add_argument("--guides", action="store_true", help="exporta además una vista con zonas seguras")
    r.add_argument("--serif-font")
    r.add_argument("--bold-font")
    r.add_argument("--out", default="portada.png")
    r.set_defaults(fn=cmd_render)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
