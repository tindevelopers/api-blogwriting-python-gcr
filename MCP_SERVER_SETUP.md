# MCP Server Setup for Blog Writer SDK

This document describes the Model Context Protocol (MCP) server setup for the Blog Writer SDK project.

## Overview

The MCP server setup includes three servers:

### 1. Blog Writer SDK MCP Server
Provides tools for managing the Blog Writer SDK project, including:
- File operations (read, write, list)
- Deployment management
- Test execution
- Project health checks

### 2. Google Cloud MCP Server (Official)
Provides 17 Google Cloud tools for:
- Google Cloud Logging queries
- Cloud Spanner database operations
- Cloud Monitoring metrics
- Cloud Trace analysis
- Resource discovery and management

### 3. Google Cloud Run MCP Server (Official)
Provides Cloud Run deployment and management tools:
- Deploy files and folders to Cloud Run
- List and manage Cloud Run services
- Get service details and logs
- Create and manage GCP projects

## Installation

The MCP server has been installed at the local project level with the following components:

### Dependencies
- `@modelcontextprotocol/server-filesystem` - Core MCP server functionality
- `@modelcontextprotocol/sdk` - MCP SDK for TypeScript/JavaScript
- `google-cloud-mcp` - Official Google Cloud MCP server with 17 tools
- `@google-cloud/cloud-run-mcp` - Official Google Cloud Run MCP server for deployment

### Files Created
- `mcp-server.js` - Main MCP server implementation
- `package.json` - Node.js project configuration with MCP scripts
- `MCP_SERVER_SETUP.md` - This documentation

## Configuration

All three MCP servers have been added to your local MCP configuration files:

**Local MCP Configuration (`mcp.json` and `.cursor/mcp.json`):**
```json
{
  "mcpServers": {
    "google-cloud-mcp": {
      "command": "node",
      "args": ["node_modules/google-cloud-mcp/dist/index.js"],
      "cwd": "/Users/gene/Library/CloudStorage/OneDrive-TheInformationNetworkLtd/-PROGRAMMING/API-As-A-Service/api-blog-writer-python-gcr",
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/Users/gene/.config/gcloud/application_default_credentials.json",
        "GOOGLE_CLOUD_PROJECT": "sdk-ai-blog-writer",
        "GOOGLE_CLOUD_REGION": "us-central1"
      }
    },
    "cloud-run": {
      "command": "npx",
      "args": ["-y", "@google-cloud/cloud-run-mcp"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/Users/gene/.config/gcloud/application_default_credentials.json",
        "GOOGLE_CLOUD_PROJECT": "sdk-ai-blog-writer",
        "GOOGLE_CLOUD_REGION": "us-central1",
        "DEFAULT_SERVICE_NAME": "api-blog-writer-python-gcr"
      }
    }
  }
}
```

## Available Tools

### Blog Writer SDK MCP Server Tools

### 1. `read_project_file`
Read a file from the Blog Writer SDK project.
- **Parameters**: `path` (relative path from project root)
- **Example**: Read `main.py` or `requirements.txt`

### 2. `write_project_file`
Write content to a file in the Blog Writer SDK project.
- **Parameters**: `path`, `content`
- **Example**: Update configuration files or create new files

### 3. `list_project_files`
List files and directories in the Blog Writer SDK project.
- **Parameters**: `path` (optional, defaults to project root), `recursive` (boolean)
- **Example**: Browse project structure

### 4. `deploy_to_cloud_run`
Deploy the Blog Writer SDK to Google Cloud Run.
- **Parameters**: `environment` (dev, staging, prod)
- **Example**: Deploy to development environment

### 5. `run_tests`
Run the test suite for the Blog Writer SDK.
- **Parameters**: `test_path` (optional specific test)
- **Example**: Run all tests or specific test files

### 6. `check_project_health`
Check the health and status of the Blog Writer SDK project.
- **Parameters**: None
- **Example**: Verify all essential files are present

### Google Cloud MCP Server Tools (17 Available)

The official Google Cloud MCP server provides comprehensive tools for:

1. **Cloud Logging Tools**
   - `query-logs` - Query log entries across your Google Cloud resources
   - `logs-time-range` - Filter logs by severity, time range, and resource type
   - Correlate logs with traces for debugging

2. **Cloud Spanner Tools**
   - `execute-spanner-query` - Execute SQL queries against Spanner databases
   - `list-spanner-tables` - List database tables and schemas
   - `list-spanner-instances` - List Spanner instances
   - `list-spanner-databases` - List databases in instances
   - `natural-language-spanner-query` - Query using natural language
   - `spanner-query-count` - Count query results

3. **Cloud Monitoring Tools**
   - `query-metrics` - Retrieve metrics from Google Cloud services
   - `list-metric-types` - List available metric types
   - `natural-language-metrics-query` - Query metrics using natural language
   - Create and manage alerting policies
   - Monitor resource utilization and performance

4. **Cloud Trace Tools**
   - `get-trace` - Analyze distributed traces across services
   - `list-traces` - List recent traces with filtering
   - `find-traces-from-logs` - Find traces associated with logs
   - `natural-language-trace-query` - Query traces using natural language
   - Identify performance bottlenecks
   - Correlate traces with logs and metrics

5. **Resource Discovery Tools**
   - `set-project-id` - Set the active Google Cloud project
   - `get-project-id` - Get the current project ID
   - List and discover Google Cloud resources
   - Get resource metadata and configurations
   - Manage resource relationships

### Google Cloud Run MCP Server Tools

The official Google Cloud Run MCP server provides deployment and management tools:

1. **Deployment Tools**
   - `deploy-file-contents` - Deploy files to Cloud Run by providing their contents directly
   - `deploy-local-folder` - Deploy a local folder to a Google Cloud Run service (local only)

2. **Service Management Tools**
   - `list-services` - List Cloud Run services in a given project and region
   - `get-service` - Get details for a specific Cloud Run service
   - `get-service-log` - Get logs and error messages for a specific Cloud Run service

3. **Project Management Tools** (local only)
   - `list-projects` - List available GCP projects
   - `create-project` - Create a new GCP project and attach it to the first available billing account

4. **Prompts**
   - `deploy` - Deploy the current working directory to Cloud Run
   - `logs` - Get the logs for a Cloud Run service

## Usage

### Starting the MCP Server
```bash
# From the project root
npm run mcp-server
# or
node mcp-server.js
```

### Testing the MCP Server
```bash
# Run the test script
node test-local-mcp.js
```

## Integration with Cursor

The MCP server is now integrated with Cursor and will be available when you:
1. Restart Cursor
2. Open this project
3. Use the MCP tools through the Cursor interface

## Google Cloud Run Deployment

The MCP server includes tools for deploying to Google Cloud Run:
- Uses existing deployment scripts in the `scripts/` directory
- Supports multiple environments (dev, staging, prod)
- Integrates with the project's Cloud Run configuration

## Troubleshooting

### Common Issues

1. **Module type warning**: Fixed by adding `"type": "module"` to `package.json`
2. **Permission errors**: Ensure `mcp-server.js` is executable (`chmod +x mcp-server.js`)
3. **Path issues**: Verify the `cwd` path in the MCP configuration matches your project location

### Verification

To verify the MCP server is working:
1. Run `node test-local-mcp.js` - should show "MCP Server test PASSED"
