#!/usr/bin/env python3
"""Generate 1200x630 OG images per model into routevault-web/public/og/.
Called standalone and from publish_db.py for new models."""
import os
import sqlite3

ROOT = os.environ.get("ROUTEVAULT_ROOT", "/mnt/nas/agents/Projects/RouteVault")
WEB = os.path.join(ROOT, "code", "routevault-web", "public", "og")

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG = (10, 14, 22)
ACCENT = (74, 144, 217)
DEEP = (26, 54, 93)
TEXT = (232, 238, 246)
DIM = (150, 162, 180)


def _font(size, bold=False):
    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else ""),
        "/usr/share/fonts/truetype/liberation/LiberationSans%s.ttf" % ("-Bold" if bold else "-Regular"),
    ):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def gen(model_id, label, provider, price_in, price_out, out_path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=ACCENT)
    d.text((70, 60), "RouteVault", font=_font(44, bold=True), fill=TEXT)
    d.text((70, 116), "Live AI model prices, scored for humans", font=_font(24), fill=DIM)
    # model id wraps
    words, lines, cur = model_id.split("."), [], ""
    f_model = _font(64, bold=True)
    for part in model_id.split("/"):
        if d.textlength(cur + part, font=f_model) > W - 140 and cur:
            lines.append(cur); cur = ""
        cur += part
    if cur:
        lines.append(cur)
    y = 220
    for ln in lines[:2]:
        d.text((70, y), ln, font=f_model, fill=TEXT)
        y += 80
    d.text((70, y + 18), f"{label} · {provider}", font=_font(34), fill=ACCENT)
    d.text((70, H - 150), f"In ${price_in}/M   ·   Out ${price_out}/M", font=_font(40, bold=True), fill=TEXT)
    d.text((70, H - 80), "routevault.ai/model/" + model_id, font=_font(26), fill=DIM)
    img.save(out_path, "PNG")


def main():
    os.makedirs(WEB, exist_ok=True)
    conn = sqlite3.connect(os.path.join(ROOT, "data", "routevault.db"))
    conn.row_factory = sqlite3.Row
    made = 0
    for r in conn.execute("SELECT * FROM models WHERE COALESCE(is_deprecated,0)=0"):
        out = os.path.join(WEB, f"{r['model_id']}.png")
        if os.path.exists(out):
            continue
        gen(r["model_id"], r["rv_label"] or "Model", r["provider"],
            r["current_input_price"], r["current_output_price"], out)
        made += 1
    print(f"og images: {made} generated, {len(os.listdir(WEB))} total")


if __name__ == "__main__":
    main()
