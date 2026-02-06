"""
Image Processing Desktop Application
Demonstrates OOP principles, Tkinter GUI, and OpenCV image processing
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import os


class ImageProcessor:
    """
    Handles all image processing operations.
    Demonstrates encapsulation with private methods and data.
    """
    
    def __init__(self):
        """Initialize the image processor with default values."""
        self._original_image: Optional[np.ndarray] = None
        self._current_image: Optional[np.ndarray] = None
        self._history: list = []
        self._redo_stack: list = []
        self._file_path: Optional[str] = None
    
    def load_image(self, file_path: str) -> bool:
        """
        Load an image from disk.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._original_image = cv2.imread(file_path)
            if self._original_image is None:
                return False
            
            self._current_image = self._original_image.copy()
            self._file_path = file_path
            self._history.clear()
            self._redo_stack.clear()
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def save_image(self, file_path: str) -> bool:
        """
        Save the current image to disk.
        
        Args:
            file_path: Path where image will be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self._current_image is None:
                return False
            
            cv2.imwrite(file_path, self._current_image)
            self._file_path = file_path
            return True
        except Exception as e:
            print(f"Error saving image: {e}")
            return False
    
    def _save_to_history(self) -> None:
        """Save current state to history for undo functionality."""
        self._history.append(self._current_image.copy())
        self._redo_stack.clear()
    
    def undo(self) -> bool:
        """
        Undo the last operation.
        
        Returns:
            True if undo was performed, False if no history
        """
        if self._history:
            self._redo_stack.append(self._current_image.copy())
            self._current_image = self._history.pop()
            return True
        return False
    
    def redo(self) -> bool:
        """
        Redo the last undone operation.
        
        Returns:
            True if redo was performed, False if no redo stack
        """
        if self._redo_stack:
            self._history.append(self._current_image.copy())
            self._current_image = self._redo_stack.pop()
            return True
        return False
    
    def reset(self) -> None:
        """Reset image to original state."""
        if self._original_image is not None:
            self._current_image = self._original_image.copy()
            self._history.clear()
            self._redo_stack.clear()
    
    # Image Processing Methods
    
    def to_grayscale(self) -> bool:
        """Convert image to grayscale."""
        if self._current_image is None:
            return False
        
        self._save_to_history()
        self._current_image = cv2.cvtColor(self._current_image, cv2.COLOR_BGR2GRAY)
        self._current_image = cv2.cvtColor(self._current_image, cv2.COLOR_GRAY2BGR)
        return True
    
    def apply_blur(self, intensity: int) -> bool:
        """
        Apply Gaussian blur to image.
        
        Args:
            intensity: Blur intensity (1-50, must be odd)
            
        Returns:
            True if successful
        """
        if self._current_image is None:
            return False
        
        self._save_to_history()
        kernel_size = max(1, intensity) | 1  # Ensure odd number
        self._current_image = cv2.GaussianBlur(
            self._current_image, (kernel_size, kernel_size), 0
        )
        return True
    
    def edge_detection(self) -> bool:
        """Apply Canny edge detection."""
        if self._current_image is None:
            return False
        
        self._save_to_history()
        gray = cv2.cvtColor(self._current_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        self._current_image = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        return True
    
    def adjust_brightness(self, value: float) -> bool:
        """
        Adjust image brightness.
        
        Args:
            value: Brightness adjustment (-100 to 100)
            
        Returns:
            True if successful
        """
        if self._current_image is None:
            return False
        
        self._save_to_history()
        brightness = cv2.convertScaleAbs(self._current_image, alpha=1, beta=value)
        self._current_image = np.clip(brightness, 0, 255).astype(np.uint8)
        return True
    
    def adjust_contrast(self, value: float) -> bool:
        """
        Adjust image contrast.
        
        Args:
            value: Contrast adjustment (0.5 to 3.0, where 1.0 is normal)
            
        Returns:
            True if successful
        """
        if self._current_image is None:
            return False
        
        self._save_to_history()
        contrast = cv2.convertScaleAbs(self._current_image, alpha=value, beta=0)
        self._current_image = np.clip(contrast, 0, 255).astype(np.uint8)
        return True
    
    def rotate_image(self, degrees: int) -> bool:
        """
        Rotate image by specified degrees.
        
        Args:
            degrees: Rotation angle (90, 180, or 270)
            
        Returns:
            True if successful
        """
        if self._current_image is None:
            return False
        
        self._save_to_history()
        rotations = {
            90: cv2.ROTATE_90_CLOCKWISE,
            180: cv2.ROTATE_180,
            270: cv2.ROTATE_90_COUNTERCLOCKWISE
        }
        
        if degrees in rotations:
            self._current_image = cv2.rotate(
                self._current_image, rotations[degrees]
            )
            return True
        return False
    
    def flip_image(self, direction: str) -> bool:
        """
        Flip image horizontally or vertically.
        
        Args:
            direction: 'horizontal' or 'vertical'
            
        Returns:
            True if successful
        """
        if self._current_image is None:
            return False
        
        self._save_to_history()
        if direction == 'horizontal':
            self._current_image = cv2.flip(self._current_image, 1)
        elif direction == 'vertical':
            self._current_image = cv2.flip(self._current_image, 0)
        else:
            return False
        return True
    
    def resize_image(self, width: int, height: int) -> bool:
        """
        Resize image to specified dimensions.
        
        Args:
            width: Target width
            height: Target height
            
        Returns:
            True if successful
        """
        if self._current_image is None or width <= 0 or height <= 0:
            return False
        
        self._save_to_history()
        self._current_image = cv2.resize(self._current_image, (width, height))
        return True
    
    def get_current_image(self) -> Optional[np.ndarray]:
        """Get current image (private data access)."""
        return self._current_image
    
    def get_image_info(self) -> dict:
        """
        Get information about current image.
        
        Returns:
            Dictionary with image metadata
        """
        info = {
            'filename': Path(self._file_path).name if self._file_path else 'None',
            'dimensions': None,
            'file_size': None,
            'has_image': False
        }
        
        if self._current_image is not None:
            height, width = self._current_image.shape[:2]
            info['dimensions'] = f"{width} × {height}"
            info['has_image'] = True
        
        if self._file_path and os.path.exists(self._file_path):
            info['file_size'] = f"{os.path.getsize(self._file_path) / 1024:.1f} KB"
        
        return info


class ImageDisplay:
    """
    Manages image display in the GUI.
    Demonstrates encapsulation and separation of concerns.
    """
    
    def __init__(self, parent_frame: tk.Widget, width: int = 800, height: int = 600):
        """
        Initialize image display.
        
        Args:
            parent_frame: Parent Tkinter frame
            width: Display width
            height: Display height
        """
        self._width = width
        self._height = height
        self._label = tk.Label(
            parent_frame,
            bg='#2b2b2b',
            fg='#ffffff'
        )
        self._label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._current_photo = None
    
    def display_image(self, cv_image: np.ndarray) -> None:
        """
        Display a CV2 image in the label.
        
        Args:
            cv_image: OpenCV image (BGR format)
        """
        if cv_image is None:
            self._label.config(image='', text='No image loaded')
            return
        
        # Convert BGR to RGB for PIL
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_image)
        
        # Scale to fit display while maintaining aspect ratio
        pil_image.thumbnail((self._width, self._height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        self._current_photo = ImageTk.PhotoImage(pil_image)
        self._label.config(image=self._current_photo, text='')
    
    def show_message(self, message: str) -> None:
        """Display a message in the display area."""
        self._label.config(image='', text=message)
        self._current_photo = None


class ImageProcessingApp:
    """
    Main application class that coordinates all components.
    Demonstrates composition and interaction between classes.
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the application.
        
        Args:
            root: Root Tkinter window
        """
        self._root = root
        self._root.title("Image Processing Studio")
        self._root.geometry("1400x900")
        
        # Initialize components
        self._processor = ImageProcessor()
        
        # Setup GUI
        self._setup_style()
        self._setup_menu()
        self._setup_main_layout()
        
        # Status
        self._last_operation = ""
    
    def _setup_style(self) -> None:
        """Configure application styling."""
        style = ttk.Style()
        
        # Modern theme colors
        self._bg_color = '#1e1e1e'
        self._fg_color = '#ffffff'
        self._accent_color = '#0078d4'
        self._button_color = '#2b2b2b'
        
        self._root.config(bg=self._bg_color)
    
    def _setup_menu(self) -> None:
        """Create application menu bar."""
        menubar = tk.Menu(self._root, bg=self._button_color, fg=self._fg_color)
        self._root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, bg=self._button_color, fg=self._fg_color, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self._open_image, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self._save_image, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self._save_as_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._root.quit, accelerator="Ctrl+Q")
        
        # Edit Menu
        edit_menu = tk.Menu(menubar, bg=self._button_color, fg=self._fg_color, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self._undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self._redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Reset to Original", command=self._reset_image)
        
        # Keyboard shortcuts
        self._root.bind('<Control-o>', lambda e: self._open_image())
        self._root.bind('<Control-s>', lambda e: self._save_image())
        self._root.bind('<Control-q>', lambda e: self._root.quit())
        self._root.bind('<Control-z>', lambda e: self._undo())
        self._root.bind('<Control-y>', lambda e: self._redo())
    
    def _setup_main_layout(self) -> None:
        """Create main layout with image display and control panel."""
        main_container = tk.Frame(self._root, bg=self._bg_color)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left side: Image display
        display_frame = tk.Frame(main_container, bg=self._bg_color)
        display_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self._display = ImageDisplay(display_frame, width=900, height=700)
        self._display.show_message("Open an image to get started")
        
        # Right side: Control panel
        control_frame = tk.Frame(main_container, bg=self._button_color, width=350)
        control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        control_frame.pack_propagate(False)
        
        self._setup_control_panel(control_frame)
        
        # Bottom: Status bar
        self._setup_status_bar()
    
    def _setup_control_panel(self, parent: tk.Widget) -> None:
        """Create control panel with adjustment sliders and buttons."""
        # Title
        title = tk.Label(
            parent,
            text="Image Controls",
            font=("Segoe UI", 14, "bold"),
            bg=self._button_color,
            fg=self._fg_color
        )
        title.pack(pady=(15, 20))
        
        # Create scrollable frame for controls
        canvas = tk.Canvas(parent, bg=self._button_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self._button_color)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mousewheel for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10))
        
        # Basic Filters Section
        self._add_section_label(scrollable_frame, "Basic Filters")
        self._add_button(scrollable_frame, "Grayscale", self._apply_grayscale)
        self._add_button(scrollable_frame, "Edge Detection", self._apply_edge_detection)
        
        # Blur Control
        self._add_section_label(scrollable_frame, "Blur Effect")
        self._blur_var = tk.IntVar(value=5)
        self._add_slider(
            scrollable_frame,
            "Blur Intensity:",
            self._blur_var,
            1, 50,
            self._apply_blur
        )
        
        # Brightness Control
        self._add_section_label(scrollable_frame, "Brightness")
        self._brightness_var = tk.IntVar(value=0)
        self._add_slider(
            scrollable_frame,
            "Brightness:",
            self._brightness_var,
            -100, 100,
            self._apply_brightness
        )
        
        # Contrast Control
        self._add_section_label(scrollable_frame, "Contrast")
        self._contrast_var = tk.DoubleVar(value=1.0)
        self._add_slider(
            scrollable_frame,
            "Contrast:",
            self._contrast_var,
            0.5, 3.0,
            self._apply_contrast,
            is_float=True
        )
        
        # Rotation Section
        self._add_section_label(scrollable_frame, "Rotation")
        rotation_frame = tk.Frame(scrollable_frame, bg=self._button_color)
        rotation_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self._add_button(rotation_frame, "90°", lambda: self._apply_rotation(90))
        self._add_button(rotation_frame, "180°", lambda: self._apply_rotation(180))
        self._add_button(rotation_frame, "270°", lambda: self._apply_rotation(270))
        
        # Flip Section
        self._add_section_label(scrollable_frame, "Flip")
        flip_frame = tk.Frame(scrollable_frame, bg=self._button_color)
        flip_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self._add_button(flip_frame, "Horizontal", lambda: self._apply_flip('horizontal'))
        self._add_button(flip_frame, "Vertical", lambda: self._apply_flip('vertical'))
        
        # Resize Section
        self._add_section_label(scrollable_frame, "Resize")
        
        resize_frame = tk.Frame(scrollable_frame, bg=self._button_color)
        resize_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(resize_frame, text="Width:", bg=self._button_color, fg=self._fg_color).pack(side=tk.LEFT)
        self._width_var = tk.StringVar(value="800")
        tk.Entry(resize_frame, textvariable=self._width_var, width=10, bg='#3b3b3b', fg=self._fg_color).pack(side=tk.LEFT, padx=5)
        
        tk.Label(resize_frame, text="Height:", bg=self._button_color, fg=self._fg_color).pack(side=tk.LEFT)
        self._height_var = tk.StringVar(value="600")
        tk.Entry(resize_frame, textvariable=self._height_var, width=10, bg='#3b3b3b', fg=self._fg_color).pack(side=tk.LEFT, padx=5)
        
        self._add_button(scrollable_frame, "Apply Resize", self._apply_resize)
    
    def _setup_status_bar(self) -> None:
        """Create status bar at bottom of window."""
        status_frame = tk.Frame(self._root, bg=self._button_color, height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self._status_label = tk.Label(
            status_frame,
            text="Ready | No image loaded",
            bg=self._button_color,
            fg='#999999',
            font=("Segoe UI", 9),
            anchor=tk.W,
            padx=10
        )
        self._status_label.pack(fill=tk.BOTH, expand=True)
    
    def _add_section_label(self, parent: tk.Widget, text: str) -> None:
        """Add a section divider label."""
        label = tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 10, "bold"),
            bg=self._button_color,
            fg=self._accent_color
        )
        label.pack(pady=(15, 8), padx=10, anchor=tk.W)
    
    def _add_button(self, parent: tk.Widget, text: str, command) -> None:
        """Add a styled button."""
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=self._accent_color,
            fg='#ffffff',
            border=0,
            padx=15,
            pady=8,
            font=("Segoe UI", 9),
            cursor="hand2",
            activebackground='#1084d7'
        )
        button.pack(fill=tk.X, padx=10, pady=4)
    
    def _add_slider(self, parent: tk.Widget, label: str, var, from_val, to_val, command, is_float=False) -> None:
        """Add a labeled slider control."""
        frame = tk.Frame(parent, bg=self._button_color)
        frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        label_widget = tk.Label(
            frame,
            text=label,
            bg=self._button_color,
            fg=self._fg_color,
            font=("Segoe UI", 9)
        )
        label_widget.pack(side=tk.LEFT)
        
        value_label = tk.Label(
            frame,
            text=f"{var.get():.1f}" if is_float else str(var.get()),
            bg=self._button_color,
            fg=self._accent_color,
            font=("Segoe UI", 9, "bold"),
            width=6,
            anchor=tk.E
        )
        value_label.pack(side=tk.RIGHT)
        
        def update_value(value):
            if is_float:
                value_label.config(text=f"{float(value):.1f}")
            else:
                value_label.config(text=str(int(float(value))))
            command()
        
        slider = tk.Scale(
            parent,
            from_=from_val,
            to=to_val,
            orient=tk.HORIZONTAL,
            variable=var,
            command=update_value,
            bg=self._button_color,
            fg=self._fg_color,
            highlightthickness=0,
            troughcolor='#3b3b3b',
            activebackground=self._accent_color
        )
        slider.pack(fill=tk.X, padx=10, pady=(0, 10))
    
    def _update_status(self, message: str) -> None:
        """Update status bar message."""
        info = self._processor.get_image_info()
        status = f"{message} | {info['filename']} | {info['dimensions'] or 'N/A'}"
        self._status_label.config(text=status)
    
    # File Operations
    
    def _open_image(self) -> None:
        """Open image file dialog."""
        file_path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png *.bmp"),
                ("JPEG Files", "*.jpg *.jpeg"),
                ("PNG Files", "*.png"),
                ("BMP Files", "*.bmp"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        if self._processor.load_image(file_path):
            self._display.display_image(self._processor.get_current_image())
            self._update_status(f"Opened: {Path(file_path).name}")
            self._reset_sliders()
        else:
            messagebox.showerror("Error", "Failed to open image")
    
    def _save_image(self) -> None:
        """Save current image."""
        info = self._processor.get_image_info()
        if not info['has_image']:
            messagebox.showwarning("Warning", "No image loaded")
            return
        
        # If already saved, overwrite
        if info['filename'] != 'None':
            if self._processor.save_image(self._processor._file_path):
                messagebox.showinfo("Success", "Image saved successfully")
                self._update_status("Image saved")
            else:
                messagebox.showerror("Error", "Failed to save image")
        else:
            self._save_as_image()
    
    def _save_as_image(self) -> None:
        """Save image with new filename."""
        info = self._processor.get_image_info()
        if not info['has_image']:
            messagebox.showwarning("Warning", "No image loaded")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG Files", "*.png"),
                ("JPEG Files", "*.jpg"),
                ("BMP Files", "*.bmp"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        if self._processor.save_image(file_path):
            messagebox.showinfo("Success", "Image saved successfully")
            self._update_status(f"Saved: {Path(file_path).name}")
        else:
            messagebox.showerror("Error", "Failed to save image")
    
    # Edit Operations
    
    def _undo(self) -> None:
        """Undo last operation."""
        if self._processor.undo():
            self._display.display_image(self._processor.get_current_image())
            self._update_status("Undone")
            self._reset_sliders()
        else:
            messagebox.showinfo("Info", "Nothing to undo")
    
    def _redo(self) -> None:
        """Redo last undone operation."""
        if self._processor.redo():
            self._display.display_image(self._processor.get_current_image())
            self._update_status("Redone")
            self._reset_sliders()
        else:
            messagebox.showinfo("Info", "Nothing to redo")
    
    def _reset_image(self) -> None:
        """Reset image to original."""
        self._processor.reset()
        self._display.display_image(self._processor.get_current_image())
        self._update_status("Reset to original")
        self._reset_sliders()
    
    def _reset_sliders(self) -> None:
        """Reset all sliders to default values."""
        self._blur_var.set(5)
        self._brightness_var.set(0)
        self._contrast_var.set(1.0)
    
    # Image Processing Operations
    
    def _apply_grayscale(self) -> None:
        """Apply grayscale filter."""
        if self._processor.to_grayscale():
            self._display.display_image(self._processor.get_current_image())
            self._update_status("Grayscale applied")
        else:
            messagebox.showwarning("Warning", "No image loaded")
    
    def _apply_blur(self) -> None:
        """Apply blur filter."""
        if self._processor.apply_blur(self._blur_var.get()):
            self._display.display_image(self._processor.get_current_image())
            self._update_status(f"Blur applied (intensity: {self._blur_var.get()})")
        else:
            messagebox.showwarning("Warning", "No image loaded")
    
    def _apply_edge_detection(self) -> None:
        """Apply edge detection."""
        if self._processor.edge_detection():
            self._display.display_image(self._processor.get_current_image())
            self._update_status("Edge detection applied")
        else:
            messagebox.showwarning("Warning", "No image loaded")
    
    def _apply_brightness(self) -> None:
        """Apply brightness adjustment."""
        # Create a fresh copy from the original for slider adjustments
        if self._processor._original_image is not None:
            self._processor._current_image = self._processor._original_image.copy()
            
            # Reapply all previous adjustments
            if self._processor.adjust_brightness(self._brightness_var.get()):
                self._display.display_image(self._processor.get_current_image())
                self._update_status(f"Brightness: {self._brightness_var.get()}")
    
    def _apply_contrast(self) -> None:
        """Apply contrast adjustment."""
        if self._processor._original_image is not None:
            self._processor._current_image = self._processor._original_image.copy()
            
            if self._processor.adjust_contrast(self._contrast_var.get()):
                self._display.display_image(self._processor.get_current_image())
                self._update_status(f"Contrast: {self._contrast_var.get():.1f}")
    
    def _apply_rotation(self, degrees: int) -> None:
        """Apply rotation."""
        if self._processor.rotate_image(degrees):
            self._display.display_image(self._processor.get_current_image())
            self._update_status(f"Rotated {degrees}°")
        else:
            messagebox.showwarning("Warning", "No image loaded")
    
    def _apply_flip(self, direction: str) -> None:
        """Apply flip transformation."""
        if self._processor.flip_image(direction):
            self._display.display_image(self._processor.get_current_image())
            self._update_status(f"Flipped {direction}")
        else:
            messagebox.showwarning("Warning", "No image loaded")
    
    def _apply_resize(self) -> None:
        """Apply image resize."""
        try:
            width = int(self._width_var.get())
            height = int(self._height_var.get())
            
            if width <= 0 or height <= 0:
                raise ValueError("Dimensions must be positive")
            
            if self._processor.resize_image(width, height):
                self._display.display_image(self._processor.get_current_image())
                self._update_status(f"Resized to {width}×{height}")
            else:
                messagebox.showwarning("Warning", "No image loaded")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid dimensions: {e}")


def main():
    """Main application entry point."""
    root = tk.Tk()
    app = ImageProcessingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
