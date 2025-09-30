# Testing ChromaDB Container

## Option 1: Using Python Client

1. Install the ChromaDB Python client:
   `
   pip install chromadb
   `

2. Run the test script:
   `
   python tests/integration/test_chroma.py
   `

3. If successful, you should see query results and a success message.

## Option 2: Using REST API

1. Install the requests library:
   `
   pip install requests
   `

2. Run the test script:
   `
   python tests/integration/test_api.py
   `

3. If successful, you should see confirmation messages for connection, collection creation, and document addition.

## Verifying Data Persistence

After running either test script:

1. Restart the ChromaDB container:
   `
   docker-compose restart chroma
   `

2. Run the test script again with a different collection name
   
3. Query the previously created collection to verify data persists across restarts

## Checking the Volume

To verify files are being written to the volume:

1. Inspect the Docker volume:
   `
   docker volume inspect chroma_chroma-data
   `

2. Check the data path (shown in the "Mountpoint" field in the inspection output)

3. Look for files in that directory - you should see database files if ChromaDB is correctly writing to the volume
