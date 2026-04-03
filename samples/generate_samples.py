"""
Generate sample images for cv-12 Smart Attendance System.
Run: pip install Pillow && python generate_samples.py
Output: 8 face images — 4 people x 2 photos each (register + recognize).
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.dirname(__file__)


def make_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def save(img, name):
    img.save(os.path.join(OUT, name))
    print(f"  created: {name}")


def face_photo(skin, hair, shirt, name, bg=(230, 230, 230), slight_offset=(0, 0)):
    img = Image.new("RGB", (300, 350), bg)
    d = ImageDraw.Draw(img)
    ox, oy = slight_offset
    cx, cy = 150 + ox, 160 + oy
    # hair
    d.ellipse([cx - 75, cy - 90, cx + 75, cy + 10], fill=hair)
    # head
    d.ellipse([cx - 70, cy - 80, cx + 70, cy + 80], fill=skin)
    # neck
    d.rectangle([cx - 20, cy + 75, cx + 20, cy + 110], fill=skin)
    # shirt
    d.polygon([(cx - 80, cy + 110), (cx - 40, cy + 80), (cx + 40, cy + 80), (cx + 80, cy + 110),
               (cx + 100, cy + 200), (cx - 100, cy + 200)], fill=shirt)
    # eyes
    for ex in [cx - 25, cx + 25]:
        d.ellipse([ex - 12, cy - 15, ex + 12, cy + 12], fill=(255, 255, 255))
        d.ellipse([ex - 6, cy - 8, ex + 6, cy + 5], fill=(40, 30, 20))
    # eyebrows
    d.line([cx - 35, cy - 22, cx - 15, cy - 20], fill=(int(hair[0] * 0.8), int(hair[1] * 0.8), int(hair[2] * 0.8)), width=2)
    d.line([cx + 15, cy - 20, cx + 35, cy - 22], fill=(int(hair[0] * 0.8), int(hair[1] * 0.8), int(hair[2] * 0.8)), width=2)
    # nose
    d.polygon([(cx, cy + 10), (cx - 8, cy + 30), (cx + 8, cy + 30)], fill=(int(skin[0] * 0.85), int(skin[1] * 0.85), int(skin[2] * 0.85)))
    # mouth
    d.arc([cx - 20, cy + 38, cx + 20, cy + 58], start=0, end=180, fill=(180, 80, 80), width=3)
    # name label
    d.text((10, 310), name, fill=(60, 60, 60), font=make_font(16))
    return img


PEOPLE = [
    {"name": "Alice Johnson", "skin": (220, 180, 140), "hair": (60, 40, 20), "shirt": (60, 100, 180)},
    {"name": "Bob Williams", "skin": (180, 130, 90), "hair": (20, 15, 10), "shirt": (180, 60, 60)},
    {"name": "Carol Davis", "skin": (240, 200, 160), "hair": (160, 100, 40), "shirt": (60, 160, 100)},
    {"name": "David Lee", "skin": (160, 110, 80), "hair": (10, 8, 5), "shirt": (100, 60, 160)},
]

if __name__ == "__main__":
    print("Generating cv-12 samples...")
    for p in PEOPLE:
        slug = p["name"].lower().replace(" ", "_")
        # Registration photo (straight on)
        save(face_photo(p["skin"], p["hair"], p["shirt"], p["name"], bg=(240, 240, 240)),
             f"register_{slug}.jpg")
        # Recognition photo (slight variation — different bg, tiny offset)
        save(face_photo(p["skin"], p["hair"], p["shirt"], p["name"],
                        bg=(220, 230, 220), slight_offset=(5, -3)),
             f"recognize_{slug}.jpg")
    print("Done — 8 images in samples/")
