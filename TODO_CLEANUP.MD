# Chroma-MCP Project Cleanup Plan

## Overview
This plan reorganizes the chroma-mcp project structure while preserving the working `~/run-chroma-mcp.sh` configuration.

## Important Preservation Requirements
- **DO NOT MODIFY**: `~/run-chroma-mcp.sh` - This script must remain functional
- The script expects: `docker exec -i chroma-mcp chroma-mcp --client-type http --host 10.0.0.225 --port 8001`
- Container name `chroma-mcp` must remain unchanged in docker-compose.yaml
- The main Dockerfile must continue to build the chroma-mcp executable in the expected location

## Phase 1: Create Directory Structure (30 minutes)

### 1.1 Create new directories
```bash
mkdir -p docker/
mkdir -p docker/custom-chroma/
mkdir -p tests/
mkdir -p tests/integration/
mkdir -p tests/unit/
mkdir -p examples/
mkdir -p scripts/
mkdir -p docs/
mkdir -p docs/archive/
mkdir -p config/
```

## Phase 2: Organize Docker Files (45 minutes)

### 2.1 Move Docker-related files
- [ ] Move `Dockerfile` → Keep in root (main application Dockerfile)
- [ ] Move `http-proxy.Dockerfile` → `docker/http-proxy.Dockerfile`
- [ ] Move `filesystem.Dockerfile` → `docker/filesystem.Dockerfile`
- [ ] Move `custom-chroma/` directory → `docker/custom-chroma/`
- [ ] Keep `docker-compose.yaml` in root (standard practice)
- [ ] Move docker-compose backups:
  - `docker-compose.fixed` → `docker/backups/docker-compose.fixed`
  - `docker-compose.yaml.backup-*` → `docker/backups/`
  - `docker-compose.yaml.bak` → `docker/backups/`
  - `docker-compose.yaml.fixed` → `docker/backups/`
  - `docker-compose.yaml.new` → `docker/backups/`

### 2.2 Update docker-compose.yaml references
- [ ] Update `dockerfile: http-proxy.Dockerfile` → `dockerfile: docker/http-proxy.Dockerfile`
- [ ] Update `dockerfile: filesystem.Dockerfile` → `dockerfile: docker/filesystem.Dockerfile`
- [ ] Update custom-chroma build context if needed

## Phase 3: Organize Test Files (30 minutes)

### 3.1 Move test files to tests directory
- [ ] Move `test_*.py` files → `tests/`
  - `test_api.py` → `tests/integration/test_api.py`
  - `test_chroma.py` → `tests/integration/test_chroma.py`
  - `test_chroma_functionality.py` → `tests/unit/test_chroma_functionality.py`
  - `test_chroma_mcp.py` → `tests/integration/test_chroma_mcp.py`
  - `test_http_proxy.py` → `tests/integration/test_http_proxy.py`
  - `test_mcp.py` → `tests/unit/test_mcp.py`
  - `test_sequential_thinking.py` → `tests/unit/test_sequential_thinking.py`
  - `test_server.py` → `tests/unit/test_server.py`
- [ ] Move `tests/test_server.py` → `tests/unit/test_server_duplicate.py` (resolve duplicate)
- [ ] Move `test_output.txt` → `tests/test_output.txt`

### 3.2 Update test imports
- [ ] Update all test files to use correct import paths from new locations

## Phase 4: Organize Example and Demo Files (20 minutes)

### 4.1 Move example files
- [ ] Move `chroma_demo.py` → `examples/chroma_demo.py`
- [ ] Move `direct_chroma_example.py` → `examples/direct_chroma_example.py`
- [ ] Move `run_chroma_demo.py` → `examples/run_chroma_demo.py`
- [ ] Move `sequential_thinking_example.py` → `examples/sequential_thinking_example.py`
- [ ] Move `knowledge_base_demo.py` → `examples/knowledge_base_demo.py`

## Phase 5: Organize Scripts and Utilities (20 minutes)

### 5.1 Move script files
- [ ] Move `run-mcp.sh` → `scripts/run-mcp.sh`
- [ ] Move `rebuild-chroma-mcp.bat` → `scripts/rebuild-chroma-mcp.bat`
- [ ] Move `rebuild-filesystem-api.bat` → `scripts/rebuild-filesystem-api.bat`
- [ ] Move `sqlite_recovery.py` → `scripts/sqlite_recovery.py`
- [ ] Move `verify_persistence.py` → `scripts/verify_persistence.py`
- [ ] Move `json_to_neo4j_migrator.py` → `scripts/json_to_neo4j_migrator.py`

## Phase 6: Organize Proxy and API Files (15 minutes)

