#!/bin/bash

# ============================================================
# Ragnarok Database Backend - Installation Script for Debian 13
# ============================================================
# This script automates the installation and setup process
# for the Ragnarok Online Database API on Debian 13
# ============================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

# Check if script is run as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_warning "This script should NOT be run as root"
        print_warning "Please run as a regular user with sudo privileges"
        exit 1
    fi
}

# Check if running on Debian
check_debian() {
    if [ ! -f /etc/debian_version ]; then
        print_error "This script is designed for Debian systems"
        exit 1
    fi
    
    DEBIAN_VERSION=$(cat /etc/debian_version)
    print_info "Detected Debian version: $DEBIAN_VERSION"
}

# Update system packages
update_system() {
    print_header "Updating System Packages"
    sudo apt update
    sudo apt upgrade -y
    print_success "System updated successfully"
}

# Install Python and dependencies
install_python() {
    print_header "Installing Python 3 and Development Tools"
    
    # Install Python 3, pip, venv, and build tools
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        git \
        curl \
        wget
    
    # Check Python version
    PYTHON_VERSION=$(python3 --version)
    print_success "Installed: $PYTHON_VERSION"
}

# Install optional system dependencies
install_optional_deps() {
    print_header "Installing Optional Dependencies"
    
    print_info "Installing nginx (web server/reverse proxy)..."
    sudo apt install -y nginx
    
    print_info "Installing supervisor (process manager)..."
    sudo apt install -y supervisor
    
    print_success "Optional dependencies installed"
}

# Setup application directory
setup_app_directory() {
    print_header "Setting Up Application Directory"
    
    APP_DIR="$HOME/ragnarok-db-backend"
    REPO_URL="https://github.com/xSleepiness/RagnarokDatabase-Backend.git"
    
    if [ -d "$APP_DIR" ]; then
        print_warning "Directory $APP_DIR already exists"
        
        # Check if it's a git repository
        if [ -d "$APP_DIR/.git" ]; then
            print_info "Updating existing repository..."
            cd "$APP_DIR"
            git pull
            print_success "Repository updated"
            return
        else
            read -p "Directory exists but is not a git repo. Remove it? (y/N): " -r
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -rf "$APP_DIR"
                print_info "Removed existing directory"
            else
                print_error "Cannot proceed with existing non-git directory"
                exit 1
            fi
        fi
    fi
    
    print_info "Cloning repository from GitHub..."
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
    print_success "Repository cloned to $APP_DIR"
}

# Create Python virtual environment
create_virtualenv() {
    print_header "Creating Python Virtual Environment"
    
    cd "$HOME/ragnarok-db-backend"
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        return
    fi
    
    print_info "Creating virtual environment..."
    python3 -m venv venv
    
    print_success "Virtual environment created"
}

# Install Python dependencies
install_python_deps() {
    print_header "Installing Python Dependencies"
    
    cd "$HOME/ragnarok-db-backend"
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        return 1
    fi
    
    print_info "Activating virtual environment and installing dependencies..."
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    deactivate
    
    print_success "Python dependencies installed"
}

# Create pre-start script for git pull and dependency updates
create_prestart_script() {
    print_header "Creating Pre-Start Script"
    
    APP_DIR="$HOME/ragnarok-db-backend"
    PRESTART_SCRIPT="$APP_DIR/prestart.sh"
    
    cat > "$PRESTART_SCRIPT" <<'EOF'
#!/bin/bash
# Pre-start script: Update code and dependencies before starting service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[$(date)] Starting pre-start tasks..."

# Git pull to get latest changes
echo "[$(date)] Pulling latest changes from GitHub..."
git pull

# Check if requirements.txt changed
REQUIREMENTS_CHANGED=false
if git diff --name-only HEAD@{1} HEAD | grep -q "requirements.txt"; then
    REQUIREMENTS_CHANGED=true
    echo "[$(date)] requirements.txt changed, will update dependencies"
fi

# Update dependencies if requirements changed
if [ "$REQUIREMENTS_CHANGED" = true ]; then
    echo "[$(date)] Installing updated dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    echo "[$(date)] Dependencies updated"
else
    echo "[$(date)] No dependency updates needed"
fi

echo "[$(date)] Pre-start tasks completed successfully"
EOF
    
    chmod +x "$PRESTART_SCRIPT"
    print_success "Pre-start script created: $PRESTART_SCRIPT"
}

# Create systemd service
create_systemd_service() {
    print_header "Creating Systemd Service"
    
    SERVICE_FILE="/etc/systemd/system/ragnarok-db-api.service"
    APP_DIR="$HOME/ragnarok-db-backend"
    USER=$(whoami)
    
    print_info "Creating service file: $SERVICE_FILE"
    
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Ragnarok Database API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStartPre=$APP_DIR/prestart.sh
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    print_info "Reloading systemd daemon..."
    sudo systemctl daemon-reload
    
    print_success "Systemd service created"
    print_info "Service name: ragnarok-db-api"
}

