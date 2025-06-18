# MCP Server Neo4j Configuration Task

**Context**: Memory data successfully migrated from JSON to Neo4j database  
**Requirement**: Update MCP memory server to use Neo4j backend instead of JSON file  
**Location**: `/mnt/l/mcp_servers/memory/`  

## 🎯 TASK OBJECTIVE

Configure the MCP memory server to read/write from Neo4j database instead of the JSON file at `/mnt/l/mcp_servers/memory/dist/memory.json`

## 📊 MIGRATION RESULTS REFERENCE

**Neo4j Database Status**:
- **Entities**: 1,553 migrated successfully
- **Relationships**: 2,721 created  
- **Container**: `chroma-neo4j` (ports 7474:7474, 7687:7687)
- **Credentials**: neo4j/password
- **Validation**: Complete (see MIGRATION_VALIDATION_REPORT.md)

## 🔧 REQUIRED CHANGES

### 1. Update MCP Server Dependencies
```bash
cd /mnt/l/mcp_servers/memory/
npm install neo4j-driver
```

### 2. Modify Server Implementation
**Current**: Uses JSON file I/O operations  
**Target**: Replace with Neo4j Cypher queries  

**Key Operations to Convert**:
- `remember` → Neo4j MERGE entity with observations
- `recall` → Neo4j MATCH entities by name/type  
- `forget` → Neo4j DELETE entities/relationships
- `search` → Neo4j full-text or property search

### 3. Update MCP Configuration
**File**: Client-side MCP configuration (e.g., Claude Desktop config)
```json
{
  "mcpServers": {
    "memory": {
      "command": "node",
      "args": ["/mnt/l/mcp_servers/memory/dist/index.js"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j", 
        "NEO4J_PASSWORD": "password"
      }
    }
  }
}
```

## 🔍 TECHNICAL SPECIFICATIONS

### Neo4j Schema (Current)
```cypher
// Entities
(:Entity {name: string, entityType: string, observations: [string], created: timestamp, source: string})

// Relationships  
()-[:RELATES_TO {type: string, created: timestamp, source: string}]->()
```

### Sample Queries for MCP Operations
```cypher
// Remember (create/update entity)
MERGE (e:Entity {name: $name, entityType: $entityType})
ON CREATE SET e.observations = [$observation], e.created = timestamp()
ON MATCH SET e.observations = e.observations + [$observation], e.updated = timestamp()

// Recall (search entities)
MATCH (e:Entity) 
WHERE e.name CONTAINS $searchTerm OR any(obs IN e.observations WHERE obs CONTAINS $searchTerm)
RETURN e.name, e.entityType, e.observations

// Forget (delete entity)
MATCH (e:Entity {name: $name, entityType: $entityType})
DETACH DELETE e
```

## ⚠️ IMPORTANT CONSIDERATIONS

1. **Backup Strategy**: Keep JSON file as backup until Neo4j integration verified
2. **Error Handling**: Implement fallback mechanisms for Neo4j connection issues  
3. **Performance**: Neo4j queries should be faster than JSON file I/O
4. **Testing**: Verify all MCP tools (remember, recall, forget) work with Neo4j
5. **Dependencies**: Ensure neo4j-driver installed in MCP server environment

## 📋 VALIDATION CHECKLIST

After implementation:
- [ ] MCP server connects to Neo4j successfully
- [ ] `remember` command creates/updates entities in Neo4j
- [ ] `recall` command searches Neo4j and returns results
- [ ] `forget` command deletes from Neo4j  
- [ ] Error handling works for Neo4j connection failures
- [ ] Performance is equal or better than JSON file approach
- [ ] All existing memory data accessible through MCP tools

## 🎯 SUCCESS CRITERIA

**Primary**: MCP memory server fully operational using Neo4j backend  
**Secondary**: JSON to Neo4j migration utilized, no data loss  
**Tertiary**: Performance improvement over JSON file I/O operations

---

**Next Action**: Implement Neo4j integration in MCP memory server codebase at `/mnt/l/mcp_servers/memory/`