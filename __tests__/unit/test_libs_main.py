"""Unit tests for libs/main.py"""

import os
import shutil
import tempfile
from pathlib import Path

import piexif
import pytest
from PIL import Image

from libs.main import (
    HEIF_SUPPORTED,
    _extract_date_data,
    _is_heic,
    _load_exif_from_heic,
    transfer_gps_data_batch,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def samples_dir():
    """Get the samples directory path"""
    return Path(__file__).parent.parent.parent / "samples"


@pytest.fixture
def source_jpg_with_gps(samples_dir):
    """Path to JPEG source file with GPS data"""
    return str(samples_dir / "exif.jpg")


@pytest.fixture
def source_heic_with_gps(samples_dir):
    """Path to HEIC source file with GPS data"""
    return str(samples_dir / "exif.HEIC")


@pytest.fixture
def target_jpg_without_gps(samples_dir):
    """Path to JPEG target file without GPS data"""
    return str(samples_dir / "3ad41821-4905-4580-b82d-12f707a91512.jpg")


class TestIsHeic:
    """Test _is_heic helper function"""

    def test_lowercase_heic(self):
        """Test lowercase .heic extension detection"""
        assert _is_heic("photo.heic") is True

    def test_uppercase_heic(self):
        """Test uppercase .HEIC extension detection"""
        assert _is_heic("photo.HEIC") is True

    def test_lowercase_heif(self):
        """Test lowercase .heif extension detection"""
        assert _is_heic("photo.heif") is True

    def test_uppercase_heif(self):
        """Test uppercase .HEIF extension detection"""
        assert _is_heic("photo.HEIF") is True

    def test_jpg_not_heic(self):
        """Test that JPG files are not detected as HEIC"""
        assert _is_heic("photo.jpg") is False

    def test_jpeg_not_heic(self):
        """Test that JPEG files are not detected as HEIC"""
        assert _is_heic("photo.JPEG") is False

    def test_png_not_heic(self):
        """Test that PNG files are not detected as HEIC"""
        assert _is_heic("photo.png") is False


class TestExtractDateData:
    """Test _extract_date_data helper function"""

    def test_extract_date_from_exif(self, source_jpg_with_gps):
        """Test extracting date data from EXIF"""
        exif_dict = piexif.load(source_jpg_with_gps)
        date_data = _extract_date_data(exif_dict)

        # Should return dict with relevant date tags
        assert date_data is not None
        assert isinstance(date_data, dict)

    def test_extract_date_no_date_returns_none(self):
        """Test that extracting date from empty EXIF returns None"""
        empty_exif = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        date_data = _extract_date_data(empty_exif)
        assert date_data is None


class TestLoadExifFromHeic:
    """Test HEIC EXIF loading"""

    @pytest.mark.skipif(not HEIF_SUPPORTED, reason="HEIC support not available")
    def test_load_exif_from_heic(self, source_heic_with_gps):
        """Test loading EXIF from HEIC file"""
        exif_dict = _load_exif_from_heic(source_heic_with_gps)

        assert exif_dict is not None
        assert isinstance(exif_dict, dict)
        # Should have GPS data
        assert "GPS" in exif_dict
        assert exif_dict["GPS"]


class TestTransferGpsDataBatch:
    """Test main GPS transfer function"""

    def test_transfer_jpg_to_jpg(
        self, source_jpg_with_gps, target_jpg_without_gps, temp_dir
    ):
        """Test transferring GPS from JPG to JPG"""
        # Copy target to temp dir
        target_copy = os.path.join(temp_dir, "target.jpg")
        shutil.copy(target_jpg_without_gps, target_copy)

        # Transfer GPS
        results = transfer_gps_data_batch(source_jpg_with_gps, [target_copy])

        # Verify results
        assert results["success_count"] == 1
        assert len(results["failed"]) == 0
        assert "Successfully processed" in results["message"]

        # Verify GPS data was written
        target_exif = piexif.load(target_copy)
        assert "GPS" in target_exif
        assert target_exif["GPS"]

    def test_transfer_jpg_to_jpg_uppercase(
        self, source_jpg_with_gps, target_jpg_without_gps, temp_dir
    ):
        """Test transferring GPS to JPG with uppercase extension"""
        # Copy target to temp dir with uppercase extension
        target_copy = os.path.join(temp_dir, "target.JPG")
        shutil.copy(target_jpg_without_gps, target_copy)

        # Transfer GPS
        results = transfer_gps_data_batch(source_jpg_with_gps, [target_copy])

        # Verify results
        assert results["success_count"] == 1
        assert len(results["failed"]) == 0

    @pytest.mark.skipif(not HEIF_SUPPORTED, reason="HEIC support not available")
    def test_transfer_heic_to_jpg(
        self, source_heic_with_gps, target_jpg_without_gps, temp_dir
    ):
        """Test transferring GPS from HEIC to JPG"""
        # Copy target to temp dir
        target_copy = os.path.join(temp_dir, "target.jpg")
        shutil.copy(target_jpg_without_gps, target_copy)

        # Transfer GPS
        results = transfer_gps_data_batch(source_heic_with_gps, [target_copy])

        # Verify results
        assert results["success_count"] == 1
        assert len(results["failed"]) == 0

        # Verify GPS data was written
        target_exif = piexif.load(target_copy)
        assert "GPS" in target_exif
        assert target_exif["GPS"]

    def test_transfer_multiple_targets(
        self, source_jpg_with_gps, samples_dir, temp_dir
    ):
        """Test transferring GPS to multiple target files"""
        # Copy multiple targets to temp dir
        target_files = [
            "3ad41821-4905-4580-b82d-12f707a91512.jpg",
            "40e2855b-639e-48d8-b8ba-b17252cf303e.jpg",
            "5dc952ea-6f8c-4a2c-ab57-182697ef3de0.jpg",
        ]

        target_copies = []
        for fname in target_files:
            src = samples_dir / fname
            dst = os.path.join(temp_dir, fname)
            shutil.copy(src, dst)
            target_copies.append(dst)

        # Transfer GPS
        results = transfer_gps_data_batch(source_jpg_with_gps, target_copies)

        # Verify results
        assert results["success_count"] == 3
        assert len(results["failed"]) == 0

        # Verify all files have GPS data
        for target in target_copies:
            target_exif = piexif.load(target)
            assert "GPS" in target_exif
            assert target_exif["GPS"]

    def test_source_without_gps(self, target_jpg_without_gps, temp_dir):
        """Test error handling when source has no GPS data"""
        # Use a target file as source (no GPS)
        target_copy = os.path.join(temp_dir, "target.jpg")
        shutil.copy(target_jpg_without_gps, target_copy)

        results = transfer_gps_data_batch(target_jpg_without_gps, [target_copy])

        # Should fail with appropriate message
        assert results["success_count"] == 0
        assert "no GPS data" in results["message"]

    def test_invalid_source_file(self, target_jpg_without_gps):
        """Test error handling with invalid source file"""
        results = transfer_gps_data_batch(
            "/nonexistent/file.jpg", [target_jpg_without_gps]
        )

        # Should fail gracefully
        assert results["success_count"] == 0
        assert "Error" in results["message"]

    def test_progress_callback(
        self, source_jpg_with_gps, target_jpg_without_gps, temp_dir, mocker
    ):
        """Test that progress callback is called during transfer"""
        # Copy target to temp dir
        target_copy = os.path.join(temp_dir, "target.jpg")
        shutil.copy(target_jpg_without_gps, target_copy)

        # Create mock callback
        callback = mocker.MagicMock()

        # Transfer GPS with callback
        results = transfer_gps_data_batch(
            source_jpg_with_gps, [target_copy], progress_callback=callback
        )

        # Verify callback was called
        assert callback.called
        assert callback.call_count >= 2  # At least start and end

    def test_skip_existing_gps_when_overwrite_false(
        self, source_jpg_with_gps, temp_dir
    ):
        """Test skipping files that already have GPS when overwrite=False"""
        # Copy source to temp dir (it has GPS already)
        target_copy = os.path.join(temp_dir, "target_with_gps.jpg")
        shutil.copy(source_jpg_with_gps, target_copy)

        # Transfer with overwrite=False
        options = {"overwrite_gps": False}
        results = transfer_gps_data_batch(
            source_jpg_with_gps, [target_copy], options=options
        )

        # Should skip the file
        assert results["skipped"] == 1
        assert results["success_count"] == 0

    def test_copy_date_option(
        self, source_jpg_with_gps, target_jpg_without_gps, temp_dir
    ):
        """Test copying date metadata with copy_date option"""
        # Copy target to temp dir
        target_copy = os.path.join(temp_dir, "target.jpg")
        shutil.copy(target_jpg_without_gps, target_copy)

        # Get source date data
        source_exif = piexif.load(source_jpg_with_gps)
        source_date_original = source_exif["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
        source_date_digitized = source_exif["Exif"].get(
            piexif.ExifIFD.DateTimeDigitized
        )
        source_datetime = source_exif["0th"].get(piexif.ImageIFD.DateTime)

        # Transfer with copy_date=True
        options = {"copy_date": True}
        results = transfer_gps_data_batch(
            source_jpg_with_gps, [target_copy], options=options
        )

        # Verify results
        assert results["success_count"] == 1

        # Verify date data was copied correctly
        target_exif = piexif.load(target_copy)

        # Check DateTimeOriginal matches
        if source_date_original:
            assert (
                target_exif["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
                == source_date_original
            )

        # Check DateTimeDigitized matches
        if source_date_digitized:
            assert (
                target_exif["Exif"].get(piexif.ExifIFD.DateTimeDigitized)
                == source_date_digitized
            )

        # Check DateTime matches
        if source_datetime:
            assert target_exif["0th"].get(piexif.ImageIFD.DateTime) == source_datetime

        # Check timezone offset tags are copied
        for offset_tag in [
            36880,
            36881,
            36882,
        ]:  # OffsetTime, OffsetTimeOriginal, OffsetTimeDigitized
            if offset_tag in source_exif.get("Exif", {}):
                assert (
                    target_exif["Exif"].get(offset_tag)
                    == source_exif["Exif"][offset_tag]
                ), f"Timezone offset tag {offset_tag} not copied correctly"
