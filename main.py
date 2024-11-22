import typer
from datetime import date

app = typer.Typer()

vocab_db = {}  # Replace with Notion integration later
sentences_db = {}

@app.command()
def show():
    """Show all vocab."""
    typer.echo("Vocab list:")
    for vocab in vocab_db:
        typer.echo(vocab)

@app.command()
def add(vocab: str):
    """Add vocab to your list."""
    vocab_db[vocab] = {"added": str(date.today())}
    typer.echo(f"Added vocab: {vocab}")

@app.command()
def today():
    """Show today's vocab."""
    today = str(date.today())
    today_vocab = [v for v, d in vocab_db.items() if d["added"] == today]
    typer.echo(f"Today's vocab: {', '.join(today_vocab) if today_vocab else 'None'}")

@app.command()
def sentence(sentence: str):
    """Write a sentence with today's vocab."""
    today = str(date.today())
    if today in sentences_db:
        typer.echo("You already wrote a sentence today!")
        return
    sentences_db[today] = sentence
    typer.echo(f"Saved sentence: {sentence}")
@app.command()
def showJournal():
    """Show all sentences."""
    for date, sentence in sentences_db.items():
        typer.echo(f"{date}: {sentence}")


if __name__ == "__main__":
    app()
