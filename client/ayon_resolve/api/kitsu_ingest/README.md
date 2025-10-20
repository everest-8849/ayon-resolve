# Kitsu Ingest Tool

A Python tool for ingesting video breakdown data from various formats (EDL, CSV) into Kitsu project management system.

## Features

- **Multiple Input Formats**: Supports EDL and CSV files
- **Video Processing**: Extract shots from video files based on metadata
- **Kitsu Integration**: Push sequences and shots directly to Kitsu
- **Preview Generation**: Create and upload preview videos for shots
- **Data Validation**: Verify metadata against local preview files

## Requirements

- Python 3.9+
- Virtual environment (recommended due to OpenTimelineIO dependencies)

## Installation

### Using Virtual Environment (Recommended)

Due to potential conflicts with the OpenTimelineIO library, it's strongly recommended to use a virtual environment:

```bash
# Create virtual environment
python -m venv kitsu_ingest_env

# Activate virtual environment
# On Windows:
kitsu_ingest_env\Scripts\activate
# On macOS/Linux:
source kitsu_ingest_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Using Conda (Alternative)

```bash
# Create conda environment
conda create -n kitsu_ingest python=3.11

# Activate environment
conda activate kitsu_ingest

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Commands

```bash
# Process metadata file locally
python -m kitsu_ingest -m path/to/metadata.edl --fps 25

# Process metadata and video together
python -m kitsu_ingest -m path/to/metadata.edl -v path/to/video.mp4 --fps 25

# Push to Kitsu project
python -m kitsu_ingest -m path/to/metadata.edl --push "PROJECT_NAME" --origin 8849

# Push existing processed folder
python -m kitsu_ingest --push_only path/to/processed/folder --push "PROJECT_NAME"
```

### Command Line Options

- `-m, --metadata`: Path to metadata file (.edl or .csv)
- `-v, --video`: Path to source video file
- `-p, --push`: Project name to push to Kitsu
- `--push_only`: Path to folder containing processed data
- `--fps`: Project frame rate (default: 25)
- `--origin`: Project originator (8849 or EVEREST)
- `--force`: Force publishing even if validation fails

## Supported Formats

### EDL Files
- CMX 3600 format
- Clip names should follow format: `SEQUENCE-SHOT`

### CSV Files
- Should contain columns for sequence, shot name, frame in/out
- Generated CSV files include Kitsu-compatible formatting

## Project Structure

```
kitsu_ingest/
├── kitsu_ingest/
│   ├── processors/          # File processors (EDL, CSV, Video)
│   ├── kitsu/              # Kitsu API integration
│   ├── models/             # Data models
│   └── config/             # Configuration settings
├── processed/              # Output directory for processed files
└── scripts/               # Utility scripts
```

## Workflow

1. **Process Metadata**: Parse EDL/CSV to extract shot information
2. **Generate Previews**: (Optional) Extract shot previews from video
3. **Validate Data**: Check metadata against local files
4. **Push to Kitsu**: Upload sequences, shots, and previews

## Troubleshooting

### Common Errors
- **File not found**: Check file paths and permissions
- **Kitsu connection**: Verify Kitsu server settings in config
- **Frame rate mismatch**: Ensure consistent FPS across metadata and video

## Configuration

Use a .venv (project root), used by the config class, needs:
- KITSU_EMAIL
- KITSU_PASSWORD
- KITSU_SERVER

## License

Developed at 8449 ༼ つ ◕_◕ ༽つ
