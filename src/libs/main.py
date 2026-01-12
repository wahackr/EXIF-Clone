"""Business logic for GPS EXIF data transfer"""

import os

import piexif
from PIL import Image

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIF_SUPPORTED = True
except ImportError:
    HEIF_SUPPORTED = False


def transfer_gps_data(source_path, target_paths):
    """
    Transfer GPS EXIF data from source image to target images.

    Args:
        source_path: Path to source image with GPS data
        target_paths: List of paths to target images

    Returns:
        dict: Results with success count and any errors
    """
    results = {
        "success_count": 0,
        "failed": [],
        "message": "",
    }

    try:
        # 1. Load GPS data from source image
        if _is_heic(source_path):
            if not HEIF_SUPPORTED:
                results["message"] = (
                    "Error: HEIC support not available. Install pillow-heif: pip install pillow-heif"
                )
                return results
            source_exif = _load_exif_from_heic(source_path)
        else:
            source_exif = piexif.load(source_path)

        gps_data = source_exif.get("GPS")

        if not gps_data:
            results["message"] = "Error: Source image has no GPS data!"
            return results

        # 2. Loop through targets and inject GPS data
        for target_path in target_paths:
            try:
                if _is_heic(target_path):
                    _write_exif_to_heic(target_path, gps_data)
                else:
                    target_exif = piexif.load(target_path)
                    target_exif["GPS"] = gps_data
                    exif_bytes = piexif.dump(target_exif)
                    piexif.insert(exif_bytes, target_path)
                results["success_count"] += 1
            except Exception as e:
                results["failed"].append({"file": target_path, "error": str(e)})

        # Build result message
        if results["success_count"] == len(target_paths):
            results["message"] = (
                f"Successfully processed {results['success_count']} file(s)"
            )
        elif results["success_count"] > 0:
            results["message"] = (
                f"Processed {results['success_count']}/{len(target_paths)} files ({len(results['failed'])} failed)"
            )
        else:
            results["message"] = "Failed to process any files"

    except Exception as e:
        results["message"] = f"Error loading source: {str(e)}"

    return results


def _is_heic(file_path):
    """Check if file is HEIC/HEIF format"""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in [".heic", ".heif"]


def _load_exif_from_heic(file_path):
    """Load EXIF data from HEIC file using PIL"""
    img = Image.open(file_path)
    exif_dict = piexif.load(img.info.get("exif", b""))
    return exif_dict


def _write_exif_to_heic(file_path, gps_data):
    """Write GPS EXIF data to HEIC file"""
    img = Image.open(file_path)

    # Load existing EXIF or create new
    existing_exif = img.info.get("exif", b"")
    if existing_exif:
        exif_dict = piexif.load(existing_exif)
    else:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    # Update GPS data
    exif_dict["GPS"] = gps_data
    exif_bytes = piexif.dump(exif_dict)

    # Save with new EXIF
    img.save(file_path, exif=exif_bytes)
