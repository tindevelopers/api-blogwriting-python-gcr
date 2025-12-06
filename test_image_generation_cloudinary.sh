#!/bin/bash

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Image Generation & Cloudinary Upload Test${NC}"
echo -e "${BLUE}Target Size: 240x350 pixels (using closest valid: 832x1216)${NC}"
echo -e "${BLUE}============================================================${NC}"

# API Endpoint (Cloud Run URL)
API_URL="${API_URL:-https://blog-writer-api-dev-kq42l26tuq-od.a.run.app}"
GENERATE_ENDPOINT="${API_URL}/api/v1/images/generate"
UPLOAD_ENDPOINT="${API_URL}/api/v1/media/upload/cloudinary"

# Image Generation Parameters
PROMPT="A serene landscape with mountains and a lake at sunset"
# Note: Stability AI SDXL model only supports specific dimensions
# Target: 240x350 (aspect ratio ~0.686 portrait)
# Closest valid SDXL dimension: 832x1216 (aspect ratio 0.684)
# Valid SDXL dimensions: 1024x1024, 1152x896, 1216x832, 1344x768, 1536x640,
#                        640x1536, 768x1344, 832x1216, 896x1152
WIDTH=832
HEIGHT=1216
QUALITY="draft"  # Use draft for faster generation during testing

echo -e "${BLUE}Test Parameters:${NC}"
echo -e "${BLUE}Prompt: ${PROMPT}${NC}"
echo -e "${BLUE}Dimensions: ${WIDTH}x${HEIGHT} pixels${NC}"
echo -e "${BLUE}Quality: ${QUALITY}${NC}"

# --- STEP 1: Generate Image ---
echo -e "\n${BLUE}============================================================${NC}"
echo -e "${BLUE}STEP 1: Generate Image (${WIDTH}x${HEIGHT})${NC}"
echo -e "${BLUE}============================================================${NC}"

GENERATE_PAYLOAD=$(jq -n \
    --arg prompt "$PROMPT" \
    --argjson width "$WIDTH" \
    --argjson height "$HEIGHT" \
    --arg quality "$QUALITY" \
    --arg aspect_ratio "custom" \
    '{
        prompt: $prompt,
        width: $width,
        height: $height,
        aspect_ratio: $aspect_ratio,
        quality: $quality,
        provider: "stability_ai"
    }')

echo -e "${BLUE}📡 Requesting image generation...${NC}"
echo -e "${BLUE}Endpoint: ${GENERATE_ENDPOINT}${NC}"

START_TIME=$(date +%s)
GENERATE_RESPONSE=$(curl -s -X POST "$GENERATE_ENDPOINT" \
    -H "Content-Type: application/json" \
    -d "$GENERATE_PAYLOAD")
END_TIME=$(date +%s)
GENERATION_TIME=$((END_TIME - START_TIME))

# Check if generation was successful
SUCCESS=$(echo "$GENERATE_RESPONSE" | jq -r '.success // false')
ERROR_MESSAGE=$(echo "$GENERATE_RESPONSE" | jq -r '.error_message // empty')

if [ "$SUCCESS" != "true" ]; then
    echo -e "${RED}❌ Image generation failed!${NC}"
    echo -e "${YELLOW}Error: ${ERROR_MESSAGE}${NC}"
    echo -e "${YELLOW}Response: ${GENERATE_RESPONSE::500}...${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Image Generated Successfully!${NC}"
echo -e "${BLUE}Generation Time: ${GENERATION_TIME} seconds${NC}"

# Extract image data (save to temp file to avoid argument list too long error)
TEMP_JSON=$(mktemp)
echo "$GENERATE_RESPONSE" > "$TEMP_JSON"

