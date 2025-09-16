#!/usr/bin/env node

/**
 * Test script for local MCP server
 * This script tests the Google Cloud MCP server locally
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('🧪 Testing Local Google Cloud MCP Server...\n');

// Test the Google Cloud MCP server
const mcpServer = spawn('node', [
  join(__dirname, 'node_modules/google-cloud-mcp/dist/index.js')
], {
  stdio: ['pipe', 'pipe', 'pipe'],
  env: {
    ...process.env,
    GOOGLE_APPLICATION_CREDENTIALS: '/Users/gene/.config/gcloud/application_default_credentials.json',
    GOOGLE_CLOUD_PROJECT: 'sdk-ai-blog-writer',
    GOOGLE_CLOUD_REGION: 'us-central1'
  }
});

// Send a tools/list request
const request = {
  jsonrpc: '2.0',
  id: 1,
  method: 'tools/list'
};

console.log('📤 Sending tools/list request...');
mcpServer.stdin.write(JSON.stringify(request) + '\n');

let output = '';
let errorOutput = '';

mcpServer.stdout.on('data', (data) => {
  output += data.toString();
});

mcpServer.stderr.on('data', (data) => {
  errorOutput += data.toString();
});

mcpServer.on('close', (code) => {
  console.log('\n📥 Server Response:');
  try {
    const response = JSON.parse(output);
    if (response.result && response.result.tools) {
      console.log(`✅ Found ${response.result.tools.length} Google Cloud MCP tools:`);
      response.result.tools.forEach((tool, index) => {
        console.log(`   ${index + 1}. ${tool.name}`);
      });
    } else {
      console.log('❌ No tools found in response');
    }
  } catch (e) {
    console.log('❌ Failed to parse response:', e.message);
    console.log('Raw output:', output);
  }
  
  if (errorOutput) {
    console.log('\n📋 Server Logs:');
    console.log(errorOutput);
  }
  
  console.log(`\n🏁 Test completed with exit code: ${code}`);
});

// Kill the server after 5 seconds
setTimeout(() => {
  mcpServer.kill();
}, 5000);
