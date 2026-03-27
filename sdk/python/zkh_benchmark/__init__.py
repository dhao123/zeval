"""
ZKH Benchmark Python SDK

A Python SDK for downloading datasets from ZKH Benchmark Platform.

Example:
    >>> from zkh_benchmark import Dataset
    >>> 
    >>> # Download training set
    >>> Dataset.download(
    ...     category="单承口管箍",
    ...     pool_type="training",
    ...     output_dir="./data"
    ... )
    >>> 
    >>> # Download evaluation set
    >>> Dataset.download(
    ...     category="球阀",
    ...     pool_type="evaluation",
    ...     format="parquet",
    ...     output_dir="./eval_data"
    ... )
"""

__version__ = "0.1.0"
__author__ = "ZKH AI Team"

from .client import ZKHBenchmarkClient
from .dataset import Dataset
from .exceptions import (
    ZKHBenchmarkError,
    AuthenticationError,
    DatasetNotFoundError,
    DownloadError,
)

__all__ = [
    "ZKHBenchmarkClient",
    "Dataset",
    "ZKHBenchmarkError",
    "AuthenticationError",
    "DatasetNotFoundError",
    "DownloadError",
]
