#!/bin/bash

# FSN Appium Farm - VPS Deployment Script

set -e

echo "🚀 FSN Appium Farm VPS Deployment"
echo "=================================="

# Configuration
PROJECT_NAME="fsn-appium-farm"
DEPLOY_DIR="/opt/${PROJECT_NAME}"
SERVICE_USER="fsn"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root for security reasons"
    exit 1
fi

# Check if .env.production exists
if [[ ! -f ".env.production" ]]; then
    print_error ".env.production file not found!"
    print_warning "Please copy env.production.template to .env.production and configure it"
    exit 1
fi

print_status "Starting deployment process..."

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
print_status "Installing system dependencies..."
sudo apt install -y \
    docker.io \
    docker-compose \
    nginx \
    certbot \
    python3-certbot-nginx \
    htop \
    curl \
    git

# Start and enable Docker
print_status "Setting up Docker..."
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Create deployment directory
print_status "Creating deployment directory..."
sudo mkdir -p $DEPLOY_DIR
sudo chown $USER:$USER $DEPLOY_DIR

# Copy application files
print_status "Copying application files..."
rsync -av --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' . $DEPLOY_DIR/

# Copy production environment
cp .env.production $DEPLOY_DIR/.env

# Build and start services
print_status "Building and starting services..."
cd $DEPLOY_DIR
docker-compose -f deployment/docker-compose.yml up --build -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 30

# Test API health
print_status "Testing API health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "✅ API is healthy!"
else
    print_error "❌ API health check failed"
    docker-compose -f deployment/docker-compose.yml logs api
    exit 1
fi

# Setup nginx (basic config)
print_status "Setting up Nginx reverse proxy..."
sudo tee /etc/nginx/sites-available/$PROJECT_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;  # Update this with your domain

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

print_status "🎉 Deployment completed successfully!"
print_status "Next steps:"
echo "1. Update the nginx config with your actual domain name"
echo "2. Run: sudo certbot --nginx -d your-domain.com"
echo "3. Configure your DNS to point to this VPS"
echo "4. Test the API at: http://your-domain.com/health"

print_warning "Remember to:"
echo "- Change default passwords in .env.production"
echo "- Set up proper SSL certificates"
echo "- Configure firewall rules"
echo "- Set up monitoring and backups"
