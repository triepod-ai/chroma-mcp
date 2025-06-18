#!/usr/bin/env python3
"""
Simplified JSON to Neo4j Migration Script
Migrates memory.json data to Neo4j using batch MERGE operations
"""

import json
import time
from neo4j import GraphDatabase

class SimpleMemoryMigrator:
    def __init__(self, json_path="/mnt/l/mcp_servers/memory/dist/memory.json"):
        self.json_path = json_path
        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
        self.stats = {"entities": 0, "relations": 0, "duplicates_merged": 0}
    
    def run_migration(self):
        """Execute complete migration in 3 simple steps"""
        print("🚀 Starting JSON to Neo4j Migration...")
        start_time = time.time()
        
        # Step 1: Load JSON data
        entities, relations = self.load_json_data()
        print(f"📊 Loaded {len(entities)} entities, {len(relations)} relations")
        
        # Step 2: Batch migrate entities using MERGE
        self.batch_migrate_entities(entities)
        
        # Step 3: Batch migrate relations using MERGE  
        self.batch_migrate_relations(relations)
        
        duration = time.time() - start_time
        print(f"✅ Migration completed in {duration:.1f}s")
        print(f"📈 Stats: {self.stats}")
        
    def load_json_data(self):
        """Load and separate entities/relations from JSON"""
        entities, relations = [], []
        
        with open(self.json_path, 'r') as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    if item.get('type') == 'entity':
                        entities.append(item)
                    elif item.get('type') == 'relation':
                        relations.append(item)
                except json.JSONDecodeError:
                    continue
                    
        return entities, relations
    
    def batch_migrate_entities(self, entities):
        """Migrate all entities using single MERGE query"""
        print("📥 Migrating entities...")
        
        query = """
        UNWIND $entities AS entity
        MERGE (e:Entity {name: entity.name, entityType: entity.entityType})
        ON CREATE SET 
            e.observations = entity.observations,
            e.created = timestamp(),
            e.source = 'JSON_MIGRATION'
        ON MATCH SET 
            e.observations = CASE 
                WHEN e.observations IS NULL THEN entity.observations
                ELSE e.observations + entity.observations
            END,
            e.updated = timestamp(),
            e.migrated_from_json = true
        RETURN count(e) as processed
        """
        
        with self.driver.session() as session:
            result = session.run(query, entities=entities)
            count = result.single()['processed']
            self.stats['entities'] = count
            print(f"✓ Processed {count} entities")
    
    def batch_migrate_relations(self, relations):
        """Migrate all relations using single MERGE query"""
        print("🔗 Migrating relations...")
        
        query = """
        UNWIND $relations AS rel
        MATCH (from:Entity {name: rel.from})
        MATCH (to:Entity {name: rel.to})
        MERGE (from)-[r:RELATES_TO {type: rel.relationType}]->(to)
        ON CREATE SET 
            r.created = timestamp(),
            r.source = 'JSON_MIGRATION'
        RETURN count(r) as processed
        """
        
        with self.driver.session() as session:
            result = session.run(query, relations=relations)
            count = result.single()['processed']
            self.stats['relations'] = count
            print(f"✓ Processed {count} relations")
    
    def close(self):
        self.driver.close()

if __name__ == "__main__":
    migrator = SimpleMemoryMigrator()
    try:
        migrator.run_migration()
    finally:
        migrator.close()