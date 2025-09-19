# Secure Credential Management Architecture
## Multi-Tenant API Credential Management System

### 📋 **Overview**
This document provides a standardized, phased approach for implementing secure credential management across all APIs in the system. The goal is to enable the Vercel frontend to provide a single, consistent interface for tenants to manage their credentials for any API service.

---

## 🎯 **System Architecture Goals**

### **Primary Objectives:**
- **Single Frontend Interface**: Vercel provides one consistent UI for all API credential management
- **Standardized Backend Pattern**: Each API follows the same credential management architecture
- **Tenant Isolation**: Each tenant can securely manage their own credentials
- **Scalable System**: Easy to add new APIs following the same pattern

### **Key Benefits:**
- ✅ Consistent User Experience across all APIs
- ✅ Reduced Development Time with reusable patterns
- ✅ Enhanced Security with standardized practices
- ✅ Easy Maintenance with one system to manage all credential flows

---

## 🏗️ **Master Architecture**

### **System Components:**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Vercel        │    │   Blog Writer    │    │   External      │
│   Frontend      │◄──►│   API Service    │◄──►│   APIs          │
│   (Tenant UI)   │    │   (Credential    │    │   (DataforSEO,  │
│                 │    │    Manager)      │    │    OpenAI, etc) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Google Secret  │
                       │   Manager        │
                       │   (Encrypted     │
                       │    Storage)      │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Supabase DB    │
                       │   (Metadata &    │
                       │    References)   │
                       └──────────────────┘
```

---

## 📊 **Implementation Phases**

### **Phase 1: Core Infrastructure Setup**
**Duration: 1-2 weeks**

#### **1.1 Database Schema Setup**
```sql
-- Tenants Table
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(100) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  settings JSONB DEFAULT '{}',
  status VARCHAR(50) DEFAULT 'active',
  subscription_tier VARCHAR(50) DEFAULT 'basic'
);

-- Tenant Credentials Table
CREATE TABLE tenant_credentials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  provider VARCHAR(100) NOT NULL, -- 'dataforseo', 'openai', 'anthropic', 'azure'
  secret_name VARCHAR(255) NOT NULL, -- Google Secret Manager reference
  is_active BOOLEAN DEFAULT true,
  last_tested TIMESTAMP,
  test_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'success', 'failed'
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(tenant_id, provider)
);

-- Credential Usage Logs
CREATE TABLE credential_usage_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  provider VARCHAR(100) NOT NULL,
  endpoint VARCHAR(255) NOT NULL,
  request_count INTEGER DEFAULT 1,
  success_count INTEGER DEFAULT 0,
  error_count INTEGER DEFAULT 0,
  last_used TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### **1.2 Google Secret Manager Setup**
```bash
# Create IAM roles for credential management
gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:[SERVICE_ACCOUNT]" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:[SERVICE_ACCOUNT]" \
  --role="roles/secretmanager.secretVersionManager"
```

#### **1.3 Base Credential Service**
```python
# src/blog_writer_sdk/services/credential_service.py
class TenantCredentialService:
    """Base service for managing tenant credentials securely."""
    
    def __init__(self, supabase_client, secret_manager_client):
        self.supabase = supabase_client
        self.secret_manager = secret_manager_client
    
    async def store_credentials(self, tenant_id: str, provider: str, credentials: dict):
        """Store encrypted credentials for a tenant."""
        pass
    
    async def get_credentials(self, tenant_id: str, provider: str):
        """Retrieve and decrypt credentials for a tenant."""
        pass
    
    async def test_credentials(self, tenant_id: str, provider: str):
        """Test credentials by making a validation API call."""
        pass
    
    async def delete_credentials(self, tenant_id: str, provider: str):
        """Securely delete tenant credentials."""
        pass
```

---

### **Phase 2: First API Implementation (DataforSEO)**
**Duration: 2-3 weeks**

#### **2.1 DataforSEO Credential Management**
```python
# src/blog_writer_sdk/services/dataforseo_credential_service.py
class DataForSEOCredentialService(TenantCredentialService):
    """DataforSEO specific credential management."""
    
    async def validate_credentials(self, api_key: str, api_secret: str) -> bool:
        """Test DataforSEO API credentials."""
        try:
            # Make test API call to validate credentials
            test_url = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"
            # Implementation details...
            return True
        except Exception:
            return False
    
    async def get_usage_stats(self, tenant_id: str) -> dict:
        """Get DataforSEO usage statistics for tenant."""
        pass
```

#### **2.2 API Endpoints for DataforSEO**
```python
# API Endpoints to implement:
@app.post("/api/v1/tenants/{tenant_id}/credentials/dataforseo")
async def store_dataforseo_credentials(tenant_id: str, credentials: DataForSEOCredentials):
    """Store DataforSEO credentials for tenant."""

@app.get("/api/v1/tenants/{tenant_id}/credentials/dataforseo")
async def get_dataforseo_credentials(tenant_id: str):
    """Get DataforSEO credential status (no actual credentials returned)."""

@app.post("/api/v1/tenants/{tenant_id}/credentials/dataforseo/test")
async def test_dataforseo_credentials(tenant_id: str):
    """Test DataforSEO credentials."""

@app.delete("/api/v1/tenants/{tenant_id}/credentials/dataforseo")
async def delete_dataforseo_credentials(tenant_id: str):
    """Delete DataforSEO credentials."""
```

