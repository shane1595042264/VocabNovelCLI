import typer
from datetime import date
from dotenv import load_dotenv
import os
import requests
import hashlib
from datetime import datetime, timezone
load_dotenv()
hydrogen_token = os.getenv("HYDROGEN_TOKEN")
vocabdb_id = os.getenv("VOCABDB_ID")
app = typer.Typer()
headers = {
    "Authorization": f"Bearer {hydrogen_token}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}
def fetch_notion_data():
    """
    Fetch data from the Notion database.
    
    Returns:
        List of results if successful, or an empty list if the request fails.
    """
    url = f"https://api.notion.com/v1/databases/{vocabdb_id}/query"
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("Fetched data successfully!")
        return data.get("results", [])
    else:
        typer.echo(f"Failed to fetch data. Status code: {response.status_code}")
        typer.echo(response.text)
        return []
def get_deterministic_vocab(vocab_list):
    """
    Select a deterministic vocabulary entry for today's date.
    
    Args:
        vocab_list (list): List of vocabulary entries from the database.

    Returns:
        dict: The vocabulary entry selected for today.
    """
    today = str(date.today())
    if not vocab_list:
        return None
    
    # Hash today's date to create a deterministic index
    hashed_date = int(hashlib.md5(today.encode()).hexdigest(), 16)
    index = hashed_date % len(vocab_list)
    
    return vocab_list[index]



@app.command()
def show_vocab():
    """Show all vocab with their English definitions."""
    url = f"https://api.notion.com/v1/databases/{vocabdb_id}/query"
    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        
        typer.echo("Vocab list:")
        for result in results:
            properties = result.get("properties", {})
            vocab_title = properties.get("Vocabulary", {}).get("title", [{}])[0].get("plain_text", "Unknown")
            english_def = properties.get("English Definition", {}).get("rich_text", [{}])[0].get("plain_text", "No definition available")
            typer.echo(f"{vocab_title}: {english_def}")
    else:
        typer.echo(f"Failed to fetch vocab. Status code: {response.status_code}")
        typer.echo(response.text)

@app.command()
def add(vocab: str):
    """Add vocab to your list."""
    vocab_db[vocab] = {"added": str(date.today())}
    typer.echo(f"Added vocab: {vocab}")

@app.command()
def today():
    """
    Show today's vocab, deterministic based on the date.
    """
    results = fetch_notion_data()
    vocab = get_deterministic_vocab(results)
    
    if vocab:
        properties = vocab.get("properties", {})
        vocab_title = properties.get("Vocabulary", {}).get("title", [{}])[0].get("plain_text", "Unknown")
        english_def = properties.get("English Definition", {}).get("rich_text", [{}])[0].get("plain_text", "No definition available")
        typer.echo(f"Today's vocab: {vocab_title}")
        typer.echo(f"Definition: {english_def}")
    else:
        typer.echo("No vocab data available.")

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
