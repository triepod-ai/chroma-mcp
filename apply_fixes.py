#!/usr/bin/env python3
import sys
import re

# Read the server.py file
with open('src/chroma_mcp/server.py', 'r') as f:
    content = f.read()

# Check if sys is imported, if not add it
if 'import sys' not in content:
    content = content.replace('import logging', 'import logging\nimport sys', 1)
    print("Added sys import")

# Fix 1: Add enhanced logging configuration with NullHandler
if 'null_handler = logging.NullHandler()' not in content:
    old_pattern = r'(logger\.addHandler\(file_handler\))\s*\n\s*\n\s*(# Prevent logging)'
    new_text = r'''\1

# Add NullHandler to prevent accidental console output
null_handler = logging.NullHandler()
logger.addHandler(null_handler)

\2'''
    content = re.sub(old_pattern, new_text, content)
    print("Added NullHandler")

# Fix 2: Add root logger management
if 'root_logger = logging.getLogger()' not in content:
    marker = '# Prevent logging from interfering with MCP protocol stdout/stderr\nlogger.propagate = False'
    if marker in content:
        content = content.replace(marker, marker + '''

# Root logger management - remove any StreamHandlers
root_logger = logging.getLogger()
if not root_logger.handlers:
    root_logger.addHandler(logging.NullHandler())
else:
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            root_logger.removeHandler(handler)''')
        print("Added root logger management")

# Fix 3: Add library logger isolation
if 'lib_logger.propagate = False' not in content:
    marker = "logging.getLogger('posthog').setLevel(logging.ERROR)"
    if marker in content:
        content = content.replace(marker, marker + '''

# Library logger isolation to prevent interference
for logger_name in ['chromadb', 'httpx', 'httpcore', 'posthog']:
    lib_logger = logging.getLogger(logger_name)
    lib_logger.propagate = False
    if not lib_logger.handlers:
        lib_logger.addHandler(logging.NullHandler())''')
        print("Added library logger isolation")

# Fix 4: Add stdout/stderr reconfiguration
if 'sys.stdout.reconfigure' not in content:
    # Find the FastMCP initialization
    marker = '# Initialize FastMCP server\nmcp = FastMCP'
    if marker in content:
        content = content.replace(marker, '''# Ensure proper buffering for MCP protocol
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Initialize FastMCP server
mcp = FastMCP''')
        print("Added stdout/stderr reconfiguration")

# Fix 5: Add test function at the end
if 'test_mcp_response' not in content:
    content = content.rstrip() + '''


@mcp.tool()
async def test_mcp_response() -> str:
    """
    Test function to verify MCP response output is working correctly.
    
    Returns:
        A test message to confirm tool responses are visible in Claude Desktop
    """
    return "MCP response test successful! If you can see this, tool responses are working."
'''
    print("Added test_mcp_response function")

# Write the fixed content
with open('src/chroma_mcp/server.py', 'w') as f:
    f.write(content)

print("✅ All fixes applied successfully!")