#### **2.3 Frontend Integration (Vercel/Next.js)**
```javascript
// components/DataForSEOConfig.jsx
const DataForSEOConfig = ({ tenantId }) => {
  const [credentials, setCredentials] = useState({
    apiKey: '',
    apiSecret: ''
  });
  const [status, setStatus] = useState('pending');
  const [testing, setTesting] = useState(false);

  const handleSave = async () => {
    const response = await fetch(`/api/v1/tenants/${tenantId}/credentials/dataforseo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    
    if (response.ok) {
      setStatus('saved');
    }
  };

  const handleTest = async () => {
    setTesting(true);
    const response = await fetch(`/api/v1/tenants/${tenantId}/credentials/dataforseo/test`, {
      method: 'POST'
    });
    
    const result = await response.json();
    setStatus(result.status);
    setTesting(false);
  };

  return (
    <div className="credential-config">
      <h3>DataforSEO Configuration</h3>
      <input 
        type="password" 
        placeholder="API Key"
        value={credentials.apiKey}
        onChange={(e) => setCredentials({...credentials, apiKey: e.target.value})}
      />
      <input 
        type="password" 
        placeholder="API Secret"
        value={credentials.apiSecret}
        onChange={(e) => setCredentials({...credentials, apiSecret: e.target.value})}
      />
      <button onClick={handleSave}>Save</button>
      <button onClick={handleTest} disabled={testing}>
        {testing ? 'Testing...' : 'Test'}
      </button>
      <div className={`status ${status}`}>
        Status: {status}
      </div>
    </div>
  );
};
```

---

### **Phase 3: Additional API Integrations**
**Duration: 2-3 weeks per API**

#### **3.1 OpenAI Integration**
```python
# src/blog_writer_sdk/services/openai_credential_service.py
class OpenAICredentialService(TenantCredentialService):
    async def validate_credentials(self, api_key: str) -> bool:
        """Test OpenAI API credentials."""
        try:
            # Test with OpenAI API
            response = await openai_client.models.list()
            return True
        except Exception:
            return False
```

#### **3.2 Anthropic Integration**
```python
# src/blog_writer_sdk/services/anthropic_credential_service.py
class AnthropicCredentialService(TenantCredentialService):
    async def validate_credentials(self, api_key: str) -> bool:
        """Test Anthropic API credentials."""
        # Implementation for Anthropic validation
        pass
```

#### **3.3 Azure OpenAI Integration**
```python
# src/blog_writer_sdk/services/azure_credential_service.py
class AzureOpenAICredentialService(TenantCredentialService):
    async def validate_credentials(self, endpoint: str, api_key: str, api_version: str) -> bool:
        """Test Azure OpenAI credentials."""
        # Implementation for Azure validation
        pass
```

---

### **Phase 4: Advanced Features**
**Duration: 2-3 weeks**

#### **4.1 Usage Monitoring & Analytics**
```python
@app.get("/api/v1/tenants/{tenant_id}/analytics")
async def get_tenant_analytics(tenant_id: str):
    """Get comprehensive analytics for tenant."""
    return {
        "api_usage": await get_api_usage_stats(tenant_id),
        "cost_analysis": await get_cost_analysis(tenant_id),
        "performance_metrics": await get_performance_metrics(tenant_id)
    }
```

#### **4.2 Credential Rotation**
```python
@app.post("/api/v1/tenants/{tenant_id}/credentials/{provider}/rotate")
async def rotate_credentials(tenant_id: str, provider: str):
    """Rotate credentials for enhanced security."""
    pass
```

#### **4.3 Bulk Operations**
```python
@app.post("/api/v1/tenants/{tenant_id}/credentials/bulk-test")
async def bulk_test_credentials(tenant_id: str):
    """Test all configured credentials for a tenant."""
    pass
