# /docker-volume-mount-verify - Claude Behavioral Guide

**Purpose**: Comprehensive verification of Docker Compose volume mounting, container status, and data accessibility
**MCP Integration**: Basic (for storing verification results and patterns)

## Your Mission
Systematically verify Docker volume mounting configuration, container health, and data accessibility. Document findings and identify any discrepancies between host-side and container-side data.

## MCP Strategy
- Store verification results in appropriate memory system
- Use workflow documentation for process improvements
- Cache common verification patterns for reuse

## Implementation Workflow

### Step 1: Docker Compose File Verification
1. **List all compose files** with modification dates
   ```bash
   ls -la docker-compose*.yaml
   ```
2. **Check active compose configuration**
   ```bash
   docker compose config --services
   ```
3. **Verify container status and creation times**
   ```bash
   docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.CreatedAt}}"
   ```

### Step 2: Volume Mount Inspection
1. **List Docker volumes**
   ```bash
   docker volume ls | grep -E "(volume_pattern_1|volume_pattern_2)"
   ```
2. **Check volume creation timestamps**
   ```bash
   docker volume inspect volume_name --format='{{.CreatedAt}}'
   ```
3. **Inspect actual container mount points**
   ```bash
   docker inspect container_name --format='{{json .Mounts}}' | python3 -m json.tool
   ```

### Step 3: Data Accessibility Testing
1. **Test volume accessibility**
   ```bash
   docker exec container_name ls -la /mounted/path
   ```
2. **Test write permissions**
   ```bash
   docker exec container_name touch /mounted/path/test-write.txt
   ```
3. **Verify data consistency** (compare host vs container data)
   ```bash
   docker exec container_name ls -la /container/data/path
   ls -la /host/data/path
   ```

### Step 4: Application Data Verification
1. **Test application data accessibility** (if applicable)
2. **Count records/collections** in database
3. **Verify data timestamps** and recency
4. **Document any data discrepancies**

### Step 5: Results Documentation
1. **Summarize findings** with specific metrics
2. **Identify discrepancies** between expected and actual state
3. **Store verification results** in memory system (optional)
4. **Provide recommendations** for any issues found

## Usage Examples
# /docker-volume-mount-verify - Complete verification of current Docker setup
# /docker-volume-mount-verify chroma-mcp - Verify specific container's volume mounts
# /docker-volume-mount-verify --data-check - Focus on data accessibility and consistency

## Verification Checklist
- [ ] All Docker Compose files identified with timestamps
- [ ] Active compose configuration confirmed
- [ ] Container creation times verified
- [ ] Volume mount points inspected
- [ ] Data accessibility tested
- [ ] Write permissions confirmed
- [ ] Host vs container data consistency checked
- [ ] Application data verified (if applicable)
- [ ] Results documented with specific metrics

## MCP Tools
# mcp__chroma__chroma_add_documents - Store verification results and patterns
# mcp__qdrant__qdrant_store - Store verification methodologies and lessons learned

## Common Issues to Check
- **Stale host data**: Host directory data older than container data
- **Volume not mounted**: Container using different storage than expected
- **Permission issues**: Write access problems in mounted volumes
- **Wrong compose file**: Using outdated or incorrect compose configuration
- **Missing volumes**: External volumes not created or accessible
- **Data inconsistency**: Differences between host and container data states

## Expected Output Format
```
## Docker Volume Mount Verification Results

**Compose File**: docker-compose.yaml (modified: YYYY-MM-DD)
**Active Services**: service1, service2, service3
**Containers Created**: YYYY-MM-DD HH:MM

### Volume Status
- volume_name_1: ✅ Mounted, accessible, writable
- volume_name_2: ✅ Mounted, accessible, writable

### Data Accessibility
- Container data: XXX MB, YYYY collections, recent activity
- Host data: XXX MB, created YYYY-MM-DD (status: current/stale)

### Findings
- ✅ All volumes properly mounted and accessible
- ⚠️ Host data appears older than container data
- ✅ Application data fully accessible with XX,XXX records

### Recommendations
- Continue using current Docker volume setup
- Consider archiving stale host data
- Volume mounting working correctly
```

## Performance Notes
- **Redis caching**: Cache common verification patterns and results
- **Parallel checks**: Run independent verifications simultaneously
- **Focus on metrics**: Provide specific numbers and timestamps
- **Graceful degradation**: Continue verification even if some checks fail

## Integration with BRAINPOD Workflow
- Follows systematic verification approach
- Documents findings with specific evidence
- Stores patterns for reuse in similar setups
- Provides actionable recommendations