# Configure nginx (optional)
configure_nginx() {
    print_header "Configuring Nginx (Optional)"
    
    read -p "Do you want to configure nginx as reverse proxy? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipping nginx configuration"
        return
    fi
    
    read -p "Enter your domain name (or press Enter for localhost): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        DOMAIN="localhost"
    fi
    
    NGINX_CONF="/etc/nginx/sites-available/ragnarok-db-api"
    
    sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $HOME/ragnarok-db-backend/data/images;
    }
}
EOF
    
    # Enable site
    sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    sudo nginx -t
    
    # Restart nginx
    sudo systemctl restart nginx
    
    print_success "Nginx configured for domain: $DOMAIN"
}

# Configure firewall
configure_firewall() {
    print_header "Configuring Firewall (Optional)"
    
    read -p "Do you want to configure UFW firewall? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipping firewall configuration"
        return
    fi
    
    print_info "Installing and configuring UFW..."
    sudo apt install -y ufw
    
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    print_warning "Firewall rules configured but NOT enabled"
    print_warning "To enable firewall, run: sudo ufw enable"
}

# Create startup script
create_startup_script() {
    print_header "Creating Startup Scripts"
    
    APP_DIR="$HOME/ragnarok-db-backend"
    
    # Start script
    cat > "$APP_DIR/start.sh" <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
EOF
    
    # Stop script
    cat > "$APP_DIR/stop.sh" <<'EOF'
#!/bin/bash
pkill -f "uvicorn main:app"
EOF
    
    # Restart script
    cat > "$APP_DIR/restart.sh" <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./stop.sh
sleep 2
./start.sh
EOF
    
    chmod +x "$APP_DIR/start.sh" "$APP_DIR/stop.sh" "$APP_DIR/restart.sh"
    
    print_success "Startup scripts created"
}

# Print final instructions
print_final_instructions() {
    print_header "Installation Complete!"
    
    echo -e "${GREEN}The Ragnarok Database API has been installed successfully!${NC}\n"
    
    echo -e "${BLUE}Application Directory:${NC} $HOME/ragnarok-db-backend\n"
    
    echo -e "${BLUE}To start the API manually:${NC}"
    echo -e "  cd ~/ragnarok-db-backend"
    echo -e "  ./start.sh"
    echo -e ""
    
    echo -e "${BLUE}To use systemd service:${NC}"
    echo -e "  sudo systemctl start ragnarok-db-api     # Start service (auto git pull)"
    echo -e "  sudo systemctl stop ragnarok-db-api      # Stop service"
    echo -e "  sudo systemctl restart ragnarok-db-api   # Restart service (auto git pull)"
    echo -e "  sudo systemctl enable ragnarok-db-api    # Enable on boot"
    echo -e "  sudo systemctl status ragnarok-db-api    # Check status"
    echo -e ""
    
    echo -e "${GREEN}Auto-Update Feature:${NC}"
    echo -e "  Every time you start/restart the service, it will:"
    echo -e "  1. Pull latest changes from GitHub"
    echo -e "  2. Update Python dependencies if requirements.txt changed"
    echo -e "  3. Start the application with the latest code"
    echo -e ""
    
    echo -e "${BLUE}Access the API:${NC}"
    echo -e "  API: http://localhost:8000"
    echo -e "  Documentation: http://localhost:8000/docs"
    echo -e "  ReDoc: http://localhost:8000/redoc"
    echo -e ""
    
    echo -e "${BLUE}Logs:${NC}"
    echo -e "  sudo journalctl -u ragnarok-db-api -f   # Follow service logs"
    echo -e ""
    
    echo -e "${YELLOW}Next Steps:${NC}"
    echo -e "  1. Review and edit configuration if needed"
    echo -e "  2. Make sure your data files are in place (data/pre-re/)"
    echo -e "  3. Start the service: sudo systemctl start ragnarok-db-api"
    echo -e "  4. Enable on boot: sudo systemctl enable ragnarok-db-api"
    echo -e ""
    
    print_success "Installation script completed!"
}

# Main installation flow
main() {
    print_header "Ragnarok Database Backend - Debian 13 Installer"
    
    check_root
    check_debian
    
    # Ask for confirmation
    echo -e "${YELLOW}This script will:${NC}"
    echo "  - Update system packages"
    echo "  - Install Python 3 and dependencies"
    echo "  - Install nginx and supervisor"
    echo "  - Clone repository from GitHub"
    echo "  - Create virtual environment"
    echo "  - Install Python packages"
    echo "  - Create systemd service with auto-update"
    echo "  - Configure startup scripts"
    echo ""
    read -p "Continue with installation? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled"
        exit 0
    fi
    
    # Run installation steps
    update_system
    install_python
    install_optional_deps
    setup_app_directory
    create_virtualenv
    install_python_deps
    create_prestart_script
    create_systemd_service
    create_startup_script
    configure_nginx
    configure_firewall
    
    print_final_instructions
}

# Run main function
main
