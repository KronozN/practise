# Object-Oriented Programming Architecture

## Overview

The Image Processing Studio application demonstrates professional object-oriented design with three core classes that work together using composition and delegation patterns. This document explains how OOP principles are implemented.

---

## Class Hierarchy & Relationships

```
ImageProcessingApp (Main Application)
├── Composes: ImageProcessor
├── Composes: ImageDisplay
└── Manages: Tkinter GUI Components
```

**Design Pattern**: Composition over Inheritance
- Classes don't inherit from each other
- Instead, they compose (contain) each other
- Each class has one clear responsibility
- More flexible and maintainable than inheritance

---

## 1. ImageProcessor Class

### Purpose
Core business logic for image processing. Encapsulates all image data and operations.

### Encapsulation in Action

```python
class ImageProcessor:
    def __init__(self):
        # PRIVATE data members (not directly accessible)
        self._original_image = None      # Original file image
        self._current_image = None       # Working copy
        self._history = []               # For undo
        self._redo_stack = []            # For redo
        self._file_path = None           # Current file
```

**Key Principle**: Users of this class cannot directly modify these attributes.
```python
# ❌ WRONG - Can't do this (private, indicated by underscore)
processor._original_image = some_image

# ✅ RIGHT - Use public methods instead
processor.load_image(file_path)
processor.to_grayscale()
```

### Constructor (Initialization)

The `__init__` method properly initializes all state:
```python
def __init__(self):
    self._original_image = None      # Not loaded yet
    self._current_image = None       # Not loaded yet
    self._history = []               # Empty history
    self._redo_stack = []            # Empty redo
    self._file_path = None           # No file open
```

**Why this matters**:
- Objects start in a known, valid state
- No undefined behavior
- All attributes initialized before use

### Methods & Single Responsibility

Each method does ONE thing well:

```python
# ✅ GOOD - Single responsibility
def to_grayscale(self) -> bool:
    """Convert current image to grayscale."""
    if self._current_image is None:
        return False
    self._save_to_history()
    self._current_image = cv2.cvtColor(...)
    return True
```

```python
# ❌ BAD - Too many responsibilities
def process_image_multiple_ways(self):
    self.to_grayscale()
    self.apply_blur()
    self.adjust_brightness()
    self.save_image()
    # Too much! Hard to test, maintain, reuse
```

### History Management (Undo/Redo)

Internal history stack pattern:

```python
def _save_to_history(self) -> None:
    """PRIVATE method - saves state for undo."""
    self._history.append(self._current_image.copy())
    self._redo_stack.clear()  # Clear redo stack on new operation

def undo(self) -> bool:
    """PUBLIC method - interface for undo."""
    if self._history:
        self._redo_stack.append(self._current_image.copy())
        self._current_image = self._history.pop()
        return True
    return False
```

**Data Access Control**:
- `_save_to_history()` is PRIVATE (internal only)
- `undo()` is PUBLIC (external interface)
- Users interact with undo(), never directly with history

### Type Hints

All methods use type hints for clarity:

```python
def resize_image(self, width: int, height: int) -> bool:
    #                       ^^^         ^^^        ^^^^
    #                    Parameter types      Return type
    """
    Args:
        width: Target width (int, must be positive)
        height: Target height (int, must be positive)
    
    Returns:
        bool: True if successful, False if failed
    """
```

**Benefits**:
- Code is self-documenting
- IDE can provide better autocomplete
- Easier to catch type errors
- Clearer what function expects

### Getter Methods (Controlled Access)

```python
def get_current_image(self) -> Optional[np.ndarray]:
    """Get current image - controlled access to private data."""
    return self._current_image

def get_image_info(self) -> dict:
    """Get image metadata - only relevant info exposed."""
    return {
        'filename': Path(self._file_path).name if self._file_path else 'None',
        'dimensions': f"{width}×{height}" if image else None,
        'file_size': f"{size_kb} KB" if exists else None,
        'has_image': self._current_image is not None
    }
```

**Encapsulation Benefits**:
- Don't expose raw data
- Can change internal representation without breaking external code
- Can add validation/processing
- Can return copies instead of originals (immutability)

---

## 2. ImageDisplay Class

### Purpose
Handles visualization. Separates display concerns from processing.

### Constructor

```python
def __init__(self, parent_frame: tk.Widget, width: int = 800, height: int = 600):
    self._width = width           # Display dimensions
    self._height = height
    self._label = tk.Label(...)   # Tkinter display widget
    self._current_photo = None    # Holds PhotoImage reference
```

**Key Point**: ImageDisplay is responsible ONLY for display, not processing.

