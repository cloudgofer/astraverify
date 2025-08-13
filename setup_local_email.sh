#!/bin/bash

echo "=========================================="
echo "  Setup Email Password for Local Development"
echo "=========================================="
echo ""

echo "🔍 Current EMAIL_PASSWORD status:"
if [ -n "$EMAIL_PASSWORD" ]; then
    echo "✅ EMAIL_PASSWORD is set"
else
    echo "❌ EMAIL_PASSWORD is not set"
fi

echo ""
echo "📝 Setting EMAIL_PASSWORD for local development..."
echo "Enter the password for hi@astraverify.com:"
read -s EMAIL_PASSWORD

if [ -z "$EMAIL_PASSWORD" ]; then
    echo "❌ Password cannot be empty"
    exit 1
fi

echo ""
echo "🔧 Setting environment variable..."

# Export the password for current session
export EMAIL_PASSWORD="$EMAIL_PASSWORD"

# Add to shell profile for persistence
SHELL_PROFILE=""
if [ -f "$HOME/.bashrc" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_PROFILE="$HOME/.bash_profile"
fi

if [ -n "$SHELL_PROFILE" ]; then
    # Remove any existing EMAIL_PASSWORD line
    sed -i.bak '/^export EMAIL_PASSWORD=/d' "$SHELL_PROFILE"
    
    # Add the new EMAIL_PASSWORD line
    echo "export EMAIL_PASSWORD=\"$EMAIL_PASSWORD\"" >> "$SHELL_PROFILE"
    
    echo "✅ EMAIL_PASSWORD added to $SHELL_PROFILE"
    echo "   (You may need to restart your terminal or run 'source $SHELL_PROFILE')"
else
    echo "⚠️  Could not find shell profile file. Please manually add:"
    echo "   export EMAIL_PASSWORD=\"$EMAIL_PASSWORD\""
    echo "   to your shell profile file (.bashrc, .zshrc, or .bash_profile)"
fi

echo ""
echo "🔍 Verifying configuration..."
cd backend
python3 -c "from app import EMAIL_PASSWORD; print('EMAIL_PASSWORD configured:', bool(EMAIL_PASSWORD))"

echo ""
echo "🚀 Testing email configuration..."
echo "Starting backend server for testing..."
echo "Press Ctrl+C to stop after testing"

# Start the backend server
python3 app.py
