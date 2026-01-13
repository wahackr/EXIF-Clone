# GPS Metadata Transfer Tool

A simple GUI application for transferring GPS EXIF data from one photo to multiple target photos. Perfect for batch updating location metadata across multiple images.

## Features

- 🗺️ Transfer GPS coordinates from source image to multiple target images
- 📸 Support for multiple image formats: JPEG, PNG, TIFF, HEIC/HEIF
- 💼 Case-insensitive file extension support (e.g., `.jpg`, `.JPG`)
- 🖥️ Clean and intuitive GUI built with CustomTkinter
- ✅ Batch processing with error handling and progress reporting
- 🍎 Full support for Apple HEIC format (iPhone photos)

## Installation

### Prerequisites

- Python 3.8 or higher
- uv (recommended) or pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd EXIF-Clone
```

2. Install dependencies:

**Using uv (recommended):**
```bash
uv pip install -r requirements.txt
```

**Using pip:**
```bash
pip install -r requirements.txt
```

### Dependencies

- `customtkinter` - Modern GUI framework
- `piexif` - EXIF data manipulation
- `Pillow` - Image processing
- `pillow-heif` - HEIC/HEIF format support

## Usage

### Running the Application

**From Source:**
```bash
uv run python src/app.py
```

Or with standard Python:
```bash
python src/app.py
```

**Standalone Binary:**

If you have a pre-built binary, simply run:
```bash
# Linux
./EXIF-Clone

# Windows
EXIF-Clone.exe
```

### How to Use

1. **Select Source Photo**: Click "Choose Source" and select an image that contains GPS metadata
2. **Select Target Photos**: Click "Choose Targets" and select one or more images you want to add GPS data to
3. **Transfer GPS Data**: Click "Transfer GPS Data" to copy the GPS coordinates from the source to all target images

The application will display:
- Success message with the number of files processed
- Partial success if some files fail
- Error messages if the source has no GPS data or processing fails

## Supported Formats

- **JPEG** (`.jpg`, `.jpeg`, `.JPG`, `.JPEG`)
- **PNG** (`.png`, `.PNG`)
- **TIFF** (`.tiff`, `.TIFF`)
- **HEIC/HEIF** (`.heic`, `.heif`, `.HEIC`, `.HEIF`) - Apple's format

## Project Structure

```
EXIF-Clone/
├── src/
│   ├── app.py              # Application entry point
│   ├── ui/
│   │   └── main.py         # GUI layer (CustomTkinter)
│   └── libs/
│       └── main.py         # Business logic (EXIF processing)
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Project configuration
└── README.md              # This file
```

## Architecture

The project follows a clean separation of concerns:

- **UI Layer** (`src/ui/main.py`): Handles user interactions, file dialogs, and display updates
- **Business Logic** (`src/libs/main.py`): Pure functions for GPS EXIF data transfer, no UI dependencies
- **Entry Point** (`src/app.py`): Initializes and runs the application

This architecture makes the business logic:
- Testable without GUI dependencies
- Reusable in CLI or API applications
- Easy to maintain and extend

## Building Standalone Binaries

You can build standalone executables that run without Python installed.

### Prerequisites for Building

**Linux:**
```bash
# Install Tk library (required for GUI)
sudo apt install tk8.6

# Install PyInstaller
uv pip install pyinstaller
```

**Windows:**
```cmd
# Install PyInstaller
uv pip install pyinstaller
```

### Build Instructions

**Both Linux and Windows:**
```bash
# Build using the spec file (recommended)
uv run pyinstaller EXIF-Clone.spec --clean
```

Or build from scratch:
```bash
# Linux
uv run pyinstaller --onefile --paths ./src --name EXIF-Clone ./src/app.py

# Windows
uv run pyinstaller --onefile --paths ./src --name EXIF-Clone ./src/app.py
```

### Output

- **Linux**: `dist/EXIF-Clone` (~30MB)
- **Windows**: `dist/EXIF-Clone.exe` (~35-40MB)

### Distribution Notes

**Linux:**
- The binary is self-contained but requires system libraries: `libtk8.6` and `libtcl8.6`
- Users can install with: `sudo apt install tk8.6`

**Windows:**
- The `.exe` is fully self-contained
- No additional dependencies needed
- No console window appears (GUI-only mode)

## Technical Details

### GPS Data Transfer Process

1. Load EXIF data from source image
2. Extract GPS metadata
3. For each target image:
   - Load existing EXIF data
   - Inject GPS metadata
   - Save updated EXIF data back to the file

### HEIC Support

HEIC files are handled specially:
- Uses `pillow-heif` to register HEIC opener with Pillow
- Extracts and injects EXIF data through PIL's image interface
- Preserves all existing EXIF data while updating GPS fields

## Troubleshooting

**HEIC files not working:**
- Ensure `pillow-heif` is installed: `pip install pillow-heif`

**No GPS data found:**
- Verify the source image actually contains GPS metadata
- Some cameras and phones don't record location by default

**Permission errors:**
- Ensure you have write permissions for the target files
- On macOS, you may need to grant location permissions to Terminal/Python

## License

[Add your license here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.