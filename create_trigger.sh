#!/bin/bash
# Create or update Cloud Build trigger for develop branch

PROJECT_ID="api-ai-blog-writer"
TRIGGER_NAME="deploy-dev-on-develop"

echo "🔧 Checking for existing trigger: $TRIGGER_NAME"

# Check if trigger exists
EXISTING_TRIGGER=$(gcloud builds triggers list \
  --project=$PROJECT_ID \
  --filter="name=$TRIGGER_NAME" \
  --format="value(id)" \
  2>/dev/null)

if [ -n "$EXISTING_TRIGGER" ]; then
  echo "✅ Trigger exists with ID: $EXISTING_TRIGGER"
  echo "   Updating trigger..."
  
  gcloud builds triggers update github \
    --id=$EXISTING_TRIGGER \
    --name=$TRIGGER_NAME \
    --repo-name=api-blogwriting-python-gcr \
    --repo-owner=tindevelopers \
    --branch-pattern="^develop$" \
    --build-config=cloudbuild.yaml \
    --substitutions=_REGION=europe-west9,_ENV=dev,_SERVICE_NAME=blog-writer-api-dev \
    --project=$PROJECT_ID \
    2>&1
  
  echo ""
  echo "✅ Trigger updated successfully"
else
  echo "📝 Creating new trigger..."
  
  gcloud builds triggers create github \
    --name=$TRIGGER_NAME \
    --repo-name=api-blogwriting-python-gcr \
    --repo-owner=tindevelopers \
    --branch-pattern="^develop$" \
    --build-config=cloudbuild.yaml \
    --substitutions=_REGION=europe-west9,_ENV=dev,_SERVICE_NAME=blog-writer-api-dev \
    --project=$PROJECT_ID \
    2>&1
  
  echo ""
  echo "✅ Trigger created successfully"
fi

echo ""
echo "📋 Trigger details:"
gcloud builds triggers describe $TRIGGER_NAME \
  --project=$PROJECT_ID \
  --format="yaml(name,github.push.branch,filename,status,disabled,substitutions)" \
  2>/dev/null || echo "Could not retrieve trigger details"

echo ""
echo "🚀 Trigger is ready. Pushing to develop branch will now trigger automatic deployment."
