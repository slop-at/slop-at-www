#!/usr/bin/env python3
"""
slop.at - Minimal web server for beautiful markdown with entity highlighting
"""
import hashlib
import httpx
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import mistune
import os

# Configuration
OXIGRAPH_URL = os.getenv("OXIGRAPH_URL", "http://localhost:7878")
SLOP_HOME = Path(os.getenv("SLOP_HOME", Path.home() / ".slop-at"))
DATA_DIR = SLOP_HOME / "slops"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Security settings
MAX_SLOP_SIZE = int(os.getenv("MAX_SLOP_SIZE", "1000000"))  # 1MB default

app = FastAPI(title="slop.at")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc:
    HTTPException(status_code=429, detail="Too many requests"))

# Serve static files
static_dir = Path("./static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


def generate_hash(content: str) -> str:
    """Generate a short hash for content"""
    return hashlib.md5(content.encode()).hexdigest()[:8]


def highlight_entities_in_html(html: str, entities: list) -> str:
    """
    Highlight entities in rendered HTML using BeautifulSoup to properly handle text nodes

    Entities should be in format:
    [{"text": "Alice", "label": "Person", "score": 0.95}, ...]
    """
    if not entities:
        return html

    from bs4 import BeautifulSoup, NavigableString
    import re

    # Build a unique list of entities (text -> best scoring entity)
    entity_map = {}
    for entity in entities:
        text = entity.get("text", "").strip()
        if not text:
            continue
        # Keep highest confidence for each text
        if text not in entity_map or entity.get("score", 0) > entity_map[text].get("score", 0):
            entity_map[text] = entity

    # Sort by length (longest first) to avoid partial replacements
    sorted_entities = sorted(entity_map.values(), key=lambda e: len(e.get("text", "")), reverse=True)

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Process each entity
    for entity in sorted_entities:
        text = entity.get("text", "")
        label = entity.get("label", "unknown")
        score = entity.get("score", 0.5)

        # Show all entities at full visibility
        # Confidence score still available in tooltip

        # Find all text nodes that contain this entity text
        # Use case-insensitive search with word boundaries
        pattern = re.compile(r'\b' + re.escape(text) + r'\b', re.IGNORECASE)

        # Walk all text nodes
        for text_node in soup.find_all(string=True):
            # Skip if already inside a mark tag
            if text_node.parent.name == 'mark':
                continue

            # Check if this text node contains our entity
            if pattern.search(str(text_node)):
                # Split and wrap matches
                new_content = []
                last_end = 0

                for match in pattern.finditer(str(text_node)):
                    # Add text before match
                    if match.start() > last_end:
                        new_content.append(str(text_node)[last_end:match.start()])

                    # Create mark tag for matched text
                    mark_tag = soup.new_tag('mark')
                    mark_tag['class'] = ['entity', f'entity-{label.lower()}']
                    mark_tag['title'] = f'{label}: {score:.2f}'
                    mark_tag.string = match.group(0)
                    new_content.append(mark_tag)

                    last_end = match.end()

                # Add remaining text after last match
                if last_end < len(str(text_node)):
                    new_content.append(str(text_node)[last_end:])

                # Replace the text node with new content
                if new_content:
                    text_node.replace_with(*new_content)

    return str(soup)



def render_markdown(content: str) -> str:
    """Render markdown to HTML"""
    md = mistune.create_markdown(
        escape=False,  # Can't escape - we inject <mark> tags for entity highlighting
        plugins=['strikethrough', 'table', 'url', 'task_lists']
    )
    html = md(content)

    # Wrap frontmatter in a special div if it exists
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter_text = parts[1].strip()
            # Render frontmatter separately and wrap it
            frontmatter_html = f'<div class="frontmatter"><pre>{frontmatter_text}</pre></div>'
            # Remove frontmatter from main content and re-render
            content_only = parts[2].strip()
            content_html = md(content_only)
            # Move frontmatter to bottom
            return content_html + frontmatter_html

    return html


@app.get("/")
async def root():
    """Landing page"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>slop.at</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <h1>slop.at</h1>
        <p class="tagline">semantic web publishing</p>
        <p class="hint">Post slops via MCP or API</p>
    </div>
</body>
</html>
    """)


@app.post("/slop")
@limiter.limit("20/minute")  # 20 slops per minute per IP
async def post_slop(request: Request):
    """
    Receive markdown + nquads, render HTML, store in graph

    Body: {
        "markdown": "# Title\\n\\nContent...",
        "nquads": "<s> <p> <o> <g> .\\n...",
        "entities": [{"text": "...", "label": "...", "start": 0, "end": 5, "score": 0.9}, ...],
        "metadata": {"title": "...", "slop_id": "...", ...}
    }
    """
    try:
        data = await request.json()
        markdown = data.get("markdown", "")
        nquads = data.get("nquads", "")
        entities = data.get("entities", [])
        metadata = data.get("metadata", {})

        if not markdown:
            raise HTTPException(status_code=400, detail="No markdown provided")

        # Check content size
        if len(markdown) > MAX_SLOP_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Slop too large (max {MAX_SLOP_SIZE} bytes)"
            )

        # Generate hash from slop_id or content
        slop_id = metadata.get("slop_id")
        if slop_id:
            slop_hash = slop_id  # Already 8 chars from MCP
        else:
            slop_hash = generate_hash(markdown)

        # Store markdown and entities
        slop_file = DATA_DIR / f"{slop_hash}.json"
        import json
        slop_file.write_text(json.dumps({
            "markdown": markdown,
            "entities": entities,
            "metadata": metadata
        }))

        # Post N-Quads to Oxigraph
        if nquads:
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"{OXIGRAPH_URL}/store",
                        content=nquads,
                        headers={"Content-Type": "application/n-quads"},
                        timeout=30.0
                    )
                    response.raise_for_status()
                except Exception as e:
                    print(f"Warning: Failed to store in Oxigraph: {e}")

        return {
            "status": "success",
            "slop_id": slop_hash,
            "url": f"/s/{slop_hash}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/s/{slop_hash}")
async def view_slop(slop_hash: str):
    """View a slop by hash"""
    slop_file = DATA_DIR / f"{slop_hash}.json"

    if not slop_file.exists():
        raise HTTPException(status_code=404, detail="Slop not found")

    import json
    data = json.loads(slop_file.read_text())
    markdown = data.get("markdown", "")
    entities = data.get("entities", [])
    metadata = data.get("metadata", {})

    title = metadata.get("title", "Untitled Slop")

    # Render to HTML first
    content_html = render_markdown(markdown)

    # Then highlight entities in the HTML
    content_html = highlight_entities_in_html(content_html, entities)

    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - slop.at</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <article class="slop">
            {content_html}
        </article>
        <footer>
            <a href="/">← back to slop.at</a>
        </footer>
    </div>
</body>
</html>
    """)


def main():
    """Run the server"""
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    main()