```

---

## 🔐 **Security Standards**

### **Non-Negotiable Security Requirements:**

#### **1. Data Encryption**
- All credentials encrypted before storage
- Use Google Secret Manager encryption
- No plaintext credentials in logs or databases

#### **2. Access Control**
- Tenant isolation enforced at database level
- JWT tokens with tenant-specific claims
- Role-based access control (RBAC)

#### **3. Input Validation**
- Validate all input parameters
- Sanitize credential data
- Implement rate limiting per tenant

#### **4. Audit Logging**
- Log all credential operations
- Monitor for suspicious activity
- Regular security audits

#### **5. Credential Testing**
- Test all credentials before activation
- Regular validation of active credentials
- Automatic deactivation of failed credentials

---

## 📋 **Implementation Checklist**

### **For Each New API:**

#### **Backend Requirements:**
- [ ] Create provider-specific credential service
- [ ] Implement credential validation logic
- [ ] Add API endpoints for CRUD operations
- [ ] Implement usage tracking and monitoring
- [ ] Add error handling and logging
- [ ] Create database migrations
- [ ] Write comprehensive tests

#### **Frontend Requirements:**
- [ ] Create credential configuration component
- [ ] Implement credential testing functionality
- [ ] Add status indicators and feedback
- [ ] Create usage analytics display
- [ ] Implement error handling and notifications
- [ ] Add responsive design for mobile

#### **Security Requirements:**
- [ ] Encrypt credentials before storage
- [ ] Implement tenant isolation
- [ ] Add input validation and sanitization
- [ ] Create audit logging
- [ ] Implement rate limiting
- [ ] Add credential rotation capability

#### **Testing Requirements:**
- [ ] Unit tests for credential service
- [ ] Integration tests for API endpoints
- [ ] End-to-end tests for frontend components
- [ ] Security testing for credential handling
- [ ] Performance testing for bulk operations

---

## 🎯 **API-Specific Templates**

### **Template for New API Integration:**

#### **1. Credential Service Template**
```python
# src/blog_writer_sdk/services/{provider}_credential_service.py
class {Provider}CredentialService(TenantCredentialService):
    """{Provider} specific credential management."""
    
    def __init__(self, supabase_client, secret_manager_client):
        super().__init__(supabase_client, secret_manager_client)
        self.provider_name = "{provider}"
    
    async def validate_credentials(self, **credentials) -> bool:
        """Test {Provider} API credentials."""
        try:
            # Implement provider-specific validation
            # Make test API call
            return True
        except Exception as e:
            logger.error(f"Credential validation failed: {e}")
            return False
    
    async def get_usage_stats(self, tenant_id: str) -> dict:
        """Get {Provider} usage statistics for tenant."""
        # Implement usage tracking
        pass
```

#### **2. API Endpoints Template**
```python
# Add to main.py
@app.post("/api/v1/tenants/{tenant_id}/credentials/{provider}")
async def store_{provider}_credentials(tenant_id: str, credentials: {Provider}Credentials):
    """Store {Provider} credentials for tenant."""

@app.get("/api/v1/tenants/{tenant_id}/credentials/{provider}")
async def get_{provider}_credentials(tenant_id: str):
    """Get {Provider} credential status."""

@app.post("/api/v1/tenants/{tenant_id}/credentials/{provider}/test")
async def test_{provider}_credentials(tenant_id: str):
    """Test {Provider} credentials."""

@app.delete("/api/v1/tenants/{tenant_id}/credentials/{provider}")
async def delete_{provider}_credentials(tenant_id: str):
    """Delete {Provider} credentials."""
```

#### **3. Frontend Component Template**
```javascript
// components/{Provider}Config.jsx
const {Provider}Config = ({ tenantId }) => {
  // Implementation following DataforSEO pattern
  // Adapt credential fields for specific provider
  // Include provider-specific validation
};
```

---

## 📊 **Monitoring & Analytics**

### **Key Metrics to Track:**
- Credential usage per tenant
- API response times and success rates
- Cost analysis per provider
- Error rates and types
- Security events and anomalies

### **Dashboard Requirements:**
- Real-time credential status
- Usage analytics and trends
- Cost tracking and projections
- Performance metrics
- Security alerts and notifications

---

## 🚀 **Deployment Strategy**

### **Environment-Specific Configuration:**
- **Development**: Use test credentials and mock services
- **Staging**: Use limited real credentials for testing
- **Production**: Full security and monitoring enabled

### **Rollout Plan:**
1. Deploy core infrastructure to all environments
2. Implement DataforSEO as pilot API
3. Test with limited tenant set
4. Roll out to all tenants
5. Add additional APIs incrementally

---

## 📚 **Documentation Requirements**

### **For Each API:**
- API endpoint documentation
- Credential setup instructions
- Troubleshooting guides
- Security best practices
- Usage examples and code samples

### **For Frontend:**
- Component usage documentation
- Integration guides
- Error handling patterns
- Testing procedures
- Deployment instructions

---

## ✅ **Success Criteria**

### **Technical Success:**
- All credentials encrypted and secure
- Tenant isolation properly implemented
- API endpoints working correctly
- Frontend components functional
- Comprehensive test coverage

### **Business Success:**
- Tenants can easily manage credentials
- Reduced support requests
- Improved security posture
- Scalable system for future APIs
- Consistent user experience

---

## 🔄 **Maintenance & Updates**

### **Regular Tasks:**
- Security audits and updates
- Credential rotation reminders
- Usage analytics reviews
- Performance optimization
- Documentation updates

### **Monitoring Alerts:**
- Failed credential tests
- Unusual usage patterns
- Security violations
- Performance degradation
- System errors

---

*This document serves as the master template for implementing secure credential management across all APIs in the system. Each API implementation should follow this standardized approach to ensure consistency, security, and scalability.*
