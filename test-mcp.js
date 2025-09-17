#!/usr/bin/env node

import { spawn } from 'child_process';
import path from 'path';

// Test MCP server configuration
const mcpServers = {
  "cloud-run": {
    command: "npx",
    args: ["-y", "@google-cloud/cloud-run-mcp"],
    env: {
      "GOOGLE_APPLICATION_CREDENTIALS": "/Users/foo/.config/gcloud/application_default_credentials.json",
      "GOOGLE_CLOUD_PROJECT": "sdk-ai-blog-writer",
      "GOOGLE_CLOUD_REGION": "us-central1",
      "DEFAULT_SERVICE_NAME": "api-blog-writer"
    }
  },
  "gcloud": {
    command: "npx", 
    args: ["-y", "@google-cloud/gcloud-mcp"],
    env: {
      "GOOGLE_APPLICATION_CREDENTIALS": "/Users/foo/.config/gcloud/application_default_credentials.json",
      "GOOGLE_CLOUD_PROJECT": "sdk-ai-blog-writer",
      "GOOGLE_CLOUD_REGION": "us-central1"
    }
  },
  "observability": {
    command: "npx",
    args: ["-y", "@google-cloud/observability-mcp"],
    env: {
      "GOOGLE_APPLICATION_CREDENTIALS": "/Users/foo/.config/gcloud/application_default_credentials.json",
      "GOOGLE_CLOUD_PROJECT": "sdk-ai-blog-writer",
      "GOOGLE_CLOUD_REGION": "us-central1"
    }
  }
};

async function testMCPServer(name, config) {
  console.log(`\n🧪 Testing ${name} MCP server...`);
  
  return new Promise((resolve) => {
    const child = spawn(config.command, config.args, {
      env: { ...process.env, ...config.env },
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let output = '';
    let error = '';

    child.stdout.on('data', (data) => {
      output += data.toString();
    });

    child.stderr.on('data', (data) => {
      error += data.toString();
    });

    child.on('close', (code) => {
      if (code === 0 || output.includes('MCP server') || output.includes('stdio transport connected')) {
        console.log(`✅ ${name}: Working`);
        console.log(`   Output: ${output.trim().substring(0, 100)}...`);
      } else {
        console.log(`❌ ${name}: Failed (exit code: ${code})`);
        if (error) console.log(`   Error: ${error.trim().substring(0, 100)}...`);
      }
      resolve();
    });

    // Send a test message and close
    setTimeout(() => {
      child.kill();
    }, 2000);
  });
}

async function main() {
  console.log('🔍 Testing MCP Server Configuration...');
  console.log('=====================================');
  
  for (const [name, config] of Object.entries(mcpServers)) {
    await testMCPServer(name, config);
  }
  
  console.log('\n✨ MCP Server testing complete!');
}

main().catch(console.error);
