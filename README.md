# slop.at

Minimal web server for beautiful markdown with entity highlighting.

## Stack

- **FastAPI** - Web server
- **Oxigraph** - RDF graph database
- **Caddy** - Automatic HTTPS
- **Docker Compose** - One-command deploy

## Endpoints

- **POST /slop** - Receive markdown + entities + nquads
- **GET /s/{id}** - View rendered slop with highlighted entities

## Features

✨ Clean, readable typography
✨ Entity highlighting with opacity based on confidence
✨ Color-coded by entity type (Person, Organization, Place, Event, Topic, DefinedTerm)
✨ Mobile responsive
✨ No JavaScript required

## Deploy

See [DEPLOY.md](DEPLOY.md) for production deployment to Digital Ocean.

## Local Development

```bash
# Start with docker compose
docker compose up

# Or run manually:
uv sync
uvx oxigraph serve --location ./data &
uv run uvicorn server:app --reload --port 8080
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
- `SLOP_HOME` - Base directory for data (default: ~/.slop-at)
- `OXIGRAPH_URL` - Oxigraph server URL (default: http://localhost:7878)

Data is stored in:
- `~/.slop-at/slops/` - Rendered slop JSON files
- `~/.slop-at/oxigraph/` - RDF graph database

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
