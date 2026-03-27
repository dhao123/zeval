"""
Dataset download functionality.
"""
import os
import time
from typing import Optional, Callable
from pathlib import Path

from .client import ZKHBenchmarkClient
from .exceptions import DatasetNotFoundError, DownloadError


class Dataset:
    """Dataset download utilities.
    
    This class provides static methods for downloading datasets
    from the ZKH Benchmark Platform.
    
    Example:
        >>> from zkh_benchmark import Dataset
        >>> 
        >>> # Download with default settings
        >>> Dataset.download("单承口管箍", "training")
        >>> 
        >>> # Download with custom settings
        >>> Dataset.download(
        ...     category="球阀",
        ...     pool_type="evaluation",
        ...     format="parquet",
        ...     version="v1.0.0",
        ...     output_dir="./my_data"
        ... )
    """
    
    @staticmethod
    def download(
        category: str,
        pool_type: str,
        output_dir: str = "./data",
        format: str = "json",
        version: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        show_progress: bool = True
    ) -> str:
        """Download a dataset.
        
        Args:
            category: Category L4 name (e.g., "单承口管箍", "球阀")
            pool_type: Type of dataset - "training" or "evaluation"
            output_dir: Directory to save the downloaded file
            format: File format - "json", "csv", or "parquet"
            version: Specific version to download. If None, downloads latest.
            api_key: API key for authentication
            base_url: Base URL for the API
            show_progress: Whether to show download progress
        
        Returns:
            Path to the downloaded file
        
        Raises:
            DatasetNotFoundError: If dataset is not found
            DownloadError: If download fails
            ValueError: If invalid parameters are provided
        """
        # Validate parameters
        if pool_type not in ("training", "evaluation"):
            raise ValueError(f"Invalid pool_type: {pool_type}. Use 'training' or 'evaluation'")
        
        if format not in ("json", "csv", "parquet"):
            raise ValueError(f"Invalid format: {format}. Use 'json', 'csv', or 'parquet'")
        
        # Create client
        client = ZKHBenchmarkClient(api_key=api_key, base_url=base_url)
        
        # Get dataset info
        info = client.get_dataset_info(category, pool_type)
        if not info:
            raise DatasetNotFoundError(f"Dataset not found: {category}/{pool_type}")
        
        # Determine version
        version = version or info.get("latest_version", "v1.0.0")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Build filename
        filename = f"{category}_{pool_type}_{version}.{format}"
        filepath = output_path / filename
        
        # Download
        params = {
            "category_l4": category,
            "pool_type": pool_type,
            "format": format,
            "version": version
        }
        
        if show_progress:
            print(f"Downloading {category} {pool_type} dataset...")
            print(f"Version: {version}, Format: {format}")
            
            progress_bar = ProgressBar()
            
            def callback(progress):
                progress_bar.update(progress)
            
            client.download("datasets/download", str(filepath), params, callback)
            progress_bar.finish()
        else:
            client.download("datasets/download", str(filepath), params)
        
        print(f"Downloaded to: {filepath}")
        return str(filepath)
    
    @staticmethod
    def download_async(
        category: str,
        pool_type: str,
        output_dir: str = "./data",
        format: str = "json",
        version: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        poll_interval: int = 5
    ) -> str:
        """Download large dataset using async export.
        
        For datasets larger than 100MB, this method creates an async
        export task and waits for completion.
        
        Args:
            category: Category L4 name
            pool_type: Type of dataset - "training" or "evaluation"
            output_dir: Directory to save the downloaded file
            format: File format - "json", "csv", or "parquet"
            version: Specific version to download
            api_key: API key for authentication
            base_url: Base URL for the API
            poll_interval: Seconds between status checks
        
        Returns:
            Path to the downloaded file
        """
        client = ZKHBenchmarkClient(api_key=api_key, base_url=base_url)
        
        # Create export task
        print(f"Creating export task for {category} {pool_type}...")
        response = client.post("datasets/export", json={
            "category_l4": category,
            "pool_type": pool_type,
            "format": format,
            "version": version
        })
        
        task_id = response.get("data", {}).get("task_id")
        if not task_id:
            raise DownloadError("Failed to create export task")
        
        print(f"Export task created: {task_id}")
        print("Waiting for completion...")
        
        # Poll for completion
        while True:
            time.sleep(poll_interval)
            
            status_response = client.get(f"datasets/export/{task_id}/status")
            status_data = status_response.get("data", {})
            
            status = status_data.get("status")
            progress = status_data.get("progress", 0)
            
            print(f"Progress: {progress}%", end="\r")
            
            if status == "completed":
                print("\nExport completed!")
                break
            elif status == "failed":
                error = status_data.get("error_message", "Unknown error")
                raise DownloadError(f"Export failed: {error}")
        
        # Download the file
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        version = version or "latest"
        filename = f"{category}_{pool_type}_{version}.{format}"
        filepath = output_path / filename
        
        print(f"Downloading exported file...")
        client.download(f"datasets/export/{task_id}/download", str(filepath))
        
        print(f"Downloaded to: {filepath}")
        return str(filepath)
    
    @staticmethod
    def list_categories(level: int = 4, **kwargs) -> list:
        """List available categories.
        
        Args:
            level: Category level (1-4)
            **kwargs: Additional arguments for client initialization
        
        Returns:
            List of category dictionaries
        """
        client = ZKHBenchmarkClient(**kwargs)
        return client.list_categories(level)
    
    @staticmethod
    def versions(category: str, **kwargs) -> list:
        """List available versions for a category.
        
        Args:
            category: Category L4 name
            **kwargs: Additional arguments for client initialization
            
        Returns:
            List of version dictionaries
        """
        client = ZKHBenchmarkClient(**kwargs)
        return client.list_versions(category)
    
    @staticmethod
    def info(category: str, pool_type: str = "both", **kwargs) -> dict:
        """Get dataset information.
        
        Args:
            category: Category L4 name
            pool_type: Type of dataset
            **kwargs: Additional arguments for client initialization
        
        Returns:
            Dataset metadata dictionary
        """
        client = ZKHBenchmarkClient(**kwargs)
        return client.get_dataset_info(category, pool_type)
    
    @staticmethod
    def smart_download(
        category: str,
        pool_type: str,
        output_dir: str = "./data",
        format: str = "json",
        version: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        show_progress: bool = True
    ) -> str:
        """Smart download: auto-detect file size and choose best method.
        
        For small files (<100MB): Direct download
        For large files (>=100MB): Async export
        For Parquet format: Always async export
        
        Args:
            category: Category L4 name
            pool_type: Type of dataset - "training" or "evaluation"
            output_dir: Directory to save the downloaded file
            format: File format - "json", "csv", or "parquet"
            version: Specific version to download
            api_key: API key for authentication
            base_url: Base URL for the API
            show_progress: Whether to show download progress
            
        Returns:
            Path to the downloaded file
        """
        client = ZKHBenchmarkClient(api_key=api_key, base_url=base_url)
        
        # Get dataset info
        info = client.get_dataset_info(category, pool_type)
        pool_info = info.get("pools", {}).get(pool_type, {})
        estimated_size = pool_info.get("file_size", 0)
        
        # Parquet always uses async
        if format == "parquet":
            if show_progress:
                print(f"Parquet format detected, using async export...")
            return Dataset.download_async(
                category, pool_type, output_dir, format, version,
                api_key, base_url
            )
        
        # Large files use async
        if estimated_size > 100 * 1024 * 1024:
            if show_progress:
                size_mb = estimated_size / (1024 * 1024)
                print(f"Large file detected ({size_mb:.1f}MB), using async export...")
            return Dataset.download_async(
                category, pool_type, output_dir, format, version,
                api_key, base_url
            )
        
        # Small files use direct download
        return Dataset.download(
            category, pool_type, output_dir, format, version,
            api_key, base_url, show_progress
        )


class ProgressBar:
    """Simple progress bar for CLI output."""
    
    def __init__(self, width: int = 40):
        self.width = width
        self.last_progress = -1
    
    def update(self, progress: float):
        """Update progress bar."""
        progress = int(progress)
        if progress == self.last_progress:
            return
        
        self.last_progress = progress
        filled = int(self.width * progress / 100)
        bar = "█" * filled + "░" * (self.width - filled)
        print(f"\r|{bar}| {progress}%", end="", flush=True)
    
    def finish(self):
        """Finish progress bar."""
        self.update(100)
        print()  # New line
