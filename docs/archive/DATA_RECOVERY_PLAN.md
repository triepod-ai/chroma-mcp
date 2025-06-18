# Data Recovery and Integration Plan - SIMPLIFIED
## Lodestar Troubles & Sequential Thinking Memory System

**🎯 GOAL**: Recover 954 Neo4j entities and JSON memory data into Chroma MCP's SQLite3 volume  
**⏱️ TIMELINE**: < 1 hour (reduced from 3-4 weeks)  
**🔧 METHOD**: Direct SQLite3 manipulation bypassing ChromaDB client

### Current Data Locations Discovered

#### 1. Neo4j Graph Database (chroma-neo4j container: 7474/7687)
- **954 Entity nodes** with rich metadata
- **Key Entities:**
  - `LodestarPineconeConnector` - Lodestar-specific vector database implementation
  - `VectorCodeLens Troubleshooting` - Standard troubleshooting procedures
  - `sequential_thinking` - Step-by-step problem-solving tool
  - `MCP Docker Connection Troubleshooting` - Container connection issues
- **Entity Types:** Components (108), Tools (40), Processes (35), Files (34)

#### 2. JSON Memory Store (`claude-memory` volume)
- **305 lines of structured JSON entities** from March 23-24, 2025
- **Entity structure:** `{type, name, entityType, observations, relations}`
- **Key Content:** ClaudeDesktopCommander project architecture, MCP configurations

#### 3. Chroma Vector Database (SQLite3 Volume)
- **Location:** `/mnt/l/ToolNexusMCP_plugins/chroma-mcp/chroma_data/chroma.sqlite3`
- **Architecture:** MCP bypasses ChromaDB client, works directly with SQLite3 volume
- **Schema:** Collections, embeddings_queue, segments tables for data storage

---

## SIMPLIFIED RECOVERY PROCEDURE

### Step 1: Run Recovery Script (30 minutes)

```bash
cd /mnt/l/ToolNexusMCP_plugins/chroma-mcp
python3 sqlite_recovery.py
```

**What this does:**
1. **Backup** SQLite3 database automatically
2. **Create** recovery collection `lodestar_memory_recovery`
3. **Export** Neo4j data using: `docker exec chroma-neo4j cypher-shell`
4. **Insert** directly into SQLite3 `embeddings_queue` table
5. **Process** Lodestar-specific entities first

### Step 2: Verify Recovery (15 minutes)

```bash
# Test MCP can read recovered data
cd /mnt/l/ToolNexusMCP_plugins/chroma-mcp
python3 -c "
from src.chroma_mcp.server import get_chroma_client
client = get_chroma_client()
collection = client.get_collection('lodestar_memory_recovery')
print(f'Recovered {collection.count()} documents')
"
```

---

## TECHNICAL IMPLEMENTATION

### Recovery Script Architecture
```python
# sqlite_recovery.py - Direct SQLite3 manipulation
class ChromaSQLiteRecovery:
    def backup_database()          # Creates timestamped backup
    def create_recovery_collection() # Inserts into collections table
    def export_neo4j_data()        # Docker exec cypher-shell
    def insert_recovery_document() # Direct embeddings_queue insert
    def quick_recovery()           # Complete 1-hour process
```

### Neo4j Export Command
```bash
docker exec chroma-neo4j cypher-shell -u neo4j -p password \
"MATCH (n:Entity) WHERE n.name CONTAINS 'Lodestar' OR n.name CONTAINS 'sequential' 
 RETURN n.name, n.entityType, n.observations LIMIT 50"
```

### SQLite3 Schema Integration
- **collections** table: Creates `lodestar_memory_recovery` collection
- **embeddings_queue** table: Inserts documents for async processing
- **segments** table: Creates vector storage segments
- **Metadata preservation**: Entity type, name, observations, recovery timestamp

---

## WHY THIS WORKS (Volume-Based Reality)

❌ **ChromaDB Client Approach**: MCP ignores ChromaDB client  
✅ **SQLite3 Volume Approach**: MCP reads directly from volume  

**Key Discovery**: The chroma-mcp server accesses the SQLite3 database file directly at `/mnt/l/ToolNexusMCP_plugins/chroma-mcp/chroma_data/chroma.sqlite3`, not through ChromaDB's client API.

---

## EXPECTED OUTCOMES

✅ **Complete memory recovery** of 954+ Lodestar entities  
✅ **Sequential thinking patterns** preserved with relationships  
✅ **Troubleshooting procedures** searchable via MCP tools  
✅ **Historical context** available for problem-solving  
✅ **Backup safety** with automatic timestamped backups  

### Success Metrics
- Recovery collection contains 50+ Lodestar-specific documents
- MCP tools can query recovered data via semantic search
- Neo4j container data successfully migrated to Chroma volume
- Total process time under 1 hour

---

## EMERGENCY ROLLBACK

If recovery fails:
```bash
# Restore from backup
cp /mnt/l/ToolNexusMCP_plugins/chroma-mcp/chroma_data/chroma.sqlite3.backup_* \
   /mnt/l/ToolNexusMCP_plugins/chroma-mcp/chroma_data/chroma.sqlite3

# Restart MCP server
docker restart chroma-mcp
```

---

**📅 Updated**: May 22, 2025  
**⚡ Status**: READY FOR EXECUTION  
**🕐 Timeline**: < 1 hour (vs original 3-4 weeks)  
**🎯 Complexity**: REDUCED by using Context7 knowledge + volume reality