#!/bin/bash

# ============================================================
# Ragnarok Database Backend - Service Uninstall Script
# ============================================================
# This script removes the systemd service and related configurations
# WITHOUT deleting the application directory or code
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

# Stop the service
stop_service() {
    print_header "Stopping Service"
    
    if systemctl is-active --quiet ragnarok-db-api.service; then
        print_info "Stopping ragnarok-db-api service..."
        sudo systemctl stop ragnarok-db-api.service
        print_success "Service stopped"
    else
        print_info "Service is not running"
    fi
}

# Disable the service
disable_service() {
    print_header "Disabling Service"
    
    if systemctl is-enabled --quiet ragnarok-db-api.service 2>/dev/null; then
        print_info "Disabling ragnarok-db-api service from starting on boot..."
        sudo systemctl disable ragnarok-db-api.service
        print_success "Service disabled"
    else
        print_info "Service is not enabled"
    fi
}

# Remove systemd service file
remove_service_file() {
    print_header "Removing Systemd Service File"
    
    SERVICE_FILE="/etc/systemd/system/ragnarok-db-api.service"
    
    if [ -f "$SERVICE_FILE" ]; then
        print_info "Removing service file: $SERVICE_FILE"
        sudo rm -f "$SERVICE_FILE"
        
        print_info "Reloading systemd daemon..."
        sudo systemctl daemon-reload
        sudo systemctl reset-failed
        
        print_success "Service file removed"
    else
        print_info "Service file not found"
    fi
}

# Remove nginx configuration
remove_nginx_config() {
    print_header "Removing Nginx Configuration (Optional)"
    
    NGINX_CONF="/etc/nginx/sites-available/ragnarok-db-api"
    NGINX_ENABLED="/etc/nginx/sites-enabled/ragnarok-db-api"
    
    if [ ! -f "$NGINX_CONF" ] && [ ! -L "$NGINX_ENABLED" ]; then
        print_info "No nginx configuration found"
        return
    fi
    
    read -p "Do you want to remove nginx configuration? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipping nginx configuration removal"
        return
    fi
    
    if [ -L "$NGINX_ENABLED" ]; then
        print_info "Removing nginx enabled site link..."
        sudo rm -f "$NGINX_ENABLED"
    fi
    
    if [ -f "$NGINX_CONF" ]; then
        print_info "Removing nginx configuration file..."
        sudo rm -f "$NGINX_CONF"
    fi
    
    print_info "Testing nginx configuration..."
    if sudo nginx -t 2>/dev/null; then
        print_info "Reloading nginx..."
        sudo systemctl reload nginx
        print_success "Nginx configuration removed"
    else
        print_warning "Nginx configuration test failed, but files were removed"
    fi
}

# Remove firewall rules
remove_firewall_rules() {
    print_header "Removing Firewall Rules (Optional)"
    
    if ! command -v ufw &> /dev/null; then
        print_info "UFW not installed, skipping"
        return
    fi
    
    if ! sudo ufw status | grep -q "Status: active"; then
        print_info "UFW is not active, skipping"
        return
    fi
    
    read -p "Do you want to remove UFW firewall rules (80/tcp, 443/tcp)? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipping firewall rules removal"
        return
    fi
    
    print_info "Removing firewall rules..."
    sudo ufw delete allow 80/tcp 2>/dev/null || true
    sudo ufw delete allow 443/tcp 2>/dev/null || true
    
    print_success "Firewall rules removed"
    print_info "Note: SSH rule was preserved"
}

# Print final information
print_final_info() {
    print_header "Uninstallation Complete!"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    echo -e "${GREEN}The Ragnarok Database API service has been removed!${NC}\n"
    
    echo -e "${BLUE}What was removed:${NC}"
    echo -e "  ✓ Systemd service (ragnarok-db-api)"
    echo -e "  ✓ Service configuration file"
    echo -e "  ✓ Nginx configuration (if selected)"
    echo -e "  ✓ Firewall rules (if selected)"
    echo -e ""
    
    echo -e "${BLUE}What was preserved:${NC}"
    echo -e "  ✓ Application directory: $SCRIPT_DIR"
    echo -e "  ✓ Python virtual environment (venv/)"
    echo -e "  ✓ All source code and data files"
    echo -e "  ✓ Configuration files"
    echo -e "  ✓ Database files"
    echo -e ""
    
    echo -e "${YELLOW}You can still run the API manually:${NC}"
    echo -e "  cd $SCRIPT_DIR"
    echo -e "  ./start.sh"
    echo -e ""
    
    echo -e "${YELLOW}To completely remove the application:${NC}"
    echo -e "  cd .."
    echo -e "  rm -rf $SCRIPT_DIR"
    echo -e ""
    
    echo -e "${YELLOW}To reinstall the service:${NC}"
    echo -e "  cd $SCRIPT_DIR"
    echo -e "  ./install_debian13.sh"
    echo -e ""
    
    print_success "Uninstallation script completed!"
}

# Main uninstallation flow
main() {
    print_header "Ragnarok Database Backend - Service Uninstaller"
    
    check_root
    
    # Show what will be done
    echo -e "${YELLOW}This script will:${NC}"
    echo "  - Stop the ragnarok-db-api service"
    echo "  - Disable the service from starting on boot"
    echo "  - Remove the systemd service file"
    echo "  - Optionally remove nginx configuration"
    echo "  - Optionally remove firewall rules"
    echo ""
    echo -e "${GREEN}This script will NOT:${NC}"
    echo "  - Delete the application directory"
    echo "  - Remove source code or data files"
    echo "  - Delete the Python virtual environment"
    echo "  - Remove installed system packages"
    echo ""
    
    read -p "Continue with service uninstallation? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Uninstallation cancelled"
        exit 0
    fi
    
    # Run uninstallation steps
    stop_service
    disable_service
    remove_service_file
    remove_nginx_config
    remove_firewall_rules
    
    print_final_info
}

# Run main function
main
