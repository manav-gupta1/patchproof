import typer

app = typer.Typer(help="PatchProof command-line interface")


@app.command()
def version() -> None:
    typer.echo("PatchProof 0.1.0")
