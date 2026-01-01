## V2 Standardized API Endpoints

This section outlines the reusable endpoint structure for managing multiple APIs in a multi-tenant setup.

### Standardized Endpoint Template
- **Base Path:** `/api/{provider_id}` (e.g., `/api/dataforseo`)
- **Common Operations:**
  - GET `/api/{provider_id}`: Retrieve provider info
  - POST `/api/{provider_id}/credentials`: Add credentials
  - PUT `/api/{provider_id}/credentials`: Update credentials
  - DELETE `/api/{provider_id}/credentials`: Remove credentials
  - POST `/api/{provider_id}/credentials/test`: Validate credentials

## API Security and Protection

To protect your API, use a layered approach:
- **Authentication**: Implement JWT or OAuth tokens.
- **API Gateway**: Use Google Cloud API Gateway for rate limits and quotas.
- **Supabase**: Handle tenant-specific credentials with Row-Level Security.
