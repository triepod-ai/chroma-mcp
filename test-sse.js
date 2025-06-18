#!/usr/bin/env node

// Simple SSE client test for Chroma MCP
const EventSource = require('eventsource');

const sseUrl = 'http://localhost:3633/sse';

console.log('🧪 Testing Chroma MCP SSE Server');
console.log('================================');
console.log(`Connecting to: ${sseUrl}`);
console.log('');

const eventSource = new EventSource(sseUrl);

eventSource.onopen = function(event) {
    console.log('✅ SSE connection opened');
};

eventSource.onmessage = function(event) {
    console.log('📨 Received message:', event.data);
    try {
        const data = JSON.parse(event.data);
        console.log('📋 Parsed data:', JSON.stringify(data, null, 2));
    } catch (e) {
        console.log('📋 Raw data:', event.data);
    }
};

eventSource.onerror = function(event) {
    console.error('❌ SSE error:', event);
};

// Test for 10 seconds then close
setTimeout(() => {
    console.log('');
    console.log('🔚 Closing connection after test');
    eventSource.close();
    process.exit(0);
}, 10000);