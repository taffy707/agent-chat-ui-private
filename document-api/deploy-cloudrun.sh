#!/bin/bash
# Script to deploy Document API to Google Cloud Run with Authentication

set -e  # Exit on error

echo "🚀 Deploying Document API to Google Cloud Run..."
echo ""

# Configuration
PROJECT_ID="metatask-461115"
REGION="us-central1"
SERVICE_NAME="document-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK first."
    echo "   Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if .env file exists for Supabase credentials
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Make sure to set SUPABASE_URL and SUPABASE_ANON_KEY as environment variables in Cloud Run"
fi

# Load Supabase credentials from .env
if [ -f .env ]; then
    export $(cat .env | grep -E '^SUPABASE_URL=' | xargs)
    export $(cat .env | grep -E '^SUPABASE_ANON_KEY=' | xargs)
fi

# Verify Supabase credentials are set
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "❌ Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set"
    echo "   Either create a .env file or set them as environment variables"
    exit 1
fi

echo "📋 Deployment Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Service Name: $SERVICE_NAME"
echo "   Image: $IMAGE_NAME"
echo "   Supabase URL: $SUPABASE_URL"
echo ""

# Set the project
echo "🔧 Setting Google Cloud project..."
gcloud config set project $PROJECT_ID

# Enable required APIs (if not already enabled)
echo "🔌 Enabling required APIs..."
gcloud services enable \
    containerregistry.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    --quiet

# Build and push the Docker image
echo ""
echo "🏗️  Building Docker image..."
gcloud builds submit --tag $IMAGE_NAME --timeout=15m

# Deploy to Cloud Run
echo ""
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars "GCP_PROJECT_ID=metatask-461115" \
    --set-env-vars "VERTEX_AI_DATA_STORE_ID=metatask_1761751621392" \
    --set-env-vars "VERTEX_AI_LOCATION=global" \
    --set-env-vars "GCS_BUCKET_NAME=metatask-documents-bucket" \
    --set-env-vars "POSTGRES_HOST=34.69.160.99" \
    --set-env-vars "POSTGRES_PORT=5432" \
    --set-env-vars "POSTGRES_USER=tafadzwabwakura" \
    --set-env-vars "POSTGRES_PASSWORD=" \
    --set-env-vars "POSTGRES_DB=vertex_ai_documents" \
    --set-env-vars "SUPABASE_URL=$SUPABASE_URL" \
    --set-env-vars "SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY" \
    --memory 512Mi \
    --timeout 300 \
    --max-instances 10 \
    --port 8080

# Get the service URL
echo ""
echo "🎉 Deployment complete!"
echo ""
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
echo "📍 Service URL: $SERVICE_URL"
echo "📍 API Docs: $SERVICE_URL/docs"
echo "📍 Health Check: $SERVICE_URL/health"
echo ""
echo "✅ To update your frontend .env, set:"
echo "   NEXT_PUBLIC_DOCUMENT_API_URL=$SERVICE_URL"
echo ""

# Test the health endpoint
echo "🏥 Testing health endpoint..."
sleep 5
if curl -s ${SERVICE_URL}/health > /dev/null 2>&1; then
    echo "✅ API is responding!"
    curl -s ${SERVICE_URL}/health | python3 -m json.tool 2>/dev/null || curl -s ${SERVICE_URL}/health
else
    echo "⚠️  API not responding yet. It may still be starting up."
    echo "   Check logs with: gcloud run services logs read $SERVICE_NAME --region $REGION"
fi

echo ""
echo "🔍 To view logs:"
echo "   gcloud run services logs read $SERVICE_NAME --region $REGION --limit 50"
echo ""
echo "🔄 To update the deployment later, just run this script again!"
echo ""
