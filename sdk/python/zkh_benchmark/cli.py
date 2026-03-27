"""
Command Line Interface for ZKH Benchmark.

This module provides a CLI tool for downloading datasets from
ZKH Benchmark Platform, similar to Hugging Face's CLI.

Example:
    $ zkh-benchmark download --category "单承口管箍" --pool training
    $ zkh-benchmark list categories
    $ zkh-benchmark info --category "球阀"
"""
import os
import sys
from typing import Optional

import click

from . import __version__
from .client import ZKHBenchmarkClient
from .dataset import Dataset
from .exceptions import ZKHBenchmarkError


@click.group()
@click.version_option(version=__version__, prog_name="zkh-benchmark")
@click.option(
    "--api-key",
    envvar="ZKH_API_KEY",
    help="API key for authentication (or set ZKH_API_KEY env var)"
)
@click.option(
    "--base-url",
    envvar="ZKH_BASE_URL",
    default="http://localhost:8000/api/v1",
    help="Base URL for the API"
)
@click.pass_context
def cli(ctx, api_key: Optional[str], base_url: str):
    """ZKH Benchmark CLI - Download datasets for AI evaluation."""
    ctx.ensure_object(dict)
    ctx.obj["api_key"] = api_key
    ctx.obj["base_url"] = base_url


@cli.group()
def config():
    """Manage configuration."""
    pass


@config.command("set-api-key")
@click.argument("api_key")
def set_api_key(api_key: str):
    """Set API key in config file."""
    config_dir = os.path.expanduser("~/.zkh-benchmark")
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, "config")
    with open(config_file, "w") as f:
        f.write(f"ZKH_API_KEY={api_key}\n")
    
    click.echo("✓ API key saved to ~/.zkh-benchmark/config")


@config.command("show")
def show_config():
    """Show current configuration."""
    config_file = os.path.expanduser("~/.zkh-benchmark/config")
    
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            content = f.read()
        click.echo("Configuration file:")
        click.echo(content)
    else:
        click.echo("No configuration file found.")
    
    # Show env vars
    click.echo("\nEnvironment variables:")
    click.echo(f"  ZKH_API_KEY: {'set' if os.getenv('ZKH_API_KEY') else 'not set'}")
    click.echo(f"  ZKH_BASE_URL: {os.getenv('ZKH_BASE_URL', 'default')}")


@cli.group()
def list_cmd():
    """List available resources."""
    pass


