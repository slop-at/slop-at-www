# slop.at-www

Minimal web server for slop.at - beautiful markdown with entity highlighting.

## Architecture

Dead simple:
- **POST /slop** - Receive markdown + nquads, render HTML, store in graph
- **GET /s/{hash}** - View rendered slop with highlighted entities
- **Oxigraph CLI** - Running separately for graph storage

## Features

✨ Clean, readable typography
✨ Entity highlighting with opacity based on confidence
✨ Color-coded by entity type (Person, Organization, Place, Event, Topic, DefinedTerm)
✨ Mobile responsive
✨ No JavaScript required

## Setup

```bash
# Install dependencies
uv sync

# Start everything (web server + Oxigraph)
./start.sh

# Or manually in separate terminals:
# Terminal 1: uvx oxigraph serve --location ./data
# Terminal 2: uv run python server.py
```

Server runs on http://localhost:8080

To stop:
```bash
./stop.sh
```

## Usage

### Post a slop

```bash
curl -X POST http://localhost:8080/slop \
  -H "Content-Type: application/json" \
  -d '{
    "markdown": "# Test Slop\n\nAlice went to Paris to attend the AI Conference.",
    "entities": [
      {"text": "Alice", "label": "Person", "start": 0, "end": 5, "score": 0.95},
      {"text": "Paris", "label": "Place", "start": 14, "end": 19, "score": 0.88},
      {"text": "AI Conference", "label": "Event", "start": 33, "end": 46, "score": 0.92}
    ],
    "nquads": "<http://example.com/alice> <http://example.com/went> <http://example.com/paris> .",
    "metadata": {"title": "Test Slop", "slop_id": "abc123"}
  }'
```

Returns:
```json
{
  "status": "success",
  "slop_id": "abc12345",
  "url": "/s/abc12345"
}
```

### View a slop

Open http://localhost:8080/s/abc12345

## Entity Highlighting

Entities are highlighted inline with:
- **Color** - based on entity type (Person=red, Place=blue, Organization=purple, etc.)
- **Opacity** - based on confidence:
  - 90%+ = full opacity (1.0)
  - 70-90% = medium opacity (0.7)
  - <70% = light opacity (0.4)

Hover over an entity to see its label and confidence score.

## Configuration

Environment variables:
- `OXIGRAPH_URL` - Oxigraph server URL (default: http://localhost:7878)

## Integration with slopnet-mcp

The MCP server posts slops here:

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8080/slop",
        json={
            "markdown": full_content,
            "entities": entities,
            "nquads": nquads_data,
            "metadata": metadata
        }
    )
```

## What's NOT here (yet)

- ❌ No related slops
- ❌ No concept clicking
- ❌ No graph visualization
- ❌ No SPARQL queries from browser

Just beautiful, readable slops with entity highlights. That's it.

---

Built with ❤️ by spacegoatai
Chief Emoji Officer at Slop Serve Inc.
