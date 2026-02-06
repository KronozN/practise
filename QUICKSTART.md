# Quick Start Guide - Image Processing Studio

## 🚀 Installation (5 minutes)

### Option 1: Windows
```batch
# Open Command Prompt and navigate to the project folder
cd path\to\image-processing-studio

# Install dependencies
pip install -r requirements.txt

# Run the application
python image_processor.py
```

### Option 2: Mac/Linux
```bash
# Open Terminal and navigate to the project folder
cd path/to/image-processing-studio

# Install dependencies
pip3 install -r requirements.txt

# Run the application
python3 image_processor.py
```

## ✅ Verify Installation

If you see a window titled "Image Processing Studio" with a dark theme and a message "Open an image to get started", your installation is successful!

## 📖 First Steps

### 1. Open an Image
- Click **File** → **Open** (or press `Ctrl+O`)
- Navigate to any image file (JPG, PNG, or BMP)
- Click **Open**

### 2. Try a Simple Filter
- Once image loads, click the **Grayscale** button
- You'll see the image convert to black and white
- Watch the status bar show "Grayscale applied"

### 3. Undo Your Change
- Press `Ctrl+Z` to undo
- Image returns to original color

### 4. Try Interactive Adjustments
- Find the **Blur Intensity** slider on the right panel
- Drag it left and right to see real-time blur effect
- Notice the preview updates instantly

### 5. Save Your Work
- Press `Ctrl+S` to save over the original, OR
- Click **File** → **Save As** to save with a new name
- Choose your format (PNG recommended for quality)

## 🎨 Common Workflows

### Make a Black & White Photo
1. Open image (`Ctrl+O`)
2. Click **Grayscale**
3. Adjust **Brightness** if needed
4. Adjust **Contrast** for more punch
5. Save (`Ctrl+S`)

### Create an Artistic Effect
1. Open image
2. Click **Edge Detection** to find contours
3. Can also adjust **Blur** before edge detection for smoother edges
4. Save result

### Fix a Dark Photo
1. Open image
2. Use **Brightness** slider to lighten
3. Use **Contrast** slider to enhance details
4. Save

### Create a Thumbnail
1. Open image
2. Enter new dimensions in **Resize** section
   - Width: 400
   - Height: 300
3. Click **Apply Resize**
4. Save with new name

## 🎯 Tips & Tricks

### Real-Time Preview
- All sliders update the image in real-time
- No need to click buttons for slider adjustments
- Click buttons for instant effects

### Undo/Redo
- You can undo/redo an unlimited number of times
- Perfect for experimenting without fear
- Press `Ctrl+Z` and `Ctrl+Y` repeatedly

### Reset Everything
- Made too many changes? Click **Edit** → **Reset to Original**
- Returns image to exactly how it was when opened
- Clears entire edit history

### Image Information
- Look at status bar (bottom of window)
- Shows current filename, dimensions, and last operation
- Helps track what you've done

### Keyboard Shortcuts
```
Ctrl+O  → Open image
Ctrl+S  → Save image
Ctrl+Z  → Undo
Ctrl+Y  → Redo
Ctrl+Q  → Exit application
```

## 🐛 Troubleshooting

### "ImportError: No module named 'cv2'"
```bash
# Reinstall OpenCV
pip install --upgrade opencv-python
```

### Application window appears blank
- Wait a moment for it to load
- Try opening an image file
- Check your image format (use JPG or PNG)

### Image processing is slow
- Try with a smaller image first
- Larger images take longer to process
- This is normal behavior

### Can't open my image file
- Check file format - must be JPG, PNG, or BMP
- Try opening with Windows Preview first to verify it's not corrupted
- Check file is not in use by another program

## 📚 Understanding the Code

The application uses **three main classes**:

### ImageProcessor
- Handles all image processing operations
- Manages undo/redo history
- Private data members for encapsulation

### ImageDisplay
- Manages display of images in the GUI
- Converts between OpenCV and Tkinter formats
- Single responsibility: display only

### ImageProcessingApp
- Main application window
- Coordinates between components
- Handles user interactions

## 🎓 Learning Resources

This project teaches:
- **Object-Oriented Programming**: How classes work together
- **GUI Development**: Building desktop applications with Tkinter
- **Image Processing**: Real-world OpenCV operations
- **Design Patterns**: How professional code is organized

Perfect for beginners learning programming concepts!

## 🚀 Next Steps

### Try Experimenting With
- Combining multiple filters
- Finding the best brightness/contrast combination for your images
- Using undo/redo to test different approaches
- Batch processing: open → modify → save multiple images

### Want to Add Features?
See the README.md file for guidance on extending the application with new filters!

---

**Got stuck?** Check the README.md file for detailed documentation.
