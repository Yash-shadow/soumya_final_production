#!/bin/bash
# TGNPDCL Monolithic App - Quick Setup Script

set -e

echo "🚀 TGNPDCL Monolithic Application Setup"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run this script from the tgnpdcl-monolith directory."
    exit 1
fi

# Step 1: Check Python
echo "📋 Step 1: Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install it first."
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Step 2: Install pip if needed
echo "📋 Step 2: Checking pip installation..."
if ! python3 -m pip --version &> /dev/null; then
    echo "⚠️  pip not found. Installing..."
    sudo apt update
    sudo apt install python3-pip python3-venv -y
fi
echo "✅ pip found: $(python3 -m pip --version)"
echo ""

# Step 3: Create virtual environment
echo "📋 Step 3: Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Step 4: Activate and install dependencies
echo "📋 Step 4: Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Step 5: Run migrations
echo "📋 Step 5: Running database migrations..."
python manage.py makemigrations
python manage.py migrate
echo "✅ Database migrations complete"
echo ""

# Step 6: Collect static files
echo "📋 Step 6: Collecting static files..."
python manage.py collectstatic --noinput
echo "✅ Static files collected"
echo ""

# Step 7: Create superuser prompt
echo "📋 Step 7: Create superuser (admin account)"
echo "You'll be prompted to create an admin account..."
python manage.py createsuperuser

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run server: python manage.py runserver"
echo "3. Visit: http://localhost:8000"
echo ""
echo "📚 To create test users for all 7 roles, run:"
echo "   python manage.py shell < create_test_users.py"
echo ""
