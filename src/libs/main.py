"""Business logic for GPS EXIF data transfer"""

import os
import shutil

import piexif
from PIL import Image

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIF_SUPPORTED = True
except ImportError:
    HEIF_SUPPORTED = False


def _should_skip_file(file_path, options):
    """
    Check if a file should be skipped (already has GPS and overwrite disabled).

    Args:
        file_path (str): Path to the file to check
        options (dict): Configuration options with 'overwrite_gps' boolean flag

    Returns:
        bool: True if file should be skipped, False otherwise
    """
    if options.get("overwrite_gps", True):
        return False  # Don't skip if overwrite is enabled

    try:
        if _is_heic(file_path):
            img = Image.open(file_path)
            existing_exif = img.info.get("exif", b"")
            if existing_exif:
                exif_dict = piexif.load(existing_exif)
            else:
                return False  # No EXIF, don't skip
        else:
            exif_dict = piexif.load(file_path)

        return bool(exif_dict.get("GPS"))  # Skip if has GPS
    except Exception:
        return False  # On error, don't skip


def _create_backup(file_path):
    """
    Create a backup of a file before modification.

    Args:
        file_path (str): Path to the file to backup

    Returns:
        str: Path to the backup file

    Raises:
        OSError: If backup creation fails due to permissions or disk space
    """
    backup_path = f"{file_path}.backup"
    try:
        shutil.copy2(file_path, backup_path)
    except (OSError, IOError) as e:
        raise OSError(f"Failed to create backup for {file_path}: {str(e)}")
    return backup_path