### Single Responsibility

```python
def display_image(self, cv_image: np.ndarray) -> None:
    """
    Display a CV2 image. Does ONLY display work:
    1. Convert color space (BGR → RGB)
    2. Convert format (numpy → PIL)
    3. Scale to fit
    4. Convert to PhotoImage
    5. Update GUI label
    """
    rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)
    pil_image.thumbnail((self._width, self._height), Image.Resampling.LANCZOS)
    self._current_photo = ImageTk.PhotoImage(pil_image)
    self._label.config(image=self._current_photo, text='')
```

**NOT the display's job**:
- Processing images
- Managing files
- Storing history
- Handling events

### Encapsulation

Display maintains its own state:
```python
def __init__(self, ...):
    self._label = tk.Label(...)           # GUI component
    self._current_photo = None            # Reference storage
    # These are PRIVATE - only display uses them
```

External code can't break display by messing with internals:
```python
# ❌ CAN'T DO THIS
display._label.destroy()
display._current_photo = something_weird

# ✅ MUST DO THIS
display.display_image(image)
display.show_message("Loading...")
```

---

## 3. ImageProcessingApp Class

### Purpose
Orchestrates everything. Coordinates between components.

### Composition Pattern

```python
class ImageProcessingApp:
    def __init__(self, root: tk.Tk):
        # COMPOSITION - contains other objects
        self._processor = ImageProcessor()     # Has-a processor
        self._display = ImageDisplay(...)      # Has-a display
        self._root = root                      # Tkinter root window
        
        # These objects are PRIVATE to this class
```

**NOT Inheritance**:
```python
# ❌ WRONG - inheritance doesn't make sense here
class ImageProcessingApp(ImageProcessor, ImageDisplay):
    # Why would app be a type of processor?
    # This violates the "is-a" vs "has-a" principle
    pass

# ✅ RIGHT - composition
class ImageProcessingApp:
    def __init__(self):
        self._processor = ImageProcessor()
        self._display = ImageDisplay()
```

### Delegation

App delegates work to specialized components:

```python
def _apply_grayscale(self) -> None:
    """Convert image to grayscale."""
    # 1. Delegate processing to ImageProcessor
    if self._processor.to_grayscale():
        # 2. Get result from processor
        image = self._processor.get_current_image()
        # 3. Delegate display to ImageDisplay
        self._display.display_image(image)
        # 4. Update UI feedback
        self._update_status("Grayscale applied")
    else:
        messagebox.showwarning("Warning", "No image loaded")
```

**Flow of Responsibility**:
1. User clicks button
2. App's event handler calls `_apply_grayscale()`
3. App asks ImageProcessor to process
4. App asks ImageDisplay to show result
5. App updates UI feedback
6. User sees result

**Separation of Concerns**:
- App doesn't do processing (processor does)
- App doesn't do display (display does)
- App coordinates the workflow

### Event Binding

```python
def _setup_menu(self) -> None:
    """Create menu - each item has a command."""
    file_menu.add_command(label="Open", command=self._open_image)
    edit_menu.add_command(label="Undo", command=self._undo)
    
    # Keyboard shortcuts
    self._root.bind('<Control-o>', lambda e: self._open_image())
    self._root.bind('<Control-z>', lambda e: self._undo())
```

**Event Handling Chain**:
1. User presses Ctrl+Z
2. Tkinter calls the lambda function
3. Lambda calls `self._undo()`
4. `_undo()` delegates to `self._processor.undo()`
5. Result is displayed

### State Management

App maintains UI state:
```python
def __init__(self, root: tk.Tk):
    # Slider states
    self._blur_var = tk.IntVar(value=5)
    self._brightness_var = tk.IntVar(value=0)
    self._contrast_var = tk.DoubleVar(value=1.0)
    
    # Resize input states
    self._width_var = tk.StringVar(value="800")
    self._height_var = tk.StringVar(value="600")
```

These are separate from processor state - they're UI state, not image state.

---

## OOP Principles in Action

### 1. Encapsulation

**Definition**: Hiding internal details, exposing only necessary interface.

**In this code**:
```python
class ImageProcessor:
    # PRIVATE - hidden from outside
    def _save_to_history(self):
        """Internal use only."""
        pass
    
    # PUBLIC - visible interface
    def undo(self):
        """External interface for undo."""
        pass
```

**Benefits**:
- Can change `_save_to_history()` without breaking external code
- Can't accidentally corrupt history from outside
- Clear API (public methods)

### 2. Abstraction

**Definition**: Hiding complexity, showing simple interface.

