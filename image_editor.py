import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox
import os


class ImageProcessor:
    """Handles image processing operations using OpenCV."""

    @staticmethod
    def to_grayscale(image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def apply_blur(image, ksize=5):
        k = max(1, ksize)
        if k % 2 == 0:
            k += 1
        return cv2.GaussianBlur(image, (k, k), 0)

    @staticmethod
    def canny_edges(image, threshold1=100, threshold2=200):
        gray = image
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Canny(gray, threshold1, threshold2)

    @staticmethod
    def adjust_brightness_contrast(image, brightness=0, contrast=0):
        """
        brightness: -100 to 100 (adds value)
        contrast: -100 to 100 (scales differences)
        """
        beta = brightness
        alpha = (contrast + 100) / 100.0
        adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        return adjusted

    @staticmethod
    def rotate(image, angle):
        if angle == 90:
            return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(image, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            return image

    @staticmethod
    def flip(image, mode="horizontal"):
        if mode == "horizontal":
            return cv2.flip(image, 1)
        elif mode == "vertical":
            return cv2.flip(image, 0)
        return image

    @staticmethod
    def resize_image(image, scale=1.0):
        h, w = image.shape[:2]
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


class ImageModel:
    """Encapsulates image data and undo/redo history."""

    def __init__(self):
        self._original_image = None
        self._current_image = None
        self._history = []
        self._future = []
        self._filename = None

    @property
    def filename(self):
        return self._filename

    @property
    def current_image(self):
        return self._current_image

    def load_image(self, filepath):
        image = cv2.imread(filepath)
        if image is None:
            raise ValueError("Unsupported or corrupted image file.")
        self._original_image = image.copy()
        self._current_image = image
        self._history = [image.copy()]
        self._future = []
        self._filename = os.path.basename(filepath)

    def save_image(self, filepath):
        if self._current_image is None:
            raise ValueError("No image loaded.")
        cv2.imwrite(filepath, self._current_image)

    def apply_operation(self, op_func, *args, **kwargs):
        if self._current_image is None:
            raise ValueError("No image loaded.")
        new_img = op_func(self._current_image, *args, **kwargs)
        self._history.append(new_img.copy())
        self._current_image = new_img
        self._future.clear()

    def undo(self):
        if len(self._history) > 1:
            last = self._history.pop()
            self._future.append(last)
            self._current_image = self._history[-1]
        else:
            raise IndexError("Nothing to undo.")

    def redo(self):
        if self._future:
            img = self._future.pop()
            self._history.append(img)
            self._current_image = img
        else:
            raise IndexError("Nothing to redo.")

    def get_dimensions(self):
        if self._current_image is None:
            return None
        h, w = self._current_image.shape[:2]
        return w, h


class ImageEditorApp:
    """Main GUI application using Tkinter."""

    def __init__(self, root):
        self.root = root
        self.root.title("Image Editor - Tkinter & OpenCV")
        self.root.geometry("1000x700")

        self.model = ImageModel()

        self.brightness_value = tk.IntVar(value=0)
        self.contrast_value = tk.IntVar(value=0)
        self.blur_value = tk.IntVar(value=1)
        self.scale_value = tk.DoubleVar(value=1.0)

        self._create_menu()
        self._create_widgets()
        self._create_status_bar()

        self._tk_image = None
        self.current_file_path = None

    # ---------- GUI creation ----------

    def _create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_image)
        file_menu.add_command(label="Save", command=self.save_image)
        file_menu.add_command(label="Save As", command=self.save_image_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo)
        edit_menu.add_command(label="Redo", command=self.redo)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        self.root.config(menu=menubar)

    def _create_widgets(self):
        self.left_frame = tk.Frame(self.root, width=700, height=600, bg="grey")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.left_frame, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.right_frame = tk.Frame(self.root, width=300)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(self.right_frame, text="Operations", font=("Arial", 12, "bold")).pack(pady=5)

        tk.Button(self.right_frame, text="Grayscale", command=self.apply_grayscale).pack(fill=tk.X, padx=10, pady=2)
        tk.Button(self.right_frame, text="Blur", command=self.apply_blur).pack(fill=tk.X, padx=10, pady=2)
        tk.Button(self.right_frame, text="Edge Detection", command=self.apply_edges).pack(fill=tk.X, padx=10, pady=2)

        tk.Label(self.right_frame, text="Brightness").pack(pady=(10, 0))
        tk.Scale(self.right_frame, from_=-100, to=100, orient=tk.HORIZONTAL,
                 variable=self.brightness_value, command=self.on_brightness_contrast_change).pack(fill=tk.X, padx=10)

        tk.Label(self.right_frame, text="Contrast").pack(pady=(10, 0))
        tk.Scale(self.right_frame, from_=-100, to=100, orient=tk.HORIZONTAL,
                 variable=self.contrast_value, command=self.on_brightness_contrast_change).pack(fill=tk.X, padx=10)

        tk.Label(self.right_frame, text="Blur Intensity (kernel size)").pack(pady=(10, 0))
        tk.Scale(self.right_frame, from_=1, to=25, orient=tk.HORIZONTAL,
                 variable=self.blur_value).pack(fill=tk.X, padx=10)

        tk.Label(self.right_frame, text="Scale").pack(pady=(10, 0))
        tk.Scale(self.right_frame, from_=0.1, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
                 variable=self.scale_value, command=self.on_scale_change).pack(fill=tk.X, padx=10)

        tk.Label(self.right_frame, text="Rotate").pack(pady=(10, 0))
        tk.Button(self.right_frame, text="Rotate 90°", command=lambda: self.apply_rotation(90)).pack(fill=tk.X, padx=10, pady=2)
        tk.Button(self.right_frame, text="Rotate 180°", command=lambda: self.apply_rotation(180)).pack(fill=tk.X, padx=10, pady=2)
        tk.Button(self.right_frame, text="Rotate 270°", command=lambda: self.apply_rotation(270)).pack(fill=tk.X, padx=10, pady=2)

        tk.Label(self.right_frame, text="Flip").pack(pady=(10, 0))
        tk.Button(self.right_frame, text="Flip Horizontal", command=lambda: self.apply_flip("horizontal")).pack(fill=tk.X, padx=10, pady=2)
        tk.Button(self.right_frame, text="Flip Vertical", command=lambda: self.apply_flip("vertical")).pack(fill=tk.X, padx=10, pady=2)

    def _create_status_bar(self):
        self.status_bar = tk.Label(self.root, text="No image loaded", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ---------- File operations ----------

    def open_image(self):
        filetypes = [("Image files", "*.jpg *.jpeg *.png *.bmp"),
                     ("All files", "*.*")]
        filepath = filedialog.askopenfilename(title="Open Image", filetypes=filetypes)
        if not filepath:
            return
        try:
            self.model.load_image(filepath)
            self.current_file_path = filepath
            self._reset_adjustments()
            self.update_image_display()
            self.update_status_bar()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_image(self):
        if self.model.current_image is None:
            messagebox.showerror("Error", "No image to save.")
            return
        if self.current_file_path is None:
            self.save_image_as()
            return
        try:
            self.model.save_image(self.current_file_path)
            messagebox.showinfo("Saved", f"Image saved to {self.current_file_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_image_as(self):
        if self.model.current_image is None:
            messagebox.showerror("Error", "No image to save.")
            return
        filetypes = [("JPEG", "*.jpg"),
                     ("PNG", "*.png"),
                     ("BMP", "*.bmp")]
        filepath = filedialog.asksaveasfilename(title="Save Image As", defaultextension=".png",
                                                filetypes=filetypes)
        if not filepath:
            return
        try:
            self.model.save_image(filepath)
            self.current_file_path = filepath
            messagebox.showinfo("Saved", f"Image saved to {filepath}")
            self.update_status_bar()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_exit(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.root.destroy()

    # ---------- Edit operations (Undo/Redo) ----------

    def undo(self):
        try:
            self.model.undo()
            self.update_image_display()
            self.update_status_bar()
        except IndexError as e:
            messagebox.showinfo("Undo", str(e))

    def redo(self):
        try:
            self.model.redo()
            self.update_image_display()
            self.update_status_bar()
        except IndexError as e:
            messagebox.showinfo("Redo", str(e))

    # ---------- Image operations (buttons/controls) ----------

    def apply_grayscale(self):
        try:
            self.model.apply_operation(self._wrap_grayscale)
            self.update_image_display()
            self.update_status_bar()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _wrap_grayscale(self, img):
        gray = ImageProcessor.to_grayscale(img)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    def apply_blur(self):
        try:
            ksize = self.blur_value.get()
            self.model.apply_operation(ImageProcessor.apply_blur, ksize)
            self.update_image_display()
            self.update_status_bar()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def apply_edges(self):
        try:
            edges = ImageProcessor.canny_edges(self.model.current_image)
            edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            self.model.apply_operation(lambda img: edges_bgr)
            self.update_image_display()
            self.update_status_bar()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_brightness_contrast_change(self, _event=None):
        if self.model.current_image is None:
            return

        try:
            last_img = self.model._history[-1]
        except IndexError:
            return

        try:
            bright = self.brightness_value.get()
            cont = self.contrast_value.get()
            adjusted = ImageProcessor.adjust_brightness_contrast(last_img, brightness=bright, contrast=cont)
            self.model._current_image = adjusted
            self.update_image_display()
            self.update_status_bar()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def apply_rotation(self, angle):
        try:
            self.model.apply_operation(ImageProcessor.rotate, angle)
            self.update_image_display()
            self.update_status_bar()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def apply_flip(self, mode):
        try:
            self.model.apply_operation(ImageProcessor.flip, mode)
            self.update_image_display()
            self.update_status_bar()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_scale_change(self, _event=None):
        if self.model.current_image is None:
            return
        try:
            scale = self.scale_value.get()
            last_img = self.model._history[-1]
            resized = ImageProcessor.resize_image(last_img, scale=scale)
            self.model._current_image = resized
            self.update_image_display()
            self.update_status_bar()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------- Helpers ----------

    def _reset_adjustments(self):
        self.brightness_value.set(0)
        self.contrast_value.set(0)
        self.blur_value.set(1)
        self.scale_value.set(1.0)

    def update_image_display(self):
        img = self.model.current_image
        if img is None:
            return

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w > 1 and canvas_h > 1:
            pil_img = self._resize_to_fit(pil_img, canvas_w, canvas_h)

        self._tk_image = ImageTk.PhotoImage(pil_img)
        self.canvas.delete("all")
        self.canvas.create_image(canvas_w // 2, canvas_h // 2, image=self._tk_image, anchor=tk.CENTER)

    def _resize_to_fit(self, pil_image, max_w, max_h):
        w, h = pil_image.size
        scale = min(max_w / w, max_h / h, 1.0)
        new_size = (int(w * scale), int(h * scale))
        return pil_image.resize(new_size, Image.ANTIALIAS)

    def update_status_bar(self):
        dims = self.model.get_dimensions()
        if dims is None:
            self.status_bar.config(text="No image loaded")
        else:
            filename = self.model.filename or "Untitled"
            w, h = dims
            self.status_bar.config(text=f"{filename} - {w}x{h} px")

def main():
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