@list_cmd.command("categories")
@click.option("--level", "-l", default=4, type=int, help="Category level (1-4)")
@click.pass_context
def list_categories(ctx, level: int):
    """List available categories."""
    try:
        client = ZKHBenchmarkClient(
            api_key=ctx.obj["api_key"],
            base_url=ctx.obj["base_url"]
        )
        
        categories = client.list_categories(level)
        
        if not categories:
            click.echo("No categories found.")
            return
        
        click.echo(f"\nAvailable categories (level {level}):\n")
        for cat in categories:
            if isinstance(cat, dict):
                click.echo(f"  • {cat.get('label', cat.get('value', str(cat)))}")
            else:
                click.echo(f"  • {cat}")
        
        click.echo(f"\nTotal: {len(categories)} categories")
        
    except ZKHBenchmarkError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--category", "-c",
    required=True,
    help="Category L4 name (e.g., '单承口管箍')"
)
@click.option(
    "--pool", "-p",
    type=click.Choice(["training", "evaluation", "both"]),
    default="both",
    help="Dataset type"
)
@click.pass_context
def info(ctx, category: str, pool: str):
    """Show dataset information."""
    try:
        info_data = Dataset.info(
            category=category,
            pool_type=pool,
            api_key=ctx.obj["api_key"],
            base_url=ctx.obj["base_url"]
        )
        
        click.echo(f"\n📦 Dataset: {info_data.get('category', category)}")
        click.echo(f"🏷️  Latest version: {info_data.get('latest_version', 'N/A')}")
        click.echo(f"📋 Available versions: {', '.join(info_data.get('versions', []))}")
        
        pools = info_data.get('pools', {})
        if 'training' in pools:
            training = pools['training']
            click.echo(f"\n📊 Training Set:")
            click.echo(f"  Records: {training.get('record_count', 0):,}")
            click.echo(f"  Size: {format_size(training.get('file_size', 0))}")
            click.echo(f"  Fields: {', '.join(training.get('fields', []))}")
        
        if 'evaluation' in pools:
            evaluation = pools['evaluation']
            click.echo(f"\n📊 Evaluation Set:")
            click.echo(f"  Records: {evaluation.get('record_count', 0):,}")
            click.echo(f"  Size: {format_size(evaluation.get('file_size', 0))}")
            click.echo(f"  Fields: {', '.join(evaluation.get('fields', []))}")
        
    except ZKHBenchmarkError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--category", "-c",
    required=True,
    help="Category L4 name"
)
@click.pass_context
def versions(ctx, category: str):
    """List available versions for a category."""
    try:
        versions = Dataset.versions(
            category=category,
            api_key=ctx.obj["api_key"],
            base_url=ctx.obj["base_url"]
        )
        
        if not versions:
            click.echo(f"No versions found for {category}")
            return
        
        click.echo(f"\n📦 Available versions for {category}:\n")
        click.echo(f"{'Version':<15} {'Latest':<10} {'Release Date':<25} {'Changelog'}")
        click.echo("-" * 80)
        
        for v in versions:
            version = v.get('version', 'N/A')
            is_latest = '✓' if v.get('is_latest') else ''
            date = v.get('release_date', 'N/A')[:19] if v.get('release_date') else 'N/A'
            changelog = v.get('changelog', '')[:30]
            click.echo(f"{version:<15} {is_latest:<10} {date:<25} {changelog}")
        
    except ZKHBenchmarkError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--category", "-c",
    required=True,
    help="Category L4 name (e.g., '单承口管箍')"
)
@click.option(
    "--pool", "-p",
    type=click.Choice(["training", "evaluation", "both"]),
    default="training",
    help="Dataset type"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "csv", "parquet"]),
    default="json",
    help="File format"
)
@click.option(
    "--version", "-v",
    help="Dataset version (default: latest)"
)
@click.option(
    "--output", "-o",
    default="./data",
    help="Output directory"
)
@click.option(
    "--async", "async_",
    is_flag=True,
    help="Force async export for large files"
)
@click.option(
    "--smart/--no-smart",
    default=True,
    help="Auto-detect file size and choose download method (default: enabled)"
)
@click.pass_context
def download(
    ctx,
    category: str,
    pool: str,
    format: str,
    version: Optional[str],
    output: str,
    async_: bool,
    smart: bool
):
    """Download a dataset.
    
    Examples:
        zkh-benchmark download -c "螺丝刀"
        zkh-benchmark download -c "球阀" -p evaluation -f parquet
        zkh-benchmark download -c "扳手" -v v1.0.0 -o ./my_data
    """
    try:
        kwargs = {
            "api_key": ctx.obj["api_key"],
            "base_url": ctx.obj["base_url"]
        }
        
        if async_:
            # Force async export
            click.echo(f"🚀 Creating async export for {category} {pool}...")
            filepath = Dataset.download_async(
                category=category,
                pool_type=pool,
                output_dir=output,
                format=format,
                version=version,
                **kwargs
            )
        elif smart and not async_:
            # Smart download: auto-detect file size
            click.echo(f"🤖 Smart downloading {category} {pool}...")
            filepath = Dataset.smart_download(
                category=category,
                pool_type=pool,
                output_dir=output,
                format=format,
                version=version,
                show_progress=True,
                **kwargs
            )
        else:
            # Direct download
            click.echo(f"⬇️  Downloading {category} {pool}...")
            filepath = Dataset.download(
                category=category,
                pool_type=pool,
                output_dir=output,
                format=format,
                version=version,
                show_progress=True,
                **kwargs
            )
        
        click.echo(f"\n✓ Downloaded to: {filepath}")
        
    except ZKHBenchmarkError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("categories", nargs=-1, required=True)
@click.option(
    "--pool", "-p",
    type=click.Choice(["training", "evaluation", "both"]),
    default="both"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "csv", "parquet"]),
    default="json"
)
@click.option(
    "--output", "-o",
    default="./data",
    help="Output directory"
)
@click.pass_context
def download_batch(ctx, categories: tuple, pool: str, format: str, output: str):
    """Download multiple datasets at once.
    
    Example:
        zkh-benchmark download-batch 单承口管箍 球阀 UPVC管 --pool training
    """
    failed = []
    
    for category in categories:
        click.echo(f"\n{'='*50}")
        click.echo(f"Downloading: {category}")
        click.echo('='*50)
        
        try:
            if pool == "both":
                # Download both training and evaluation
                Dataset.download(
                    category=category,
                    pool_type="training",
                    output_dir=output,
                    format=format,
                    api_key=ctx.obj["api_key"],
                    base_url=ctx.obj["base_url"],
                    show_progress=True
                )
                Dataset.download(
                    category=category,
                    pool_type="evaluation",
                    output_dir=output,
                    format=format,
                    api_key=ctx.obj["api_key"],
                    base_url=ctx.obj["base_url"],
                    show_progress=True
                )
            else:
                Dataset.download(
                    category=category,
                    pool_type=pool,
                    output_dir=output,
                    format=format,
                    api_key=ctx.obj["api_key"],
                    base_url=ctx.obj["base_url"],
                    show_progress=True
                )
            
        except ZKHBenchmarkError as e:
            click.echo(f"Failed to download {category}: {e}", err=True)
            failed.append(category)
    
    click.echo(f"\n{'='*50}")
    if failed:
        click.echo(f"Completed with {len(failed)} failures: {', '.join(failed)}")
    else:
        click.echo("✓ All downloads completed successfully!")


def format_size(size_bytes: int) -> str:
    """Format byte size to human readable."""
    if size_bytes == 0:
        return "0 Bytes"
    
    for unit in ["Bytes", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    
    return f"{size_bytes:.2f} TB"


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
