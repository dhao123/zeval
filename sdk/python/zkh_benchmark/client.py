"""
HTTP Client for ZKH Benchmark API.
"""
import os
from typing import Optional, Dict, Any
import requests
from urllib.parse import urljoin

from .exceptions import AuthenticationError, ZKHBenchmarkError


class ZKHBenchmarkClient:
    """ZKH Benchmark API Client.
    
    Args:
        api_key: API key for authentication. If not provided, will look for
                ZKH_API_KEY environment variable.
        base_url: Base URL for the API. Defaults to production URL.
        timeout: Request timeout in seconds. Defaults to 30.
    
    Example:
        >>> client = ZKHBenchmarkClient(api_key="your-api-key")
        >>> info = client.get_dataset_info("单承口管箍", "training")
    """
    
    DEFAULT_BASE_URL = "http://localhost:8000/api/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        self.api_key = api_key or os.getenv("ZKH_API_KEY")
        self.base_url = base_url or os.getenv(
            "ZKH_BASE_URL", 
            self.DEFAULT_BASE_URL
        )
        self.timeout = timeout
        
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": f"zkh-benchmark-python/0.1.0"
        })
        
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request."""
        url = urljoin(self.base_url + "/", endpoint)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            
            # Check for API error
            data = response.json()
            if isinstance(data, dict) and data.get("code") != 0:
                raise ZKHBenchmarkError(
                    data.get("message", "Unknown API error")
                )
            
            return data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid or expired API key")
            raise ZKHBenchmarkError(f"HTTP Error: {e}")
        except requests.exceptions.RequestException as e:
            raise ZKHBenchmarkError(f"Request failed: {e}")
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make GET request."""
        return self._request("GET", endpoint, params=params)
    
    def post(
        self,
        endpoint: str,
        json: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make POST request."""
        return self._request("POST", endpoint, json=json)
    
    def download(
        self,
        endpoint: str,
        output_path: str,
        params: Optional[Dict] = None,
        progress_callback=None
    ) -> None:
        """Download file with progress tracking."""
        url = urljoin(self.base_url + "/", endpoint)
        
        try:
            response = self.session.get(
                url,
                params=params,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
                            
        except requests.exceptions.RequestException as e:
            raise DownloadError(f"Download failed: {e}")
    
    def get_dataset_info(
        self,
        category: str,
        pool_type: str = "both"
    ) -> Dict[str, Any]:
        """Get dataset metadata.
        
        Args:
            category: Category L4 name (e.g., "单承口管箍")
            pool_type: Pool type - "training", "evaluation", or "both"
        
        Returns:
            Dataset metadata including versions, sizes, and formats.
        """
        params = {
            "category_l4": category,
            "pool_type": pool_type
        }
        response = self.get("datasets/info", params=params)
        return response.get("data", {})
    
    def list_categories(self, level: int = 4) -> list:
        """List available categories.
        
        Args:
            level: Category level (1-4). Defaults to 4.
        
        Returns:
            List of category names.
        """
        response = self.get(f"categories/l{level}-options")
        return response.get("data", [])
    
    def list_versions(self, category: str) -> list:
        """List available versions for a category.
        
        Args:
            category: Category L4 name
            
        Returns:
            List of version dictionaries with version, release_date, changelog, is_latest
        """
        params = {"category_l4": category}
        response = self.get("datasets/versions", params=params)
        return response.get("data", {}).get("versions", [])
