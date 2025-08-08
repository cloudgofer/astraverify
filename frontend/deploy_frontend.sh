#!/bin/bash

# Exit on error
set -e

echo "🛠️ Building React app..."
npm install
npm run build

echo "🚀 Deploying to Firebase Hosting..."
firebase deploy

echo "✅ Frontend deployed successfully!"
