import os
import json
import numpy as np
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw
from sklearn.cluster import KMeans
import customtkinter as ctk

# --------------------- Config ---------------------- #
HISTORY_FILE = "palette_history.json"
EXPORT_SIZES = [1, 8, 32]
DEFAULT_NUM_COLORS = 12

# ------------------ Color Utils -------------------- #
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

# ------------------ Main App Class ------------------ #
class PaletteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("lava.pallete 🐉")
        self.root.geometry("900x600")
        self.root.resizable(False, False)

        self.image = None
        self.num_colors = DEFAULT_NUM_COLORS

        self.build_ui()

    def build_ui(self):
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left Panel
        left = ctk.CTkFrame(main_frame, width=280)
        left.pack(side="left", fill="y", padx=10, pady=10)

        # Frame to simulate border
        self.image_frame = ctk.CTkFrame(left, width=254, height=254, corner_radius=12, fg_color="#444444")
        self.image_frame.pack(pady=10)
        self.image_frame.pack_propagate(False)  # fix size
        
        # Label inside frame
        self.image_label = ctk.CTkLabel(
            self.image_frame, text="Drop Image Here", width=250, height=250,
            corner_radius=10, fg_color="transparent", anchor="center"
        )
        self.image_label.pack(expand=True, fill="both")
        
        # Drag and drop binding on label
        self.image_label.drop_target_register(DND_FILES)
        self.image_label.dnd_bind("<<Drop>>", self.on_drop)
        
        self.image_label.drop_target_register(DND_FILES)
        self.image_label.dnd_bind("<<Drop>>", self.on_drop)

        self.select_btn = ctk.CTkButton(left, text="Select Image", command=self.select_image)
        self.select_btn.pack(pady=(10, 5))

        ctk.CTkLabel(left, text="Number of Colors:").pack(pady=(20, 5))

        slider_frame = ctk.CTkFrame(left, fg_color="transparent")
        slider_frame.pack(padx=10, fill="x")

        self.color_count = ctk.IntVar(value=self.num_colors)

        self.slider = ctk.CTkSlider(
            slider_frame, from_=3, to=24, number_of_steps=21,
            variable=self.color_count, command=lambda e: self.update_color_count()
        )
        self.slider.pack(side="left", fill="x", expand=True)

        self.color_label = ctk.CTkLabel(slider_frame, text=str(self.num_colors), width=40)
        self.color_label.pack(side="right", padx=(10, 0))

        self.export_btn = ctk.CTkButton(
            left, text="Export Palette", command=self.export_files, state="disabled"
        )
        self.export_btn.pack(pady=20)

        # Right Panel (Palette)
        self.palette_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.palette_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    def update_color_count(self):
        self.color_label.configure(text=str(self.color_count.get()))
        self.generate_palette()

    def on_drop(self, event):
        path = event.data.strip().replace('{', '').replace('}', '')
        if os.path.isfile(path) and path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            self.load_image(path)
        else:
            messagebox.showwarning("Invalid File", "Please drop a valid image file.")

    def select_image(self):
        filetypes = [("Image Files", "*.png *.jpg *.jpeg *.webp")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.load_image(path)

    def load_image(self, path):
        try:
            self.image = Image.open(path).convert("RGB")
            self.image_path = path
            self.display_image(self.image)
            self.generate_palette()
            self.export_btn.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def display_image(self, img):
        preview = img.copy()
        preview.thumbnail((250, 250))
        self.tk_img = ImageTk.PhotoImage(preview)
        self.image_label.configure(image=self.tk_img, text="", fg_color="transparent")

    def generate_palette(self):
        if not self.image:
            return

        for widget in self.palette_frame.winfo_children():
            widget.destroy()

        self.num_colors = self.color_count.get()
        self.colors = extract_colors(self.image, self.num_colors)

        columns = 4
        for i, color in enumerate(self.colors):
            hex_color = rgb_to_hex(color)
            tile = ctk.CTkLabel(
                self.palette_frame,
                text=hex_color,
                width=180,
                height=40,
                corner_radius=6,
                fg_color=hex_color,
                text_color="white" if sum(color) < 400 else "black"
            )
            tile.grid(row=i // columns, column=i % columns, padx=8, pady=8, sticky="nsew")

        for i in range(columns):
            self.palette_frame.grid_columnconfigure(i, weight=1)

    def export_files(self):
        base = os.path.splitext(os.path.basename(self.image_path))[0]
        folder = filedialog.askdirectory(title="Select Folder to Export")
        if not folder:
            return

        export_gpl(self.colors, os.path.join(folder, f"{base}.gpl"))
        for scale in EXPORT_SIZES:
            export_png(self.colors, os.path.join(folder, f"{base}_x{scale}.png"), scale)

        save_history({
            "file": self.image_path,
            "colors": [rgb_to_hex(c) for c in self.colors]
        })
        messagebox.showinfo("Success", "Palette exported!")

# ---------------------- Entry Point ---------------------- #
if __name__ == "__main__":
    root = TkinterDnD.Tk()

    # Setup CustomTkinter theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    try:
        root.tk.eval('package require tkdnd')
    except Exception as e:
        print("tkdnd load error:", e)
        messagebox.showerror("Drag & Drop Error", "Could not load tkdnd extension.\nDrag-and-drop may not work.")

    app = PaletteApp(root)
    root.mainloop()