IMAGE_DATA=$(jq -r '.images[0].image_data // empty' "$TEMP_JSON")
IMAGE_ID=$(jq -r '.images[0].image_id // empty' "$TEMP_JSON")
ACTUAL_WIDTH=$(jq -r '.images[0].width // 0' "$TEMP_JSON")
ACTUAL_HEIGHT=$(jq -r '.images[0].height // 0' "$TEMP_JSON")
IMAGE_FORMAT=$(jq -r '.images[0].format // "png"' "$TEMP_JSON")
SIZE_BYTES=$(jq -r '.images[0].size_bytes // 0' "$TEMP_JSON")
COST=$(jq -r '.cost // 0' "$TEMP_JSON")
PROVIDER=$(jq -r '.provider // "unknown"' "$TEMP_JSON")
MODEL=$(jq -r '.model // "unknown"' "$TEMP_JSON")

echo -e "\n${BLUE}Generated Image Details:${NC}"
echo -e "${BLUE}Image ID: ${IMAGE_ID}${NC}"
echo -e "${BLUE}Dimensions: ${ACTUAL_WIDTH}x${ACTUAL_HEIGHT} pixels${NC}"
echo -e "${BLUE}Format: ${IMAGE_FORMAT}${NC}"
echo -e "${BLUE}Size: ${SIZE_BYTES} bytes ($(echo "scale=2; $SIZE_BYTES / 1024" | bc) KB)${NC}"
echo -e "${BLUE}Provider: ${PROVIDER}${NC}"
echo -e "${BLUE}Model: ${MODEL}${NC}"
printf "${BLUE}Cost: $%.5f${NC}\n" "$COST"

# Verify dimensions
if [ "$ACTUAL_WIDTH" -eq "$WIDTH" ] && [ "$ACTUAL_HEIGHT" -eq "$HEIGHT" ]; then
    echo -e "${GREEN}✓ Dimensions match target (${WIDTH}x${HEIGHT})${NC}"
else
    echo -e "${YELLOW}⚠ Dimensions differ from target (got ${ACTUAL_WIDTH}x${ACTUAL_HEIGHT}, expected ${WIDTH}x${HEIGHT})${NC}"
fi

if [ -z "$IMAGE_DATA" ]; then
    echo -e "${RED}❌ No image data in response!${NC}"
    echo -e "${YELLOW}Response: ${GENERATE_RESPONSE::1000}...${NC}"
    exit 1
fi

# Check if image_data has data: prefix (base64 with MIME type)
if [[ "$IMAGE_DATA" == data:* ]]; then
    # Extract base64 part after comma
    IMAGE_DATA=$(echo "$IMAGE_DATA" | cut -d',' -f2)
fi

