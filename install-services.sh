#!/bin/bash

# Installation and Setup Script for IICC Attendance System

echo "Setting up IICC Attendance System..."

# Set installation directory
INSTALL_DIR="/home/frappe/bt_attendance"
SERVICE_DIR="/etc/systemd/system"

# Install systemd services
echo "Installing systemd services..."
sudo cp "$INSTALL_DIR/iicc-portal.service" "$SERVICE_DIR/"
sudo cp "$INSTALL_DIR/iicc-admin-portal.service" "$SERVICE_DIR/"
sudo cp "$INSTALL_DIR/iicc-admin-dashboard.service" "$SERVICE_DIR/"

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable iicc-portal
sudo systemctl enable iicc-admin-portal
sudo systemctl enable iicc-admin-dashboard

# Start the services
sudo systemctl start iicc-portal
sudo systemctl start iicc-admin-portal
sudo systemctl start iicc-admin-dashboard

echo "Setup complete!"
echo ""
echo "Services installed:"
echo "  - Remote Check-in Portal: http://localhost:5001"
echo "  - Admin Portal: http://localhost:5002"
echo "  - Employee Location Dashboard: http://localhost:5002/admin"
echo ""
echo "Manage services with:"
echo "  sudo systemctl start|stop|restart|status iicc-portal"
echo "  sudo systemctl start|stop|restart|status iicc-admin-portal"
echo "  sudo systemctl start|stop|restart|status iicc-admin-dashboard"
echo ""
echo "View logs:"
echo "  tail -f logs/portal.log"
echo "  tail -f logs/admin_portal.log"
echo "  tail -f logs/admin_dashboard.log"
echo ""
echo "🎯 Access Admin Dashboard: http://localhost:5002/admin"
echo "📍 For CF Tunnel access: https://your-tunnel-name.trycloudflare.com/admin"
