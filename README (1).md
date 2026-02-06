# Image Processing Studio

A professional desktop application for image manipulation and processing, built with Python, Tkinter, and OpenCV. This project demonstrates object-oriented programming principles, modern GUI design, and practical image processing techniques.

## Features

### Image Processing
- **Grayscale Conversion** - Convert images to black and white
- **Blur Effect** - Apply Gaussian blur with adjustable intensity (1-50)
- **Edge Detection** - Canny edge detection algorithm
- **Brightness Adjustment** - Increase/decrease brightness (-100 to +100)
- **Contrast Adjustment** - Adjust contrast levels (0.5x to 3.0x)
- **Rotation** - Rotate image by 90°, 180°, or 270°
- **Flip** - Flip horizontally or vertically
- **Resize/Scale** - Manually adjust image dimensions

### File Operations
- Open image files (JPG, PNG, BMP)
- Save processed images
- Save As with file format selection
- File format support for JPG, PNG, and BMP

### Edit Operations
- Undo/Redo functionality with full history
- Reset to original image
- Keyboard shortcuts (Ctrl+Z, Ctrl+Y, etc.)

## Architecture & OOP Principles

### Class Structure

#### 1. **ImageProcessor** (Image Processing Engine)
Encapsulates all image processing operations with strong encapsulation.

**Key Features:**
- Private attributes for image data (`_original_image`, `_current_image`)
- History management for undo/redo functionality
- Separation of concerns: handles only image operations

**Methods:**
- `load_image()` - Load images from disk
- `save_image()` - Save processed images
- `to_grayscale()` - Grayscale conversion
- `apply_blur()` - Gaussian blur with adjustable intensity
- `edge_detection()` - Canny edge detection
- `adjust_brightness()` - Brightness adjustment
- `adjust_contrast()` - Contrast adjustment
- `rotate_image()` - Rotation operations
- `flip_image()` - Flip transformations
- `resize_image()` - Image resizing
- `undo()` / `redo()` - History management

**OOP Principles Demonstrated:**
- **Encapsulation**: Private data members with controlled access
- **Constructor**: `__init__` initializes state properly
- **Methods**: Well-defined, single-responsibility methods
- **Getter/Setter Pattern**: `get_current_image()`, `get_image_info()`

#### 2. **ImageDisplay** (GUI Display Component)
Manages image visualization in the Tkinter interface.

**Key Features:**
- Handles conversion from OpenCV to PIL format
- Automatic scaling to fit display area
- Maintains aspect ratio

**Methods:**
- `display_image()` - Display CV2 images with proper conversion
- `show_message()` - Display status messages

**OOP Principles Demonstrated:**
- **Encapsulation**: Internal image state management
- **Single Responsibility**: Only handles display concerns
- **Composition**: Used by main application

#### 3. **ImageProcessingApp** (Main Application)
Orchestrates all components and manages user interface.

**Key Features:**
- Complete GUI layout management
- Event handling and user interactions
- Component coordination (composition pattern)
- State management

**Methods:**
- `_setup_menu()` - Menu bar creation
- `_setup_control_panel()` - Control interface
- `_setup_status_bar()` - Status information
- Event handlers for all operations
- File dialogs and user interactions

**OOP Principles Demonstrated:**
- **Composition**: Uses ImageProcessor and ImageDisplay
- **Delegation**: Delegates work to specialized classes
- **Class Interaction**: Coordinates between components
- **Constructor Pattern**: Proper initialization chain

### Design Patterns Used

1. **Model-View-Controller (MVC)**
   - Model: `ImageProcessor` (business logic)
   - View: `ImageDisplay` (presentation)
   - Controller: `ImageProcessingApp` (orchestration)

2. **Composition Pattern**
   - Main app composes `ImageProcessor` and `ImageDisplay`
   - Each class has a specific responsibility

3. **History Pattern**
   - Stack-based undo/redo implementation
   - State preservation for editing operations

4. **Builder Pattern**
   - UI components built methodically in setup methods

## Installation

### Requirements
- Python 3.8 or higher
- pip (Python package manager)

### Dependencies
```bash
pip install opencv-python pillow numpy
```

### Step-by-Step Setup

1. **Clone or download the project**
   ```bash
   cd image-processing-studio
   ```

2. **Install dependencies**
   ```bash
   pip install opencv-python pillow numpy
   ```

3. **Run the application**
   ```bash
   python image_processor.py
   ```

## Usage Guide

### Opening an Image
1. Click **File → Open** or press `Ctrl+O`
2. Select an image file (JPG, PNG, or BMP)
3. Image will appear in the main display area

### Applying Filters

#### Grayscale
- Click the **Grayscale** button
- Image converts to black and white

#### Blur Effect
- Use the **Blur Intensity** slider (1-50)
- Slider updates in real-time
- Higher values = more blur

