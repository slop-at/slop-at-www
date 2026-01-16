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
import mistune
import os

# Configuration
OXIGRAPH_URL = os.getenv("OXIGRAPH_URL", "http://localhost:7878")
DATA_DIR = Path("./slops")
DATA_DIR.mkdir(exist_ok=True)

app = FastAPI(title="slop.at")

# Serve static files
static_dir = Path("./static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


def generate_hash(content: str) -> str:
    """Generate a short hash for content"""
    return hashlib.md5(content.encode()).hexdigest()[:8]


def highlight_entities(markdown: str, entities: list) -> str:
    """
    Highlight entities in markdown text with opacity based on confidence

    Entities should be in format:
    [{"text": "Alice", "label": "Person", "start": 0, "end": 5, "score": 0.95}, ...]
    """
    if not entities:
        return markdown

    # Sort entities by start position (reverse) to avoid offset issues
    sorted_entities = sorted(entities, key=lambda e: e.get("start", 0), reverse=True)

    result = markdown
    for entity in sorted_entities:
        text = entity.get("text", "")
        label = entity.get("label", "unknown")
        score = entity.get("score", 0.5)
        start = entity.get("start", 0)
        end = entity.get("end", start + len(text))

        # Map confidence to opacity: 0.9+ = 1.0, 0.7-0.9 = 0.7, <0.7 = 0.4
        if score >= 0.9:
            opacity = 1.0
        elif score >= 0.7:
            opacity = 0.7
        else:
            opacity = 0.4

        # Create highlighted span
        highlighted = f'<mark class="entity entity-{label.lower()}" style="opacity: {opacity}" title="{label}: {score:.2f}">{text}</mark>'

        # Replace in text
        result = result[:start] + highlighted + result[end:]

    return result


def render_markdown(content: str) -> str:
    """Render markdown to HTML"""
    md = mistune.create_markdown(
        escape=False,
        plugins=['strikethrough', 'table', 'url', 'task_lists']
    )
    return md(content)


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

        # Generate hash from slop_id or content
        slop_id = metadata.get("slop_id")
        if slop_id:
            slop_hash = slop_id[:8]
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

    # Highlight entities in markdown before rendering
    highlighted_markdown = highlight_entities(markdown, entities)

    # Render to HTML
    content_html = render_markdown(highlighted_markdown)

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