**In this code**:
```python
# Complex: Convert color space, format, scale, create PhotoImage
# Simple interface:
display.display_image(image)

# Complex: Find edges, apply threshold, format output
# Simple interface:
processor.edge_detection()
```

Users don't need to know HOW, just WHAT methods are available.

### 3. Single Responsibility Principle

**Definition**: Each class has one reason to change.

**In this code**:
```python
# ImageProcessor changes if: image processing algorithms change
class ImageProcessor:
    pass

# ImageDisplay changes if: display technology changes
class ImageDisplay:
    pass

# ImageProcessingApp changes if: workflow changes
class ImageProcessingApp:
    pass
```

This makes code:
- Easier to understand
- Easier to test
- Easier to modify
- Reusable

### 4. Dependency Injection

**Definition**: Pass dependencies into objects, don't create internally.

**In this code**:
```python
class ImageDisplay:
    def __init__(self, parent_frame: tk.Widget, ...):
        # Receives parent frame as dependency
        self._label = tk.Label(parent_frame, ...)
        # Doesn't create parent - it's provided

class ImageProcessingApp:
    def __init__(self, root: tk.Tk):
        # Receives root window as dependency
        self._root = root
        # Doesn't create root - it's provided
```

**Benefits**:
- Objects are more testable
- Can swap implementations
- Clearer what each object needs

### 5. Composition Over Inheritance

**Definition**: Prefer "has-a" relationships over "is-a" relationships.

**In this code**:
```python
# ✅ COMPOSITION
class ImageProcessingApp:
    def __init__(self):
        self._processor = ImageProcessor()    # has-a
        self._display = ImageDisplay()        # has-a

# Instead of:
# ❌ INHERITANCE
class ImageProcessingApp(ImageProcessor, ImageDisplay):
    # is-a processor AND display
    # Doesn't make semantic sense
```

---

## Method Documentation

### Type Hints

```python
def resize_image(self, width: int, height: int) -> bool:
    """
    Parameters must be documented and typed:
    
    Args:
        width: Target image width in pixels (must be positive)
        height: Target image height in pixels (must be positive)
    
    Returns:
        bool: True if resize successful, False if image not loaded
    
    Raises:
        None: Returns False instead of raising exceptions
    """
```

### Docstring Format

```python
def apply_blur(self, intensity: int) -> bool:
    """
    Brief one-liner description.
    
    More detailed explanation if needed.
    Explain what it does, not how it does it.
    
    Args:
        intensity: Blur strength from 1 to 50. Higher = more blur.
    
    Returns:
        True if successful, False if no image loaded.
    """
```

---

## Testing the OOP Design

### How to verify good OOP design:

**1. Can you use a class independently?**
```python
# Yes - ImageProcessor works without GUI
processor = ImageProcessor()
processor.load_image("photo.jpg")
processor.to_grayscale()
processor.save_image("result.jpg")
# No GUI needed!
```

**2. Can you swap implementations?**
```python
# If we want to change how images display:
class BetterImageDisplay:
    # Different implementation
    def display_image(self, image):
        pass

# We only change one line in ImageProcessingApp:
self._display = BetterImageDisplay(...)  # Instead of ImageDisplay
# Rest of code still works!
```

**3. Is each class testable?**
```python
# Yes - can test each independently
def test_processor():
    p = ImageProcessor()
    p.load_image("test.jpg")
    assert p.get_current_image() is not None
    
def test_display():
    frame = tk.Frame()
    d = ImageDisplay(frame)
    d.display_image(test_image)
    # Verify display worked
```

---

## Key Takeaways

| Principle | How Used | Benefit |
|-----------|----------|---------|
| **Encapsulation** | Private `_` attributes, public methods | Control access, change internals safely |
| **Constructor** | `__init__` initializes state | Objects start valid, no undefined behavior |
| **Methods** | Single responsibility per method | Reusable, testable, maintainable |
| **Composition** | App contains Processor and Display | Flexible, easier than inheritance |
| **Abstraction** | Public interface hides complexity | Simple to use, easy to learn |
| **Type Hints** | Annotate parameters and returns | Self-documenting, fewer bugs |
| **Documentation** | Docstrings explain what, not how | Clear API, easier maintenance |

---

## Real-World Application

This architecture could easily be:
- **Extended**: Add new filters by adding methods to ImageProcessor
- **Tested**: Unit test each class independently
- **Reused**: Use ImageProcessor in other apps (web, mobile, batch)
- **Maintained**: Change implementation without changing interface
- **Documented**: Clear roles and responsibilities

This is how professional software is built!
