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
noveldb_id = os.getenv("NOVELDB_ID")
app = typer.Typer()
headers = {
    "Authorization": f"Bearer {hydrogen_token}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}
def fetch_novel_data():
    """
    Fetch data from the Notion Page for Novel.
    
    Returns:
        List of results if successful, or an empty list if the request fails.
    """
    url = f"https://api.notion.com/v1/blocks/{noveldb_id}/children"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("Fetched novel successfully!")
        return data.get("results", [])
    else:
        typer.echo(f"Failed to fetch data. Status code: {response.status_code}")
        typer.echo(response.text)
        return []
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
def fetch_block_children(block_id):
    """
    Fetch the children of a block if it has children.
    
    Args:
        block_id (str): The ID of the block whose children to fetch.

    Returns:
        List of children blocks.
    """
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("results", [])
    else:
        typer.echo(f"Failed to fetch children for block {block_id}. Status code: {response.status_code}")
        typer.echo(response.text)
        return []

@app.command()
def show_novel():
    """Show the novel data, including unfolded content."""
    results = fetch_novel_data()

    if not results:
        print("No data found for the novel.")
        return

    # Initialize a list to store novel content
    novel_content = []

    # Loop through the fetched blocks and extract text
    for block in results:
        block_type = block.get('type')
        has_children = block.get('has_children', False)
        
        # Handle paragraphs
        if block_type == 'paragraph':
            rich_text = block['paragraph']['rich_text']
            paragraph_text = ''.join([text['plain_text'] for text in rich_text])
            novel_content.append(paragraph_text)
        
        # Handle headings (e.g., heading_1, heading_2)
        elif block_type.startswith('heading'):
            rich_text = block[block_type]['rich_text']
            heading_text = ''.join([text['plain_text'] for text in rich_text])
            novel_content.append(f"\n{heading_text}\n")  # Add line breaks for headings

        # If the block has children, fetch them recursively
        if has_children:
            children = fetch_block_children(block['id'])
            for child in children:
                child_type = child.get('type')
                if child_type == 'paragraph':
                    rich_text = child['paragraph']['rich_text']
                    child_text = ''.join([text['plain_text'] for text in rich_text])
                    novel_content.append(child_text)

    # Join all text into a single string with line breaks
    full_novel = '\n'.join(novel_content)

    # Display the novel
    typer.echo("Here’s your novel:")
    typer.echo(full_novel)
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
    """
    Write a sentence using today's vocab. 
    If valid, append it to the last block of the current chapter.
    """
    # Fetch today's vocab
    vocab_results = fetch_notion_data()
    today_vocab_entry = get_deterministic_vocab(vocab_results)

    if not today_vocab_entry:
        typer.echo("No vocab data available for today.")
        return

    # Extract today's vocab
    properties = today_vocab_entry.get("properties", {})
    vocab_title = properties.get("Vocabulary", {}).get("title", [{}])[0].get("plain_text", "Unknown")

    # Check if the sentence includes today's vocab
    if vocab_title.lower() not in sentence.lower():
        typer.echo(f"Your sentence must include today's vocab: '{vocab_title}'. Try again.")
        return

    # Fetch novel data to find the last block
    results = fetch_novel_data()
    if not results:
        typer.echo("Failed to fetch novel data.")
        return

    # Recursively find the last child block in the current chapter
    def find_last_block(blocks):
        last_block = None
        for block in blocks:
            has_children = block.get("has_children", False)
            if has_children:
                children = fetch_block_children(block["id"])
                last_block = find_last_block(children) or block
            else:
                last_block = block
        return last_block

    last_block = find_last_block(results)
    if not last_block:
        typer.echo("Couldn't determine the last block to append to.")
        return

    # Append the sentence to the last block
    last_block_id = last_block["id"]
    url = f"https://api.notion.com/v1/blocks/{last_block_id}/children"
    payload = {
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": sentence
                            }
                        }
                    ]
                }
            }
        ]
    }

    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code == 200:
        typer.echo("Your sentence has been added to the last block of the current chapter!")
    else:
        typer.echo(f"Failed to add your sentence. Status code: {response.status_code}")
        typer.echo(response.text)

@app.command()
def showJournal():
    """Show all sentences."""
    for date, sentence in sentences_db.items():
        typer.echo(f"{date}: {sentence}")


if __name__ == "__main__":
    app()
