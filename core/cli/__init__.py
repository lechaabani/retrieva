"""Retrieva CLI — command-line interface for the RAG platform."""

from __future__ import annotations

import click

from core.cli.commands.plugin import plugin
from core.cli.commands.setup import setup


@click.group()
@click.version_option(version="0.1.0", prog_name="retrieva")
def main() -> None:
    """Retrieva — The WordPress of RAG."""


main.add_command(plugin)
main.add_command(setup)