IMAGE_DATA_LENGTH=${#IMAGE_DATA}
echo -e "${BLUE}Image Data Length: ${IMAGE_DATA_LENGTH} characters${NC}"

# --- STEP 2: Upload to Cloudinary ---
echo -e "\n${BLUE}============================================================${NC}"
echo -e "${BLUE}STEP 2: Upload Image to Cloudinary${NC}"
echo -e "${BLUE}============================================================${NC}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="test_image_${WIDTH}x${HEIGHT}_${TIMESTAMP}.${IMAGE_FORMAT}"
FOLDER="test-images"

# Create upload payload file using Python to handle large base64 strings
UPLOAD_PAYLOAD_FILE=$(mktemp)
# Save base64 data to temp file first
BASE64_TEMP=$(mktemp)
echo "$IMAGE_DATA" > "$BASE64_TEMP"

python3 << EOF > "$UPLOAD_PAYLOAD_FILE"
import json
from datetime import datetime

# Read base64 data from temp file
with open("${BASE64_TEMP}", "r") as f:
    image_data = f.read().strip()

payload = {
    "media_data": image_data,
    "filename": "${FILENAME}",
    "folder": "${FOLDER}",
    "alt_text": "Test image ${WIDTH}x${HEIGHT} - ${PROMPT}",
    "metadata": {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "dimensions": "${WIDTH}x${HEIGHT}",
        "provider": "${PROVIDER}",
        "model": "${MODEL}",
        "test": True
    }
}

print(json.dumps(payload))
EOF

# Clean up base64 temp file
rm -f "$BASE64_TEMP"

echo -e "${BLUE}📡 Uploading to Cloudinary...${NC}"
echo -e "${BLUE}Filename: ${FILENAME}${NC}"
echo -e "${BLUE}Folder: ${FOLDER}${NC}"
echo -e "${BLUE}Endpoint: ${UPLOAD_ENDPOINT}${NC}"

START_TIME=$(date +%s)
UPLOAD_RESPONSE=$(curl -s -X POST "$UPLOAD_ENDPOINT" \
    -H "Content-Type: application/json" \
    -d @"$UPLOAD_PAYLOAD_FILE")
END_TIME=$(date +%s)
UPLOAD_TIME=$((END_TIME - START_TIME))

# Clean up temp files
rm -f "$TEMP_JSON" "$UPLOAD_PAYLOAD_FILE" "$BASE64_TEMP" 2>/dev/null

# Check if upload was successful
UPLOAD_SUCCESS=$(echo "$UPLOAD_RESPONSE" | jq -r '.success // false')
UPLOAD_ERROR=$(echo "$UPLOAD_RESPONSE" | jq -r '.detail // empty')

if [ "$UPLOAD_SUCCESS" != "true" ]; then
    echo -e "${RED}❌ Cloudinary upload failed!${NC}"
    if [ -n "$UPLOAD_ERROR" ]; then
        echo -e "${YELLOW}Error: ${UPLOAD_ERROR}${NC}"
    fi
    echo -e "${YELLOW}Response: ${UPLOAD_RESPONSE::500}...${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Image Uploaded to Cloudinary Successfully!${NC}"
echo -e "${BLUE}Upload Time: ${UPLOAD_TIME} seconds${NC}"

# Extract Cloudinary details
CLOUDINARY_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.result.id // empty')
CLOUDINARY_URL=$(echo "$UPLOAD_RESPONSE" | jq -r '.result.url // empty')
CLOUDINARY_WIDTH=$(echo "$UPLOAD_RESPONSE" | jq -r '.result.width // 0')
CLOUDINARY_HEIGHT=$(echo "$UPLOAD_RESPONSE" | jq -r '.result.height // 0')
CLOUDINARY_FORMAT=$(echo "$UPLOAD_RESPONSE" | jq -r '.result.format // "unknown"')
CLOUDINARY_SIZE=$(echo "$UPLOAD_RESPONSE" | jq -r '.result.size // 0')
CLOUDINARY_CREATED=$(echo "$UPLOAD_RESPONSE" | jq -r '.result.created_at // empty')
TRANSFORMATION_URL=$(echo "$UPLOAD_RESPONSE" | jq -r '.result.transformation_url // empty')

echo -e "\n${BLUE}Cloudinary Storage Details:${NC}"
echo -e "${BLUE}Public ID: ${CLOUDINARY_ID}${NC}"
echo -e "${BLUE}URL: ${CLOUDINARY_URL}${NC}"
echo -e "${BLUE}Dimensions: ${CLOUDINARY_WIDTH}x${CLOUDINARY_HEIGHT} pixels${NC}"
echo -e "${BLUE}Format: ${CLOUDINARY_FORMAT}${NC}"
echo -e "${BLUE}Size: ${CLOUDINARY_SIZE} bytes ($(echo "scale=2; $CLOUDINARY_SIZE / 1024" | bc) KB)${NC}"
if [ -n "$CLOUDINARY_CREATED" ]; then
    echo -e "${BLUE}Created At: ${CLOUDINARY_CREATED}${NC}"
fi
if [ -n "$TRANSFORMATION_URL" ]; then
    echo -e "${BLUE}Transformation URL: ${TRANSFORMATION_URL}${NC}"
fi

# --- STEP 3: How Image is Saved ---
echo -e "\n${BLUE}============================================================${NC}"
echo -e "${BLUE}STEP 3: How Image is Saved on Cloudinary${NC}"
echo -e "${BLUE}============================================================${NC}"

echo -e "${BLUE}Storage Structure:${NC}"
echo -e "${BLUE}  Folder: ${FOLDER}${NC}"
echo -e "${BLUE}  Public ID: ${CLOUDINARY_ID}${NC}"
echo -e "${BLUE}  Full Path: ${FOLDER}/${CLOUDINARY_ID}${NC}"

echo -e "\n${BLUE}Cloudinary URL Structure:${NC}"
echo -e "${BLUE}  Base URL: https://res.cloudinary.com/{cloud_name}/image/upload${NC}"
echo -e "${BLUE}  Full URL: ${CLOUDINARY_URL}${NC}"

echo -e "\n${BLUE}Image Properties:${NC}"
echo -e "${BLUE}  - Auto-optimized quality and format${NC}"
echo -e "${BLUE}  - CDN delivery enabled${NC}"
echo -e "${BLUE}  - Transformations available via URL parameters${NC}"
echo -e "${BLUE}  - Metadata preserved${NC}"

# --- SUMMARY ---
echo -e "\n${BLUE}============================================================${NC}"
echo -e "${BLUE}SUMMARY${NC}"
echo -e "${BLUE}============================================================${NC}"

echo -e "${BLUE}✓ Image Generation:${NC}"
echo -e "${BLUE}  - Dimensions: ${ACTUAL_WIDTH}x${ACTUAL_HEIGHT}${NC}"
echo -e "${BLUE}  - Format: ${IMAGE_FORMAT}${NC}"
echo -e "${BLUE}  - Size: $(echo "scale=2; $SIZE_BYTES / 1024" | bc) KB${NC}"
echo -e "${BLUE}  - Generation Time: ${GENERATION_TIME}s${NC}"
printf "${BLUE}  - Cost: $%.5f${NC}\n" "$COST"

echo -e "\n${BLUE}✓ Cloudinary Upload:${NC}"
echo -e "${BLUE}  - Public ID: ${CLOUDINARY_ID}${NC}"
echo -e "${BLUE}  - Folder: ${FOLDER}${NC}"
echo -e "${BLUE}  - Upload Time: ${UPLOAD_TIME}s${NC}"
echo -e "${BLUE}  - URL: ${CLOUDINARY_URL}${NC}"

echo -e "\n${GREEN}============================================================${NC}"
echo -e "${GREEN}Test completed successfully!${NC}"
echo -e "${GREEN}============================================================${NC}"

# Save results to file
RESULTS_FILE="image_generation_test_results_${TIMESTAMP}.json"
{
    echo "{"
    echo "  \"generation\": {"
    echo "    \"success\": true,"
    echo "    \"image_id\": \"${IMAGE_ID}\","
    echo "    \"dimensions\": \"${ACTUAL_WIDTH}x${ACTUAL_HEIGHT}\","
    echo "    \"format\": \"${IMAGE_FORMAT}\","
    echo "    \"size_bytes\": ${SIZE_BYTES},"
    echo "    \"generation_time_seconds\": ${GENERATION_TIME},"
    echo "    \"cost\": ${COST},"
    echo "    \"provider\": \"${PROVIDER}\","
    echo "    \"model\": \"${MODEL}\""
    echo "  },"
    echo "  \"cloudinary\": {"
    echo "    \"success\": true,"
    echo "    \"public_id\": \"${CLOUDINARY_ID}\","
    echo "    \"url\": \"${CLOUDINARY_URL}\","
    echo "    \"folder\": \"${FOLDER}\","
    echo "    \"dimensions\": \"${CLOUDINARY_WIDTH}x${CLOUDINARY_HEIGHT}\","
    echo "    \"format\": \"${CLOUDINARY_FORMAT}\","
    echo "    \"size_bytes\": ${CLOUDINARY_SIZE},"
    echo "    \"upload_time_seconds\": ${UPLOAD_TIME},"
    echo "    \"transformation_url\": \"${TRANSFORMATION_URL}\""
    echo "  }"
    echo "}"
} > "$RESULTS_FILE"

echo -e "\n${BLUE}Results saved to: ${RESULTS_FILE}${NC}"

