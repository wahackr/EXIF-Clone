"""Integration tests for the complete GPS transfer workflow"""

import os
import shutil
import tempfile
from pathlib import Path

import piexif
import pytest

from libs.main import HEIF_SUPPORTED, transfer_gps_data_batch


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


class TestEndToEndWorkflow:
    """Integration tests for complete workflows"""

    def test_jpg_with_gps_to_multiple_jpg_without_gps(self, samples_dir, temp_dir):
        """
        Integration test: Transfer GPS from JPG with GPS to multiple JPGs without GPS
        """
        # Arrange: Setup source and targets
        source = str(samples_dir / "exif.jpg")

        target_files = [
            "3ad41821-4905-4580-b82d-12f707a91512.jpg",
            "40e2855b-639e-48d8-b8ba-b17252cf303e.jpg",
            "5dc952ea-6f8c-4a2c-ab57-182697ef3de0.jpg",
        ]

        # Copy targets to temp directory
        targets = []
        for fname in target_files:
            src_path = samples_dir / fname
            dst_path = os.path.join(temp_dir, fname)
            shutil.copy(src_path, dst_path)
            targets.append(dst_path)

        # Get source GPS data for verification
        source_exif = piexif.load(source)
        source_gps = source_exif["GPS"]

        # Act: Transfer GPS data
        results = transfer_gps_data_batch(source, targets)

        # Assert: Verify results
        assert results["success_count"] == 3
        assert len(results["failed"]) == 0
        assert results["skipped"] == 0
        assert "Successfully processed 3 file(s)" in results["message"]

        # Verify each target now has GPS data
        for target in targets:
            target_exif = piexif.load(target)
            assert "GPS" in target_exif
            assert target_exif["GPS"]

            # Verify GPS data matches source
            assert (
                target_exif["GPS"][piexif.GPSIFD.GPSLatitude]
                == source_gps[piexif.GPSIFD.GPSLatitude]
            )
            assert (
                target_exif["GPS"][piexif.GPSIFD.GPSLongitude]
                == source_gps[piexif.GPSIFD.GPSLongitude]
            )

    @pytest.mark.skipif(not HEIF_SUPPORTED, reason="HEIC support not available")
    def test_heic_with_gps_to_jpg_without_gps(self, samples_dir, temp_dir):
        """
        Integration test: Transfer GPS from HEIC with GPS to JPG without GPS
        """
        # Arrange
        source = str(samples_dir / "exif.HEIC")
        target_src = samples_dir / "3ad41821-4905-4580-b82d-12f707a91512.jpg"
        target = os.path.join(temp_dir, "target.jpg")
        shutil.copy(target_src, target)

        # Act
        results = transfer_gps_data_batch(source, [target])

        # Assert
        assert results["success_count"] == 1
        assert len(results["failed"]) == 0

        # Verify GPS was transferred
        target_exif = piexif.load(target)
        assert "GPS" in target_exif
        assert target_exif["GPS"]

    def test_uppercase_extension_handling(self, samples_dir, temp_dir):
        """
        Integration test: Handle files with uppercase extensions (.JPG)
        """
        # Arrange: Create file with uppercase extension
        source = str(samples_dir / "exif.jpg")
        target_src = samples_dir / "3ad41821-4905-4580-b82d-12f707a91512.jpg"
        target = os.path.join(temp_dir, "TARGET.JPG")
        shutil.copy(target_src, target)

        # Act
        results = transfer_gps_data_batch(source, [target])

        # Assert
        assert results["success_count"] == 1
        assert len(results["failed"]) == 0

        # Verify file with uppercase extension was processed
        assert os.path.exists(target)
        target_exif = piexif.load(target)
        assert "GPS" in target_exif

    def test_lowercase_extension_handling(self, samples_dir, temp_dir):
        """
        Integration test: Handle files with lowercase extensions (.jpg)
        """
        # Arrange
        source = str(samples_dir / "exif.jpg")
        target_src = samples_dir / "3ad41821-4905-4580-b82d-12f707a91512.jpg"
        target = os.path.join(temp_dir, "target.jpg")
        shutil.copy(target_src, target)

        # Act
        results = transfer_gps_data_batch(source, [target])

        # Assert
        assert results["success_count"] == 1
        assert len(results["failed"]) == 0

    def test_mixed_case_extensions(self, samples_dir, temp_dir):
        """
        Integration test: Handle mix of upper and lowercase extensions
        """
        # Arrange
        source = str(samples_dir / "exif.jpg")

        targets = []
        for i, ext in enumerate([".jpg", ".JPG", ".Jpg"]):
            target_src = samples_dir / "3ad41821-4905-4580-b82d-12f707a91512.jpg"
            target = os.path.join(temp_dir, f"target{i}{ext}")
            shutil.copy(target_src, target)
            targets.append(target)

        # Act
        results = transfer_gps_data_batch(source, targets)

        # Assert
        assert results["success_count"] == 3
        assert len(results["failed"]) == 0

        # Verify all were processed
        for target in targets:
            assert os.path.exists(target)
            target_exif = piexif.load(target)
            assert "GPS" in target_exif

    def test_file_without_exif_receives_gps(self, samples_dir, temp_dir):
        """
        Integration test: Transfer GPS to file that has no EXIF data at all
        """
        # Arrange: Create a simple image with no EXIF
        from PIL import Image

        source = str(samples_dir / "exif.jpg")
        target = os.path.join(temp_dir, "no_exif.jpg")

        # Create image without EXIF
        img = Image.new("RGB", (100, 100), color="red")
        img.save(target, "JPEG")

        # Verify it has no EXIF initially
        try:
            target_exif = piexif.load(target)
            assert not target_exif.get("GPS")  # No GPS initially
        except:
            pass  # May raise if no EXIF at all

        # Act
        results = transfer_gps_data_batch(source, [target])

        # Assert
        assert results["success_count"] == 1
        assert len(results["failed"]) == 0

        # Verify GPS was added
        target_exif = piexif.load(target)
        assert "GPS" in target_exif
        assert target_exif["GPS"]

    def test_partial_failure_with_mixed_targets(self, samples_dir, temp_dir):
        """
        Integration test: Handle scenario with some valid and some invalid targets
        """
        # Arrange
        source = str(samples_dir / "exif.jpg")

        # Valid target
        valid_target = os.path.join(temp_dir, "valid.jpg")
        shutil.copy(
            samples_dir / "3ad41821-4905-4580-b82d-12f707a91512.jpg", valid_target
        )

        # Invalid target (doesn't exist)
        invalid_target = os.path.join(temp_dir, "nonexistent.jpg")

        targets = [valid_target, invalid_target]

        # Act
        results = transfer_gps_data_batch(source, targets)

        # Assert
        assert results["success_count"] == 1
        assert len(results["failed"]) == 1
        assert results["failed"][0]["file"] == invalid_target
        assert "Processed 1/2 files" in results["message"]

    def test_overwrite_existing_gps_default(self, samples_dir, temp_dir):
        """
        Integration test: By default, overwrite existing GPS data
        """
        # Arrange: Use a file that already has GPS as target
        source = str(samples_dir / "exif.jpg")
        target = os.path.join(temp_dir, "already_has_gps.jpg")
        shutil.copy(source, target)

        # Act: Transfer (should overwrite by default)
        results = transfer_gps_data_batch(source, [target])

        # Assert: Should have been processed (overwritten)
        assert results["success_count"] == 1
        assert results["skipped"] == 0

        # Verify GPS data matches source (was overwritten)
        source_exif = piexif.load(source)
        target_exif = piexif.load(target)
        assert (
            target_exif["GPS"][piexif.GPSIFD.GPSLatitude]
            == source_exif["GPS"][piexif.GPSIFD.GPSLatitude]
        )
        assert (
            target_exif["GPS"][piexif.GPSIFD.GPSLongitude]
            == source_exif["GPS"][piexif.GPSIFD.GPSLongitude]
        )

    def test_skip_existing_gps_when_disabled(self, samples_dir, temp_dir):
        """
        Integration test: Skip files with existing GPS when overwrite disabled
        """
        # Arrange
        source = str(samples_dir / "exif.jpg")
        target = os.path.join(temp_dir, "already_has_gps.jpg")
        shutil.copy(source, target)

        # Act: Transfer with overwrite disabled
        options = {"overwrite_gps": False}
        results = transfer_gps_data_batch(source, [target], options=options)

        # Assert: Should have been skipped
        assert results["success_count"] == 0
        assert results["skipped"] == 1

    @pytest.mark.skipif(not HEIF_SUPPORTED, reason="HEIC support not available")
    def test_uppercase_heic_extension(self, samples_dir, temp_dir):
        """
        Integration test: Handle HEIC files with uppercase extension
        """
        # Arrange
        source = str(samples_dir / "exif.HEIC")  # Already uppercase
        target_src = samples_dir / "3ad41821-4905-4580-b82d-12f707a91512.jpg"
        target = os.path.join(temp_dir, "target.jpg")
        shutil.copy(target_src, target)

        # Act
        results = transfer_gps_data_batch(source, [target])

        # Assert
        assert results["success_count"] == 1
        assert len(results["failed"]) == 0

    def test_progress_callback_integration(self, samples_dir, temp_dir, mocker):
        """
        Integration test: Verify progress callback works throughout the process
        """
        # Arrange
        source = str(samples_dir / "exif.jpg")
        targets = []
        for i in range(3):
            target = os.path.join(temp_dir, f"target{i}.jpg")
            shutil.copy(
                samples_dir / "3ad41821-4905-4580-b82d-12f707a91512.jpg", target
            )
            targets.append(target)

        # Create mock callback
        callback = mocker.MagicMock()

        # Act
        results = transfer_gps_data_batch(source, targets, progress_callback=callback)

        # Assert
        assert results["success_count"] == 3
        assert callback.call_count >= 4  # At least one per file plus final

        # Verify callback arguments
        for call in callback.call_args_list:
            args = call[0]
            assert len(args) == 3  # current, total, status
            assert isinstance(args[0], int)
            assert isinstance(args[1], int)
            assert isinstance(args[2], str)

    def test_real_world_scenario_batch_processing(self, samples_dir, temp_dir):
        """
        Integration test: Real-world scenario - batch process multiple photos from a photoshoot
        """
        # Arrange: Simulate a photographer's workflow
        # One photo has GPS (taken with phone), others don't (taken with camera)
        source = str(samples_dir / "exif.jpg")

        # Create multiple test files with different names
        targets = []
        for i, fname in enumerate(
            [
                "3ad41821-4905-4580-b82d-12f707a91512.jpg",
                "40e2855b-639e-48d8-b8ba-b17252cf303e.jpg",
                "5dc952ea-6f8c-4a2c-ab57-182697ef3de0.jpg",
            ]
        ):
            target = os.path.join(temp_dir, f"photoshoot_{i}.jpg")
            shutil.copy(samples_dir / fname, target)
            targets.append(target)

        # Act: Batch transfer GPS
        results = transfer_gps_data_batch(source, targets)

        # Assert: All photos should now have GPS
        assert results["success_count"] == len(targets)
        assert len(results["failed"]) == 0

        # Verify all images have identical GPS data
        source_exif = piexif.load(source)
        source_gps = source_exif["GPS"]

        for target in targets:
            target_exif = piexif.load(target)
            assert (
                target_exif["GPS"][piexif.GPSIFD.GPSLatitude]
                == source_gps[piexif.GPSIFD.GPSLatitude]
            )
            assert (
                target_exif["GPS"][piexif.GPSIFD.GPSLongitude]
                == source_gps[piexif.GPSIFD.GPSLongitude]
            )

    def test_backup_created_during_transfer(self, samples_dir, temp_dir):
        """
        Integration test: Verify backup files are created during GPS transfer
        """
        # Arrange
        source = str(samples_dir / "exif.jpg")
        target_src = samples_dir / "3ad41821-4905-4580-b82d-12f707a91512.jpg"
        target = os.path.join(temp_dir, "target.jpg")
        shutil.copy(target_src, target)

        # Act: Transfer GPS data
        results = transfer_gps_data_batch(source, [target])

        # Assert: Verify backup was created
        backup_path = f"{target}.backup"
        assert os.path.exists(backup_path), "Backup file should exist"

        # Verify original file was modified (has GPS now)
        target_exif = piexif.load(target)
        assert "GPS" in target_exif
        assert target_exif["GPS"]

        # Verify backup doesn't have GPS (original state)
        backup_exif = piexif.load(backup_path)
        assert not backup_exif.get("GPS"), "Backup should not have GPS data"

    def test_multiple_backups_created(self, samples_dir, temp_dir):
        """
        Integration test: Verify backups are created for multiple files
        """
        # Arrange
        source = str(samples_dir / "exif.jpg")
        targets = []
        for i in range(3):
            target = os.path.join(temp_dir, f"target{i}.jpg")
            shutil.copy(samples_dir / "3ad41821-4905-4580-b82d-12f707a91512.jpg", target)
            targets.append(target)

        # Act: Transfer GPS data
        results = transfer_gps_data_batch(source, targets)

        # Assert: Verify all backups were created
        for target in targets:
            backup_path = f"{target}.backup"
            assert os.path.exists(backup_path), f"Backup should exist for {target}"

        # Verify processing succeeded
        assert results["success_count"] == 3
