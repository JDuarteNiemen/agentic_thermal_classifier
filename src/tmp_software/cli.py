# src/tmp_project/cli.py

import json
import typer

from .api import (
    FastTMP,
    DemocraticTMP,
    SummaryTMP,
)

app = typer.Typer()


@app.command()
def fast(
    accession: str,
    model: str = "gemma4:e4b"
):
    """
    Fast thermal prediction.
    """

    result = FastTMP(accession, model)

    print(json.dumps(result, indent=2))


@app.command()
def democratic(
    accession: str,
    model: str = "gemma4:e4b"
):
    """
    Democratic thermal prediction.
    """

    result = DemocraticTMP(accession, model)

    print(json.dumps(result, indent=2))


@app.command()
def summary(
    accession: str,
    model: str = "gemma:e4b"
):
    """
    Summary thermal prediction.
    """

    result = SummaryTMP(accession, model)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    app()