def transfer_gps_data_batch(
    source_path, target_paths, options=None, progress_callback=None
):
    """
    Transfer GPS EXIF data from source image to target images with progress reporting.

    Args:
        source_path: Path to source image with GPS data
        target_paths: List of paths to target images
        options: Dict with 'copy_date' and 'overwrite_gps' boolean flags
        progress_callback: Optional callback function(current, total, status) for progress updates

    Returns:
        dict: Results with success count and any errors
    """
    # Default options
    if options is None:
        options = {"copy_date": False, "overwrite_gps": True}

    results = {
        "success_count": 0,
        "skipped": 0,
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

        # Get creation date from source if needed
        date_data = None
        if options.get("copy_date", False):
            date_data = _extract_date_data(source_exif)

        # 2. Loop through targets and inject GPS data
        total = len(target_paths)
        for idx, target_path in enumerate(target_paths):
            try:
                # Update progress
                if progress_callback:
                    progress_callback(idx, total, f"({os.path.basename(target_path)})")

                # Check if file should be skipped (already has GPS)
                if _should_skip_file(target_path, options):
                    results["skipped"] += 1
                    continue

                # Create backup before modification
                _create_backup(target_path)

                if _is_heic(target_path):
                    skipped = _write_exif_to_heic(
                        target_path, gps_data, date_data, options
                    )
                else:
                    skipped = _write_exif_to_jpeg(
                        target_path, gps_data, date_data, options
                    )

                if skipped:
                    results["skipped"] += 1
                else:
                    results["success_count"] += 1
            except Exception as e:
                results["failed"].append({"file": target_path, "error": str(e)})

        # Final progress update
        if progress_callback:
            progress_callback(total, total, "")

        # Build result message
        total_attempted = len(target_paths) - results["skipped"]
        if results["success_count"] == total_attempted and results["skipped"] == 0:
            results["message"] = (
                f"Successfully processed {results['success_count']} file(s)"
            )
        elif results["success_count"] > 0:
            msg_parts = [
                f"Processed {results['success_count']}/{len(target_paths)} files"
            ]
            if results["skipped"] > 0:
                msg_parts.append(f"{results['skipped']} skipped")
            if len(results["failed"]) > 0:
                msg_parts.append(f"{len(results['failed'])} failed")
            results["message"] = (
                " (" + ", ".join(msg_parts[1:]) + ")"
                if len(msg_parts) > 1
                else msg_parts[0]
            )
            results["message"] = msg_parts[0] + (
                " (" + ", ".join(msg_parts[1:]) + ")" if len(msg_parts) > 1 else ""
            )
        else:
            if results["skipped"] == len(target_paths):
                results["message"] = (
                    f"All {results['skipped']} files skipped (already have GPS data)"
                )
            else:
                results["message"] = "Failed to process any files"

    except Exception as e:
        results["message"] = f"Error loading source: {str(e)}"

    return results


def transfer_gps_data(source_path, target_paths, options=None, progress_callback=None):
    """
    Transfer GPS EXIF data from source image to target images.

    Args:
        source_path: Path to source image with GPS data
        target_paths: List of paths to target images
        options: Dict with 'copy_date' and 'overwrite_gps' boolean flags
        progress_callback: Optional callback function(current, total, status) for progress updates

    Returns:
        dict: Results with success count and any errors
    """
    # Default options
    if options is None:
        options = {"copy_date": False, "overwrite_gps": True}

    results = {
        "success_count": 0,
        "skipped": 0,
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

        # Get creation date from source if needed
        date_data = None
        if options.get("copy_date", False):
            date_data = _extract_date_data(source_exif)

        # 2. Loop through targets and inject GPS data
        total = len(target_paths)
        for idx, target_path in enumerate(target_paths):
            try:
                # Update progress
                if progress_callback:
                    progress_callback(idx, total, f"({os.path.basename(target_path)})")

                # Check if file should be skipped (already has GPS)
                if _should_skip_file(target_path, options):
                    results["skipped"] += 1
                    continue

                # Create backup before modification
                _create_backup(target_path)

                if _is_heic(target_path):
                    skipped = _write_exif_to_heic(
                        target_path, gps_data, date_data, options
                    )
                else:
                    skipped = _write_exif_to_jpeg(
                        target_path, gps_data, date_data, options
                    )

                if skipped:
                    results["skipped"] += 1
                else:
                    results["success_count"] += 1
            except Exception as e:
                results["failed"].append({"file": target_path, "error": str(e)})

        # Final progress update
        if progress_callback:
            progress_callback(total, total, "")

        # Build result message
        total_attempted = len(target_paths) - results["skipped"]
        if results["success_count"] == total_attempted and results["skipped"] == 0:
            results["message"] = (
                f"Successfully processed {results['success_count']} file(s)"
            )
        elif results["success_count"] > 0:
            msg_parts = [
                f"Processed {results['success_count']}/{len(target_paths)} files"
            ]
            if results["skipped"] > 0:
                msg_parts.append(f"{results['skipped']} skipped")
            if len(results["failed"]) > 0:
                msg_parts.append(f"{len(results['failed'])} failed")
            results["message"] = (
                " (" + ", ".join(msg_parts[1:]) + ")"
                if len(msg_parts) > 1
                else msg_parts[0]
            )
            results["message"] = msg_parts[0] + (
                " (" + ", ".join(msg_parts[1:]) + ")" if len(msg_parts) > 1 else ""
            )
        else:
            if results["skipped"] == len(target_paths):
                results["message"] = (
                    f"All {results['skipped']} files skipped (already have GPS data)"
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


def _extract_date_data(exif_dict):
    """Extract date/time EXIF data from source including timezone offsets"""
    date_data = {}

    # Extract from Exif IFD
    if "Exif" in exif_dict:
        # DateTime tags
        for tag in [piexif.ExifIFD.DateTimeOriginal, piexif.ExifIFD.DateTimeDigitized]:
            if tag in exif_dict["Exif"]:
                date_data[tag] = exif_dict["Exif"][tag]

        # Timezone offset tags (EXIF 2.31)
        for tag in [
            36880,
            36881,
            36882,
        ]:  # OffsetTime, OffsetTimeOriginal, OffsetTimeDigitized
            if tag in exif_dict["Exif"]:
                date_data[tag] = exif_dict["Exif"][tag]

    # Extract from 0th IFD (DateTime)
    if "0th" in exif_dict and piexif.ImageIFD.DateTime in exif_dict["0th"]:
        date_data[piexif.ImageIFD.DateTime] = exif_dict["0th"][piexif.ImageIFD.DateTime]

    return date_data if date_data else None


def _apply_date_data(exif_dict, date_data):
    """Apply date/time data to target EXIF including timezone offsets"""
    if not date_data:
        return

    # Ensure Exif and 0th IFDs exist
    if "Exif" not in exif_dict:
        exif_dict["Exif"] = {}
    if "0th" not in exif_dict:
        exif_dict["0th"] = {}

    # Apply date tags
    for tag, value in date_data.items():
        if tag in [
            piexif.ExifIFD.DateTimeOriginal,
            piexif.ExifIFD.DateTimeDigitized,
            36880,
            36881,
            36882,
        ]:
            # DateTime, DateTimeDigitized, OffsetTime, OffsetTimeOriginal, OffsetTimeDigitized
            exif_dict["Exif"][tag] = value
        elif tag == piexif.ImageIFD.DateTime:
            exif_dict["0th"][tag] = value


def _write_exif_to_jpeg(file_path, gps_data, date_data=None, options=None):
    """Write GPS and date EXIF data to JPEG/PNG/TIFF file

    Returns:
        bool: True if skipped, False if written
    """
    if options is None:
        options = {"overwrite_gps": True}

    target_exif = piexif.load(file_path)

    # Check if target already has GPS and skip if needed
    if not options.get("overwrite_gps", True) and target_exif.get("GPS"):
        return True  # Skipped

    # Update GPS data
    target_exif["GPS"] = gps_data

    # Copy date data if option enabled
    if date_data:
        _apply_date_data(target_exif, date_data)

    # Write EXIF data back to file
    exif_bytes = piexif.dump(target_exif)
    piexif.insert(exif_bytes, file_path)

    return False  # Written successfully


def _write_exif_to_heic(file_path, gps_data, date_data=None, options=None):
    """Write GPS and date EXIF data to HEIC file

    Returns:
        bool: True if skipped, False if written
    """
    if options is None:
        options = {"overwrite_gps": True}

    img = Image.open(file_path)

    # Load existing EXIF or create new
    existing_exif = img.info.get("exif", b"")
    if existing_exif:
        exif_dict = piexif.load(existing_exif)
    else:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    # Check if target already has GPS and skip if needed
    if not options.get("overwrite_gps", True) and exif_dict.get("GPS"):
        return True  # Skipped

    # Update GPS data
    exif_dict["GPS"] = gps_data

    # Copy date data if provided
    if date_data:
        _apply_date_data(exif_dict, date_data)

    exif_bytes = piexif.dump(exif_dict)

    # Save with new EXIF
    img.save(file_path, exif=exif_bytes)

    return False  # Written successfully
