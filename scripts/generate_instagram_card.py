#!/usr/bin/env python3
"""
scripts/generate_instagram_card.py
Genera una scheda grafica moderna in formato Instagram Story (1080x1920) / Post
con il piano Benchmark a 3 Giorni di BAgent.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "storage" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_IMG = OUTPUT_DIR / "instagram_benchmark_story.png"

def create_instagram_card():
    width = 1080
    height = 1920
    img = Image.new("RGB", (width, height), color=(15, 23, 42)) # Slate dark 900
    draw = ImageDraw.Draw(img)

    # Gradient / background accent
    for y in range(400):
        alpha = int(40 * (1 - y / 400))
        draw.line([(0, y), (width, y)], fill=(16, 185, 129, alpha)) # Emerald glow

    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 56)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        font_card_h = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 44)
        font_card_txt = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        font_footer = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    except Exception:
        font_title = font_sub = font_card_h = font_card_txt = font_footer = ImageFont.load_default()

    # Top Header
    draw.text((width // 2, 120), "BAGENT SPORTS AI", fill=(52, 211, 153), font=font_sub, anchor="mt")
    draw.text((width // 2, 180), "72H BENCHMARK TEST", fill=(255, 255, 255), font=font_title, anchor="mt")
    draw.text((width // 2, 260), "Paper Trading Challenge (Zero Rischio)", fill=(148, 163, 184), font=font_sub, anchor="mt")

    # Cards
    cards_data = [
        {
            "day": "GIORNO 1: MARTEDÌ 22 SET",
            "odds": "@ 2.12",
            "matches": [
                "• Lanús vs Estudiantes: Under 3.0 Asiatico (Push)",
                "• Arsenal W vs HB Køge: MultiGol 2-4 Casa",
                "• Juventus W vs Benfica W: 1X + MultiGol 1-5"
            ],
            "badge": "PARACADUTE ASIATICO + WOMEN CL",
            "color": (30, 41, 59)
        },
        {
            "day": "GIORNO 2: MERCOLEDÌ 23 SET",
            "odds": "@ 2.05",
            "matches": [
                "• Servette W vs Lione F: 2 + Over 1.5",
                "• Barcellona F vs Paris FC: 1 + MultiGol 2-5",
                "• Chelsea W vs Austria Vienna: 1X + Over 1.5"
            ],
            "badge": "BIG DOMINANTI & ANTI-CEILING",
            "color": (30, 41, 59)
        },
        {
            "day": "GIORNO 3: GIOVEDÌ 24 SET",
            "odds": "@ 2.16",
            "matches": [
                "• Olanda vs Germania: Over 1.5 Gol (xG > 3.20)",
                "• Portogallo vs Galles: 1X + MultiGol 1-5",
                "• Norvegia vs Danimarca: 1X o Over 1.5"
            ],
            "badge": "BATTESIMO UEFA NATIONS LEAGUE A",
            "color": (30, 41, 59)
        }
    ]

    card_y = 360
    card_h = 390
    margin_x = 70

    for c in cards_data:
        # Draw card container
        draw.rounded_rectangle(
            [(margin_x, card_y), (width - margin_x, card_y + card_h)],
            radius=28,
            fill=c["color"],
            outline=(51, 65, 85),
            width=2
        )

        # Header card
        draw.text((margin_x + 40, card_y + 35), c["day"], fill=(255, 255, 255), font=font_card_h)
        draw.text((width - margin_x - 40, card_y + 35), c["odds"], fill=(52, 211, 153), font=font_card_h, anchor="ra")

        # Badge
        draw.text((margin_x + 40, card_y + 95), f"🎯 {c['badge']}", fill=(56, 189, 248), font=font_footer)

        # Divider
        draw.line([(margin_x + 40, card_y + 140), (width - margin_x - 40, card_y + 140)], fill=(51, 65, 85), width=1)

        # Matches text
        m_y = card_y + 165
        for m in c["matches"]:
            draw.text((margin_x + 40, m_y), m, fill=(226, 232, 240), font=font_card_txt)
            m_y += 65

        card_y += card_h + 50

    # Bottom Footer
    footer_box_y = 1680
    draw.rounded_rectangle(
        [(margin_x, footer_box_y), (width - margin_x, footer_box_y + 160)],
        radius=20,
        fill=(15, 23, 42),
        outline=(16, 185, 129),
        width=2
    )
    draw.text((width // 2, footer_box_y + 35), "🛡️ 100% STRICT VALIDATOR CERTIFIED", fill=(52, 211, 153), font=font_card_txt, anchor="mt")
    draw.text((width // 2, footer_box_y + 95), "Audit Hugging Face SportsBERT • Zero Seconde Categorie", fill=(148, 163, 184), font=font_footer, anchor="mt")

    img.save(OUTPUT_IMG, "PNG")
    print(f"✅ Scheda Instagram Story generata con successo: {OUTPUT_IMG}")

if __name__ == "__main__":
    create_instagram_card()
