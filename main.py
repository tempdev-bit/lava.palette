import os
import json
import numpy as np
from PIL import Image, ImageDraw
from sklearn.cluster import KMeans

import flet as ft
from flet import (
    FilePicker,
    FilePickerResultEvent,
    Column,
    Row,
    Container,
    Image as FtImage,
    Text,
    ElevatedButton,
    Slider,
    Switch,
    IconButton,
    ProgressBar,
    TextField,
    Colors,
    Icons as icons,
)

# ---------------- Config ---------------- #
HISTORY_FILE = "palette_history.json"
EXPORT_SIZES = [1, 8, 32]
DEFAULT_NUM_COLORS = 16
PREVIEW_SIZE = 200

# ---------------- Utils ---------------- #
def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % tuple(rgb)

def extract_colors(image, num_colors):
    img = image.resize((200, 200))
    data = np.array(img).reshape(-1, 3)
    kmeans = KMeans(n_clusters=num_colors, n_init='auto')
    kmeans.fit(data)
    return [tuple(map(int, c)) for c in kmeans.cluster_centers_]

def export_gpl(colors, filename):
    with open(filename, 'w') as f:
        f.write("GIMP Palette\nName: Exported Palette\nColumns: 0\n#\n")
        for c in colors:
            f.write(f"{c[0]} {c[1]} {c[2]}\t{rgb_to_hex(c)}\n")

def export_png(colors, filename, scale):
    width = len(colors) * scale
    height = scale
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for i, color in enumerate(colors):
        draw.rectangle([i*scale, 0, (i+1)*scale, height], fill=color)
    img.save(filename)

def save_history(entry):
    try:
        with open(HISTORY_FILE, "r") as f:
            existing = json.load(f)
    except:
        existing = []
    existing.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(existing, f, indent=2)

# ---------------- Main App ---------------- #
def main(page: ft.Page):
    page.title = "lava.palette 🐉"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20
    page.window_width = 1024
    page.window_height = 720

    image = None
    image_path = None
    colors = []

    preview_img = FtImage(width=PREVIEW_SIZE, height=PREVIEW_SIZE, visible=False)
    palette_grid = ft.GridView(
            expand=True,
            runs_count=0,          # auto wrap
            max_extent=200,        # max tile width
            child_aspect_ratio=1.5, # width/height ratio of color tiles
            spacing=10,
            run_spacing=10,
        )

    def load_image(path):
        nonlocal image, image_path, colors
        image_path = path
        image = Image.open(path).convert("RGB")
        preview = image.copy()
        preview.thumbnail((PREVIEW_SIZE, PREVIEW_SIZE))
        thumb_path = "_preview.png"
        preview.save(thumb_path)
        preview_img.src = thumb_path
        preview_img.visible = True
        generate_palette(None)
        export_btn.disabled = False
        page.update()

    def generate_palette(e):
        nonlocal colors
        if image is None:
            return
        num = int(slider.value)
        colors = extract_colors(image, num)
        palette_grid.controls.clear()
        for color in colors:
            hex_color = rgb_to_hex(color)
            tile = Container(
                content=Text(hex_color, color="white" if sum(color) < 400 else "black"),
                bgcolor=hex_color,
                width=180,
                height=48,
                border_radius=10,
                alignment=ft.alignment.center
            )
            palette_grid.controls.append(tile)
        page.update()

    def select_file_result(e: FilePickerResultEvent):
        if e.files:
            load_image(e.files[0].path)

    def export_palette(e):
        if not image_path:
            return
        folder = os.path.join(os.path.expanduser("~"), "Downloads")
        if not folder:
            return
        base = os.path.splitext(os.path.basename(image_path))[0]
        export_gpl(colors, os.path.join(folder, f"{base}.gpl"))
        for scale in EXPORT_SIZES:
            export_png(colors, os.path.join(folder, f"{base}_x{scale}.png"), scale)
        save_history({
            "file": image_path,
            "colors": [rgb_to_hex(c) for c in colors]
        })
        page.snack_bar = ft.SnackBar(ft.Text("✅ Palette exported!"))
        page.snack_bar.open = True
        page.update()

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if theme_switch.value else ft.ThemeMode.LIGHT
        page.update()

    file_picker = FilePicker(on_result=select_file_result)
    folder_picker = FilePicker()
    page.overlay.extend([file_picker, folder_picker])

    slider = Slider(
        min=2,
        max=24,
        divisions=20,
        label="{value}",
        value=DEFAULT_NUM_COLORS,
        on_change=generate_palette
    )

    theme_switch = Switch(label="Dark Mode", value=True, on_change=toggle_theme)

    export_btn = ElevatedButton("⬇ Export Palette", on_click=export_palette, disabled=True)

    browse_button = ElevatedButton(
        text="Browse Image",
        icon=icons.IMAGE,
        on_click=lambda _: file_picker.pick_files(allow_multiple=False)
    )

    page.add(
        Row([
            Column([
                Text("lava.palette 🐉", size=28, weight=ft.FontWeight.BOLD),
                browse_button,
                preview_img,
                Text("Number of Colors:"),
                slider,
                export_btn,
                theme_switch
            ], width=350, spacing=20),
            Container(
                content=palette_grid,
                expand=True,
                padding=10,
                border_radius=12,
                bgcolor="#2b2b2b"  # dark gray background
            )
        ], expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)
