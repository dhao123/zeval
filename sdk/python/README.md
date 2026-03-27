# ZKH Benchmark Python SDK

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Python SDK and CLI tool for downloading datasets from ZKH Benchmark Platform.

## Features

- 🚀 **Easy Download**: Simple API for downloading training and evaluation datasets
- 📦 **Multiple Formats**: Support for JSON, CSV, and Parquet formats
- 🔄 **Async Export**: Handle large files (>100MB) with async export tasks
- 💻 **CLI Tool**: Command-line interface for automation and scripting
- 📊 **Progress Tracking**: Visual progress bars for downloads
- 🔐 **Authentication**: Secure API key-based authentication

## Installation

```bash
pip install zkh-benchmark
```

## Quick Start

### Python SDK

```python
from zkh_benchmark import Dataset

# Download training set (includes Input + GT)
Dataset.download(
    category="单承口管箍",
    pool_type="training",
    output_dir="./training_data"
)

# Download evaluation set (Input only, no GT)
Dataset.download(
    category="球阀",
    pool_type="evaluation",
    format="parquet",
    output_dir="./eval_data"
)
```

### CLI Tool

```bash
# Configure API key
export ZKH_API_KEY="your-api-key"

# List available categories
zkh-benchmark list categories

# Download a dataset
zkh-benchmark download \
  --category "单承口管箍" \
  --pool training \
  --format json \
  --output ./data

# Download multiple datasets
zkh-benchmark download-batch 单承口管箍 球阀 UPVC管 --pool training
```

## Authentication

You can authenticate using one of the following methods:

1. **Environment Variable** (recommended):
   ```bash
   export ZKH_API_KEY="your-api-key"
   ```

2. **Configuration File**:
   ```bash
   zkh-benchmark config set-api-key your-api-key
   ```

3. **Pass directly in code**:
   ```python
   Dataset.download(
       category="单承口管箍",
       pool_type="training",
       api_key="your-api-key"
   )
   ```

## API Reference

### Dataset.download()

Download a dataset.

```python
Dataset.download(
    category: str,           # Category L4 name (e.g., "单承口管箍")
    pool_type: str,          # "training" or "evaluation"
    output_dir: str = "./data",  # Output directory
    format: str = "json",    # "json", "csv", or "parquet"
    version: str = None,     # Specific version, default: latest
    api_key: str = None,     # API key
    base_url: str = None,    # API base URL
    show_progress: bool = True   # Show progress bar
)
```

### Dataset.download_async()

Download large dataset using async export (for files > 100MB).

```python
Dataset.download_async(
    category: str,
    pool_type: str,
    output_dir: str = "./data",
    format: str = "json",
    version: str = None,
    poll_interval: int = 5   # Seconds between status checks
)
```

### Dataset.info()

Get dataset metadata.

```python
info = Dataset.info("单承口管箍", "training")
print(info["record_count"])  # Number of records
print(info["file_size"])     # File size in bytes
print(info["fields"])        # Available fields
```

## CLI Reference

### Commands

| Command | Description |
|---------|-------------|
| `zkh-benchmark config set-api-key` | Set API key |
| `zkh-benchmark config show` | Show configuration |
| `zkh-benchmark list categories` | List available categories |
| `zkh-benchmark info` | Show dataset information |
| `zkh-benchmark download` | Download a dataset |
| `zkh-benchmark download-batch` | Download multiple datasets |

### Examples

```bash
# Show dataset info
zkh-benchmark info --category "单承口管箍" --pool training

# Download with specific version
zkh-benchmark download \
  --category "球阀" \
  --pool evaluation \
  --version v1.0.0 \
  --format csv

# Download large file with async export
zkh-benchmark download \
  --category "UPVC管" \
  --pool training \
  --async

# Batch download
zkh-benchmark download-batch \
  单承口管箍 球阀 UPVC管 铜接头 \
  --pool both \
  --format parquet \
  --output ./all_datasets
```

## Dataset Formats

### Training Set (JSON)
```json
{
  "metadata": {
    "category": "单承口管箍",
    "pool_type": "training",
    "version": "v1.0.0",
    "record_count": 10000,
    "fields": ["id", "input", "gt", "category_l1", "category_l2", "category_l3", "category_l4"]
  },
  "data": [
    {
      "id": "dp_abc123",
      "input": "单承口管箍 DN50...",
      "gt": {
        "材质": "UPVC",
        "规格": "DN50"
      },
      "category_l1": "建材",
      "category_l2": "管材管件",
      "category_l3": "塑料管材",
      "category_l4": "UPVC管"
    }
  ]
}
```

### Evaluation Set (JSON)
```json
{
  "metadata": {
    "category": "单承口管箍",
    "pool_type": "evaluation",
    "note": "GT字段已移除，用于公平评测"
  },
  "data": [
    {
      "id": "dp_def456",
      "input": "单承口管箍 DN50...",
      "category_l1": "建材",
      "category_l2": "管材管件",
      "category_l3": "塑料管材",
      "category_l4": "UPVC管"
    }
  ]
}
```

## Error Handling

```python
from zkh_benchmark import Dataset
from zkh_benchmark.exceptions import (
    AuthenticationError,
    DatasetNotFoundError,
    DownloadError
)

try:
    Dataset.download(category="单承口管箍", pool_type="training")
except AuthenticationError:
    print("Invalid API key")
except DatasetNotFoundError:
    print("Dataset not found")
except DownloadError as e:
    print(f"Download failed: {e}")
```

## Advanced Usage

### Custom Progress Callback

```python
def my_progress(progress):
    print(f"Downloaded: {progress:.1f}%")

Dataset.download(
    category="单承口管箍",
    pool_type="training",
    show_progress=True
)
```

### Using Client Directly

```python
from zkh_benchmark import ZKHBenchmarkClient

client = ZKHBenchmarkClient(api_key="your-key")

# Get dataset info
info = client.get_dataset_info("单承口管箍", "training")

# List categories
categories = client.list_categories(level=4)
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please visit our [GitHub Issues](https://github.com/zkh360/benchmark-sdk/issues) page.

---

**ZKH Benchmark** - Empowering AI evaluation with quality industrial datasets.
