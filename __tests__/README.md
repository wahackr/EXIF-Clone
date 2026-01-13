# Tests for EXIF-Clone

This directory contains comprehensive unit and integration tests for the EXIF-Clone GPS metadata transfer tool.

## Test Structure

```
__tests__/
├── unit/
│   └── test_libs_main.py      # Unit tests for business logic
└── integration/
    └── test_workflow.py        # Integration tests for complete workflows
```

## Test Coverage

### Unit Tests (`test_libs_main.py`)

Tests individual functions and components:

- **File Type Detection**
  - ✅ Lowercase extensions (.heic, .heif, .jpg)
  - ✅ Uppercase extensions (.HEIC, .HEIF, .JPG)
  - ✅ Mixed case handling

- **EXIF Operations**
  - ✅ Loading EXIF from JPEG
  - ✅ Loading EXIF from HEIC
  - ✅ Extracting date metadata
  - ✅ GPS data extraction

- **GPS Transfer Logic**
  - ✅ JPG to JPG transfer
  - ✅ HEIC to JPG transfer
  - ✅ Multiple target files
  - ✅ Progress callbacks
  - ✅ Error handling (no GPS, invalid files)
  - ✅ Skip existing GPS option
  - ✅ Copy date metadata option

### Integration Tests (`test_workflow.py`)

Tests complete end-to-end workflows:

- **Real-World Scenarios**
  - ✅ Batch processing multiple photos
  - ✅ Mixed file types (JPEG, HEIC)
  - ✅ Files with/without existing EXIF
  - ✅ Uppercase/lowercase extensions
  - ✅ Partial failures with error reporting

- **Workflow Tests**
  - ✅ JPG with GPS → Multiple JPGs without GPS
  - ✅ HEIC with GPS → JPG without GPS
  - ✅ Files without any EXIF data
  - ✅ Overwrite vs. skip existing GPS
  - ✅ Progress tracking through callbacks

## Test Data

Tests use real sample files from the `samples/` directory:

- `exif.jpg` - JPEG file with GPS EXIF data (source)
- `exif.HEIC` - HEIC file with GPS EXIF data (source, uppercase extension)
- `3ad41821-*.jpg` - JPEG files without GPS (targets)
- `40e2855b-*.jpg` - JPEG files without GPS (targets)
- `5dc952ea-*.jpg` - JPEG files without GPS (targets)

## Running Tests

### Install Test Dependencies

```bash
uv pip install -r requirements.txt
```

Or with pip:
```bash
pip install pytest pytest-mock pytest-cov
```

### Run All Tests

```bash
pytest
```

Or using the test runner:
```bash
python run_tests.py all
```

### Run Unit Tests Only

```bash
pytest __tests__/unit/
```

Or:
```bash
python run_tests.py unit
```

### Run Integration Tests Only

```bash
pytest __tests__/integration/
```

Or:
```bash
python run_tests.py integration
```

### Run with Verbose Output

```bash
pytest -vv
```

### Run with Coverage Report

```bash
pytest --cov=src --cov-report=term-missing --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`

### Run Specific Test File

```bash
pytest __tests__/unit/test_libs_main.py
```

### Run Specific Test Class

```bash
pytest __tests__/unit/test_libs_main.py::TestIsHeic
```

### Run Specific Test Method

```bash
pytest __tests__/unit/test_libs_main.py::TestIsHeic::test_uppercase_heic
```

## Test Requirements

### Required

- `pytest` - Testing framework
- `pytest-mock` - Mocking support with MockFixture
- `pytest-cov` - Coverage reporting

### Optional

- `pillow-heif` - For HEIC tests (tests will skip if not available)

## Test Fixtures

The tests use pytest fixtures for common setup:

- `temp_dir` - Temporary directory for test files (auto-cleanup)
- `samples_dir` - Path to samples directory
- `source_jpg_with_gps` - Path to JPEG source with GPS
- `source_heic_with_gps` - Path to HEIC source with GPS
- `target_jpg_without_gps` - Path to JPEG target without GPS

## Mocking with pytest-mock

Tests use `pytest-mock` (MockFixture) for mocking:

```python
def test_progress_callback(self, source_jpg_with_gps, target_jpg_without_gps, temp_dir, mocker):
    # Create mock callback using mocker fixture
    callback = mocker.MagicMock()
    
    # Use the mock in your test
    transfer_gps_data_batch(source, targets, progress_callback=callback)
    
    # Verify mock was called correctly
    assert callback.called
    assert callback.call_count >= 2
```

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=src --cov-report=xml
```

## Test Markers

Tests can be marked for selective running:

```python
@pytest.mark.skipif(not HEIF_SUPPORTED, reason="HEIC support not available")
def test_heic_feature():
    # Test code
```

## Troubleshooting

**Tests fail with import errors:**
- Ensure you're in the project root directory
- Run: `export PYTHONPATH="${PYTHONPATH}:${PWD}/src"`

**HEIC tests skipped:**
- Install pillow-heif: `pip install pillow-heif`

**Sample files not found:**
- Ensure `samples/` directory exists in project root
- Verify sample files are present

## Contributing

When adding new features:

1. Add unit tests for individual functions
2. Add integration tests for complete workflows
3. Ensure all tests pass before submitting PR
4. Aim for >80% code coverage
