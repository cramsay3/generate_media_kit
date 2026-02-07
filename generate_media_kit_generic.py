import os
from PIL import Image

def find_first_existing(*filenames):
    for f in filenames:
        if os.path.isfile(f):
            return f
    return None

def get_or_prompt(label, *default_candidates):
    found = find_first_existing(*default_candidates)
    if found:
        print(f"✅ Using {label}: {found}")
        return found
    while True:
        path = input(f"Enter filename for {label} ({' or '.join(default_candidates)}): ").strip()
        if os.path.isfile(path):
            return path
        print(f"❌ File not found: {path}")

def crop_center(img, target_size):
    aspect_ratio = target_size[0] / target_size[1]
    w, h = img.size
    current_ratio = w / h
    if current_ratio > aspect_ratio:
        new_width = int(h * aspect_ratio)
        offset = (w - new_width) // 2
        box = (offset, 0, offset + new_width, h)
    else:
        new_height = int(w / aspect_ratio)
        offset = (h - new_height) // 2
        box = (0, offset, w, offset + new_height)
    return img.crop(box)

def resize_and_save(image_file, output_path, size):
    img = Image.open(image_file).convert("RGB")
    img = crop_center(img, size)
    img = img.resize(size, Image.LANCZOS)
    img.save(output_path, format="JPEG", quality=95)

# === Setup ===
ARTIST_NAME = input("Enter artist name (e.g., Charley Ramsay): ").strip().replace(" ", "_")
BASE_DIR = f"{ARTIST_NAME}_Media_Kit"
os.makedirs(BASE_DIR, exist_ok=True)

# === Look for files ===
album_art = get_or_prompt("album art", "album_cover.jpg")
portrait = get_or_prompt("portrait image", "profile.jpg", "profile.jpeg")
wide = get_or_prompt("wide/banner image", "banner.jpg")

folders = [
    "Profile_Photos", "Banner_Images", "Album_Art",
    "Promo_Assets", "Live_Photos", "Source"
]
for folder in folders:
    os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)

# === Profile photos ===
resize_and_save(portrait, f"{BASE_DIR}/Profile_Photos/profile_sq_1080x1080.jpg", (1080, 1080))
resize_and_save(portrait, f"{BASE_DIR}/Profile_Photos/profile_sq_750x750.jpg", (750, 750))

# === Banner images ===
resize_and_save(wide, f"{BASE_DIR}/Banner_Images/fb_banner_1640x856.jpg", (1640, 856))
resize_and_save(wide, f"{BASE_DIR}/Banner_Images/yt_banner_2560x1440_safe1546x423.jpg", (2560, 1440))
resize_and_save(wide, f"{BASE_DIR}/Banner_Images/spotify_header_2660x1140.jpg", (2660, 1140))
resize_and_save(wide, f"{BASE_DIR}/Banner_Images/bandcamp_banner_975x40.jpg", (975, 40))
resize_and_save(wide, f"{BASE_DIR}/Banner_Images/reverbnation_banner_1240x260.jpg", (1240, 260))
resize_and_save(wide, f"{BASE_DIR}/Banner_Images/soundcloud_banner_2480x520.jpg", (2480, 520))

# === Album Art ===
resize_and_save(album_art, f"{BASE_DIR}/Album_Art/album_3000x3000.jpg", (3000, 3000))

# === Promo Assets ===
resize_and_save(portrait, f"{BASE_DIR}/Promo_Assets/ig_post_1080x1080.jpg", (1080, 1080))
resize_and_save(portrait, f"{BASE_DIR}/Promo_Assets/ig_story_1080x1920.jpg", (1080, 1920))
resize_and_save(wide, f"{BASE_DIR}/Promo_Assets/yt_thumb_1280x720.jpg", (1280, 720))
resize_and_save(wide, f"{BASE_DIR}/Promo_Assets/fb_event_1920x1005.jpg", (1920, 1005))

# === Originals ===
os.system(f'cp "{album_art}" "{BASE_DIR}/Source/album_art.jpg"')
os.system(f'cp "{portrait}" "{BASE_DIR}/Live_Photos/portrait.jpg"')
os.system(f'cp "{wide}" "{BASE_DIR}/Live_Photos/wide.jpg"')
os.system(f'cp "{portrait}" "{BASE_DIR}/Source/profile.jpg"')
os.system(f'cp "{wide}" "{BASE_DIR}/Source/banner.jpg"')

print(f"\\n✅ Media kit created at: {BASE_DIR}")
