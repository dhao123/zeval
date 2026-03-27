"""
Exception classes for ZKH Benchmark SDK.
"""


class ZKHBenchmarkError(Exception):
    """Base exception for ZKH Benchmark SDK."""
    pass


class AuthenticationError(ZKHBenchmarkError):
    """Raised when authentication fails."""
    pass


class DatasetNotFoundError(ZKHBenchmarkError):
    """Raised when requested dataset is not found."""
    pass


class DownloadError(ZKHBenchmarkError):
    """Raised when download fails."""
    pass


class ExportError(ZKHBenchmarkError):
    """Raised when async export fails."""
    pass


class ValidationError(ZKHBenchmarkError):
    """Raised when input validation fails."""
    pass