#### Edge Detection
- Click **Edge Detection** button
- Uses Canny algorithm to find edges

#### Brightness & Contrast
- **Brightness** slider: -100 to +100
- **Contrast** slider: 0.5x to 3.0x
- Adjustments are real-time

### Transformations

#### Rotation
- Click **90°**, **180°**, or **270°**
- Rotates clockwise by specified angle

#### Flip
- **Horizontal**: Mirror left-right
- **Vertical**: Mirror top-bottom

#### Resize
- Enter desired width and height in pixel values
- Click **Apply Resize**
- New dimensions must be positive integers

### Saving Your Work

#### Save
- Press `Ctrl+S` to save over original
- Click **File → Save**

#### Save As
- Click **File → Save As...**
- Choose location and format
- Supports JPG, PNG, BMP

### Undo/Redo Operations
- **Undo**: `Ctrl+Z` or **Edit → Undo**
- **Redo**: `Ctrl+Y` or **Edit → Redo**
- **Reset**: **Edit → Reset to Original** (reverts all changes)

### Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open image |
| `Ctrl+S` | Save image |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+Q` | Exit application |

## Code Quality Features

### Encapsulation
- Private attributes with leading underscore (`_`)
- Controlled access through methods
- Data hiding and protection

### Documentation
- Comprehensive docstrings for all classes
- Method documentation with parameter descriptions
- Type hints throughout codebase

### Error Handling
- File operation error handling
- Validation of user inputs
- Graceful error messages
- User feedback with message boxes

### Maintainability
- Clear separation of concerns
- Single responsibility principle
- Reusable components
- Well-organized code structure

## Technical Specifications

### Image Processing
- **Library**: OpenCV (cv2)
- **Formats**: BGR color space (OpenCV standard)
- **Operations**: All in-place processing with history
- **Memory**: Efficient image copying for undo/redo

### GUI Framework
- **Library**: Tkinter (built-in Python)
- **Display**: PIL/Pillow for image conversion
- **Theme**: Modern dark theme with accent colors
- **Layout**: Responsive with scrollable controls

### File Support
- **Read**: JPG, JPEG, PNG, BMP
- **Write**: JPG, PNG, BMP
- **Memory**: Up to application/system limits

## Example Workflow

1. **Open Image**
   - File → Open → Select sample.jpg

2. **Apply Filters**
   - Convert to grayscale
   - Apply blur (intensity: 15)
   - Adjust brightness (+30)

3. **Transform**
   - Rotate 90°
   - Flip horizontally

4. **Edit Adjustments**
   - Undo blur
   - Apply contrast (1.5x)

5. **Save Results**
   - File → Save As
   - Save as "result.png"

## Troubleshooting

### Image won't open
- Ensure file format is supported (JPG, PNG, BMP)
- Check file isn't corrupted
- Verify sufficient disk space

### UI scaling issues
- Application is optimized for 1280×720 minimum
- Larger screens will scale proportionally
- Try adjusting window size manually

### Memory issues with large images
- OpenCV processes full images in memory
- Very large images (>50MB) may be slow
- Consider resizing before processing

### Performance optimization
- Slider operations recalculate from original
- This ensures smooth, artifact-free adjustments
- Trade-off between performance and quality

## Development & Extension

### Adding New Filters

To add a new image processing filter:

1. **Add method to ImageProcessor class**
   ```python
   def apply_new_filter(self, param: type) -> bool:
       if self._current_image is None:
           return False
       
       self._save_to_history()
       # Processing code here
       self._current_image = processed_image
       return True
   ```

2. **Add UI control in ImageProcessingApp**
   ```python
   self._add_button(scrollable_frame, "New Filter", self._apply_new_filter)
   ```

3. **Implement handler method**
   ```python
   def _apply_new_filter(self) -> None:
       if self._processor.apply_new_filter(param):
           self._display.display_image(self._processor.get_current_image())
           self._update_status("Filter applied")
   ```

### Extending the Application

**Ideas for enhancement:**
- Batch processing multiple images
- Custom color adjustments (HSV, RGB)
- Histogram equalization
- Image cropping with selection tool
- Filter presets/favorites
- Before/after comparison view
- Batch export options
- Plugin system for third-party filters

## License

This project is provided as-is for educational purposes.

## Author Notes

This application demonstrates:
- **Object-Oriented Design**: Three-class hierarchy with clear responsibilities
- **Design Patterns**: MVC, Composition, History pattern
- **Professional Practices**: Documentation, error handling, user feedback
- **GUI Development**: Responsive layout, modern styling, user-friendly controls
- **Image Processing**: Real-time effects with efficient memory management

Perfect for students learning OOP, GUI development, and image processing techniques.

---

**Version**: 1.0  
**Last Updated**: 2024  
**Python**: 3.8+  
**Status**: Complete and Production-Ready