### 6.1 Move proxy implementations
- [ ] Create `src/proxies/` directory
- [ ] Move `http_proxy.py` → `src/proxies/http_proxy.py`
- [ ] Move `direct_http_proxy.py` → `src/proxies/direct_http_proxy.py`
- [ ] Move `functional_http_proxy.py` → `src/proxies/functional_http_proxy.py`
- [ ] Move `simple_http_proxy.py` → `src/proxies/simple_http_proxy.py`
- [ ] Move `websocket_http_proxy.py` → `src/proxies/websocket_http_proxy.py`
- [ ] Move `filesystem_main.py` → `src/proxies/filesystem_main.py`

## Phase 7: Organize Documentation (15 minutes)

### 7.1 Move documentation files
- [ ] Keep main docs in root: `README.md`, `LICENSE`, `CHANGELOG.md`, `SECURITY.md`
- [ ] Move project-specific docs to docs/:
  - `CLAUDE_CONTEXT.md` → `docs/CLAUDE_CONTEXT.md`
  - `CONTAINER_REBUILD_SUMMARY.md` → `docs/archive/CONTAINER_REBUILD_SUMMARY.md`
  - `DATA_RECOVERY_PLAN.md` → `docs/archive/DATA_RECOVERY_PLAN.md`
  - `DEPLOYMENT_STATUS.md` → `docs/DEPLOYMENT_STATUS.md`
  - `FILESYSTEM-INTEGRATION.md` → `docs/FILESYSTEM-INTEGRATION.md`
  - `HTTP_PROXY_USAGE.md` → `docs/HTTP_PROXY_USAGE.md`
  - `MCP_NEO4J_CONFIGURATION_TASK.md` → `docs/archive/MCP_NEO4J_CONFIGURATION_TASK.md`
  - `MIGRATION_COMPLETE.md` → `docs/archive/MIGRATION_COMPLETE.md`
  - `MIGRATION_VALIDATION_REPORT.md` → `docs/archive/MIGRATION_VALIDATION_REPORT.md`
  - `TEST_INSTRUCTIONS.md` → `docs/TEST_INSTRUCTIONS.md`
  - `TOKEN_OPTIMIZATION_GUIDE.md` → `docs/TOKEN_OPTIMIZATION_GUIDE.md`
  - `VALIDATION_REPORT.md` → `docs/archive/VALIDATION_REPORT.md`

## Phase 8: Clean Up and Configuration (10 minutes)

### 8.1 Move configuration files
- [ ] Move `glama.json` → `config/glama.json`
- [ ] Move `smithery.yaml` → `config/smithery.yaml`
- [ ] Keep `.gitignore` in root
- [ ] Keep `pyproject.toml` in root
- [ ] Keep `uv.lock` in root
- [ ] Keep `requirements-filesystem.txt` → consider renaming to `requirements-proxy.txt`

### 8.2 Remove or archive
- [ ] Delete `desktop.ini` (Windows system file)
- [ ] Review and potentially remove `L/` directory (appears to be empty or symlink)
- [ ] Keep `CLAUDE.local.md` in root (local configuration)
- [ ] Keep `TODO.md` in root (active task tracking)

## Phase 9: Update References (30 minutes)

### 9.1 Update all file references
- [ ] Update imports in Python files
- [ ] Update Dockerfile COPY commands
- [ ] Update docker-compose.yaml build contexts and dockerfile paths
- [ ] Update any hardcoded paths in scripts
- [ ] Update CI/CD configurations if any

### 9.2 Test critical functionality
- [ ] Verify `~/run-chroma-mcp.sh` still works
- [ ] Test docker-compose up
- [ ] Run basic integration test
- [ ] Verify HTTP proxy functionality

## Phase 10: Documentation Updates (20 minutes)

### 10.1 Update documentation
- [ ] Update README.md with new project structure
- [ ] Create `docs/PROJECT_STRUCTURE.md` documenting the new layout
- [ ] Update any setup instructions with new paths

## Final Project Structure

```
chroma-mcp/
├── src/
│   ├── chroma_mcp/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── http_server.py
│   │   └── server.py
│   └── proxies/
│       ├── http_proxy.py
│       ├── direct_http_proxy.py
│       ├── functional_http_proxy.py
│       ├── simple_http_proxy.py
│       ├── websocket_http_proxy.py
│       └── filesystem_main.py
├── docker/
│   ├── http-proxy.Dockerfile
│   ├── filesystem.Dockerfile
│   ├── custom-chroma/
│   └── backups/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── test_output.txt
├── examples/
├── scripts/
├── docs/
│   └── archive/
├── config/
├── logs/
├── chroma_data/
├── specs/
├── Dockerfile
├── docker-compose.yaml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── SECURITY.md
├── pyproject.toml
├── uv.lock
├── .gitignore
├── CLAUDE.local.md
├── TODO.md
└── chroma-mcp.code-workspace
```

## Estimated Total Time: 3.5 hours

## Critical Success Criteria
1. `~/run-chroma-mcp.sh` continues to work without modification
2. Docker containers build and run successfully
3. All tests pass from new locations
4. No breaking changes to external integrations