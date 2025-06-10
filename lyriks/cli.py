import click
from pathlib import Path

@click.group()
@click.version_option()

def main():
    pass

@main.command()
@click.option("--text", "-t", default="Hello World!", help="Prints anything to the Command Line")
def test(text):
    click.secho(str(text), fg="green", bold=True)
    
if __name__ == "__main__":
    main()