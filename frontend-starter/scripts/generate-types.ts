import openapiTS from 'openapi-typescript';
import fs from 'fs';
import path from 'path';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 
  'https://blog-writer-api-dev-613248238610.europe-west9.run.app';

async function generateTypes() {
  console.log('🔄 Fetching OpenAPI schema from:', BACKEND_URL);
  
  try {
    const output = await openapiTS(`${BACKEND_URL}/openapi.json`, {
      exportType: true,
      pathParamsAsTypes: true,
    });
    
    const outputDir = path.join(process.cwd(), 'lib/api');
    const outputPath = path.join(outputDir, 'types.ts');
    
    // Ensure directory exists
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    fs.writeFileSync(outputPath, output);
    
    console.log('✅ Generated TypeScript types at:', outputPath);
    console.log('📦 Types are now available for import:');
    console.log('   import type { paths, components } from "@/lib/api/types"');
  } catch (error) {
    console.error('❌ Failed to generate types:', error);
    process.exit(1);
  }
}

generateTypes();

