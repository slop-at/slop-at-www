# slop.at TODO

## Configuration & Setup
- [ ] Use GitHub username instead of email for author field
  - Currently extracts from git config user.email (e.g., "rob.kunkle")
  - Should use GitHub username (e.g., "goodlux")
  - Makes querying and matching across users cleaner
  - Author field appears in frontmatter and RDF graph

- [ ] GitHub Action: Auto-generate n-triples for direct commits
  - Check if .nt file exists and is newer than .md file
  - If not: run entity extraction, generate RDF, commit n-triples
  - Enables multiple authoring paths:
    - Via MCP (local extraction)
    - Via GitHub web UI (action generates)
    - Via direct git commit (action fills gaps)
  - N-triples become like compiled artifacts
  - Ensures graph server always has complete data

## Future Features

### Entity Interaction
- [ ] Make highlighted entities clickable
  - Show entity details on click
  - Display confidence score
  - Show entity type
  - Link to related entities in the graph

### Entity Extraction Improvements
- [ ] Add temporal entity types to GLiNER2 extraction
  - Date: extract dates (e.g., "January 16, 2026", "2026-01-16")
  - Time: extract times (e.g., "8:54 AM", "14:30")
  - Consider using schema.org Date/Time types
  - Will need corresponding CSS colors for highlighting

- [ ] Separate frontmatter entity extraction
  - Currently frontmatter is included in main extraction
  - Should have dedicated extraction step for metadata fields
  - Example: author name not always highlighted in frontmatter
  - Would allow better metadata-specific entity handling

### Entity Highlighting Improvements
- [x] Switch from position-based to word-list highlighting
  - ~~Currently: only highlights specific instances GLiNER2 detected~~
  - ~~Future: highlight ALL instances of detected entities~~
  - ~~Use word/type/confidence dictionary instead of start/end positions~~
  - ~~This ensures consistent highlighting across the document~~
  - DONE: Now using BeautifulSoup to find and highlight all instances

### Relationship Visualization
- [ ] Draw arrows between related entities
  - Extract relationships from RDF graph
  - Visual connections showing semantic relationships
  - Interactive: click entity to see all connections
  - Could use SVG overlay or a library like D3.js

### Shape Analytics
- [ ] Local vs Server shape comparison
  - Local Oxigraph: user's personal writing patterns
  - Server Oxigraph: aggregate across all users
  - Compare entity distributions, co-occurrence patterns
  - Find semantic overlap between users ("who writes about similar topics?")
  - Periodic jobs to generate shape metrics

- [ ] Pre-computed analytics cache
  - Generate entity co-occurrence matrices
  - Calculate entity centrality/importance scores
  - Track temporal trends (topics over time)
  - Save as JSON/Parquet for fast visualization
  - Update on slop post or periodic refresh

- [ ] Matching users by semantic similarity
  - "Find people writing about Oxigraph"
  - "Who else mentions ontology gardening + SPARQL?"
  - Use co-occurrence data to suggest connections

## Notes
- Current highlighting works well for MVP
- These features will need JavaScript for interactivity
- Relationship data is already in Oxigraph, just needs querying
- Named graphs provide natural co-occurrence: all entities in same graph co-occur in that slop
- Local + server architecture enables personal vs community analytics
