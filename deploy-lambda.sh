#!/bin/bash

# AWS Lambda Deployment Script for Zpravodaj Converter
# This script creates a deployment package and uploads it to AWS Lambda

set -e

echo "🚀 AWS Lambda Deployment Script"
echo "================================"

# Configuration
LAMBDA_FUNCTION_NAME="zpravodaj-converter"
REGION="eu-central-1"  # Frankfurt
RUNTIME="python3.11"
TIMEOUT=600  # 10 minutes
MEMORY=3008  # 3GB (max for better performance)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Creating deployment package${NC}"

# Create temporary directory
rm -rf lambda-package
mkdir -p lambda-package

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements-lambda.txt -t lambda-package/ --platform manylinux2014_x86_64 --only-binary=:all:

# Copy application code
echo "Copying application code..."
cp lambda_handler.py lambda-package/
cp -r lib lambda-package/

# Create ZIP package
echo "Creating ZIP package..."
cd lambda-package
zip -r ../lambda-deployment.zip . -q
cd ..

echo -e "${GREEN}✓ Deployment package created: lambda-deployment.zip${NC}"
echo "Package size: $(du -h lambda-deployment.zip | cut -f1)"

echo ""
echo -e "${YELLOW}Step 2: Uploading to AWS Lambda${NC}"

# Check if function exists
if aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $LAMBDA_FUNCTION_NAME \
        --zip-file fileb://lambda-deployment.zip \
        --region $REGION

    aws lambda update-function-configuration \
        --function-name $LAMBDA_FUNCTION_NAME \
        --timeout $TIMEOUT \
        --memory-size $MEMORY \
        --region $REGION
else
    echo "Creating new Lambda function..."
    echo ""
    echo -e "${YELLOW}⚠️  You need to create IAM role first!${NC}"
    echo "Run: aws iam create-role --role-name lambda-zpravodaj-role --assume-role-policy-document file://lambda-trust-policy.json"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo -e "${GREEN}✓ Lambda function deployed successfully!${NC}"

echo ""
echo -e "${YELLOW}Step 3: Adding Tesseract Layer${NC}"
echo "You need to add Tesseract Lambda Layer:"
echo "ARN: arn:aws:lambda:eu-central-1:770693421928:layer:Klayers-p311-tesseract:1"
echo ""
echo "Run:"
echo "aws lambda update-function-configuration \\"
echo "  --function-name $LAMBDA_FUNCTION_NAME \\"
echo "  --layers arn:aws:lambda:eu-central-1:770693421928:layer:Klayers-p311-tesseract:1 \\"
echo "  --region $REGION"

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "Test your function:"
echo "aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME --payload file://test-payload.json output.json --region $REGION"
