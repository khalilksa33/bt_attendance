# 🎯 IICC Attendance System - Enhanced Admin Dashboard

## Overview

The **IICC Attendance Admin Dashboard** is a stunning, modern web application for managing employee locations and tracking field staff. It provides real-time monitoring of remote field employees with an intuitive interface.

## Features

### 🎨 Modern User Interface
- **Gradient Design**: Beautiful purple gradient theme
- **Responsive Layout**: Works seamlessly on desktop and mobile
- **Real-time Updates**: Dashboard refreshes every 30 seconds
- **Dark Mode Friendly**: Professional color scheme

### 📍 Location Management
- **Employee Location Assignment**: Assign employees to specific work locations
- **Multiple Location Support**: Manage Office, Field Sites, Remote workers, On Leave status
- **Real-time Tracking**: See where employees checked in and when
- **Location History**: Track check-in timestamps for each employee

### 📊 Dashboard Statistics
- **Total Employees**: Count of all employees in the system
- **Checked In Today**: Real-time count of employees who checked in
- **Field Locations**: Number of available work locations
- **Last Update**: Timestamp of the latest employee activity

### 👥 Employee Management
- **Quick Assignment**: Add employees to locations with single form
- **Bulk Operations**: Manage multiple employee locations
- **Remove Employees**: Easy removal from assignments
- **Employee List**: View all assigned employees with their locations

### ⚙️ Admin Settings
- **Location Configuration**: Add/edit/remove work locations
- **Location Tracking**: Enable/disable real-time location tracking
- **Session Management**: Secure admin sessions with token authentication
- **Settings Persistence**: All settings saved to JSON database

## Ports & Access

| Service | Port | URL |
|---------|------|-----|
| Remote Check-in Portal | 5001 | `http://localhost:5001` |
| Admin Dashboard | 5002 | `http://localhost:5002/admin` |
| Daily Report | 10:00 AM | Scheduled cron job |

## Cloudflare Tunnel Integration

For external access via Cloudflare Tunnel:

```bash
# CF Tunnel configuration example
cloudflared tunnel create attendance-system
cloudflared tunnel route dns attendance-system your-domain.com
cloudflared tunnel config
```

Then access the dashboard at:
```
https://your-domain.com/admin
```

## Admin Dashboard Login

**Default Credentials:**
- Username: `admin`
- Password: Set via environment variable `ADMIN_PORTAL_PASSWORD`

⚠️ **Change the default password immediately!**

## Using the Dashboard

### 1. Login
```
1. Navigate to http://localhost:5002/admin
2. Enter admin credentials
3. Click "Login to Dashboard"
```

### 2. Configure Locations
```
1. Go to "Location Settings" section
2. Add locations (one per line):
   - Office
   - Field Site A
   - Field Site B
   - Remote
   - On Leave
3. Enable "Real-time Location Tracking" if desired
4. Click "Save Settings"
```

### 3. Assign Employees
```
1. Enter Employee Name (e.g., "Ahmed Hassan")
2. Enter Employee ID (e.g., "5")
3. Select Primary Location from dropdown
4. Click "Assign Location"
5. Employee appears in "Assigned Employees" list
```

### 4. Monitor Check-ins
- Real-time display of all employee check-ins
- Timestamp of last check-in
- Employee location status
- Dashboard stats update every 30 seconds

## API Endpoints

### Authentication
```bash
POST /admin/login
Content-Type: application/json
{
  "username": "admin",
  "password": "password"
}
```

### Get Settings
```bash
GET /admin/api/settings
Headers:
  X-Admin-Token: [token]
```

### Save Settings
```bash
PUT /admin/api/settings
Headers:
  X-Admin-Token: [token]
Content-Type: application/json
{
  "locations": ["Office", "Field Site A"],
  "enable_location_tracking": true
}
```

### Assign Employee
```bash
POST /admin/api/assign-employee
Headers:
  X-Admin-Token: [token]
Content-Type: application/json
{
  "name": "Ahmed Hassan",
  "employee_id": "5",
  "location": "Field Site A"
}
```

### Get Locations
```bash
GET /admin/api/locations
Headers:
  X-Admin-Token: [token]
```

### Record Check-in
```bash
POST /admin/api/check-in
Headers:
  X-Admin-Token: [token]
Content-Type: application/json
{
  "employee_id": "5",
  "name": "Ahmed Hassan",
  "location": "Field Site A",
  "latitude": 24.7136,  // optional
  "longitude": 46.6753  // optional
}
```

## File Structure

```
/home/frappe/bt_attendance/
├── admin_dashboard.py          # Enhanced admin dashboard (main server)
├── portal.py                   # Remote employee check-in portal
├── attendance_bot.py           # Daily report generator
├── iicc-admin-dashboard.service # Systemd service file
├── iicc-portal.service         # Remote portal service
├── install-services.sh         # Service installation script
├── admin_settings.json         # Location settings database
├── employee_locations.json     # Real-time location database
└── logs/
    ├── admin_dashboard.log
    ├── portal.log
    └── attendance_ids.log
```

## Service Management

### View All Services
```bash
systemctl status iicc-portal.service
systemctl status iicc-admin-dashboard.service
```

### View Logs
```bash
# Admin Dashboard logs
tail -f /home/frappe/bt_attendance/logs/admin_dashboard.log

# Remote Portal logs
tail -f /home/frappe/bt_attendance/logs/portal.log

# System logs
sudo journalctl -u iicc-admin-dashboard.service -f
```

### Control Services
```bash
# Start
sudo systemctl start iicc-admin-dashboard.service

# Stop
sudo systemctl stop iicc-admin-dashboard.service

# Restart
sudo systemctl restart iicc-admin-dashboard.service

# Enable auto-start on boot
sudo systemctl enable iicc-admin-dashboard.service
```

## Environment Variables

Add these to your `.env` file:

```bash
# Admin Dashboard
ADMIN_PORTAL_PORT=5002
ADMIN_PORTAL_USERNAME=admin
ADMIN_PORTAL_PASSWORD=YourSecurePassword123!

# Remote Portal
PORT=5001
PORTAL_ACCESS_CODE=optional-code

# Daily Report
ERP_URL=https://your-erp.com
ERP_API_KEY=your-api-key
ERP_API_SECRET=your-api-secret
EMAIL_USER=your-email@company.com
EMAIL_PASS=your-email-password
RECIPIENT_EMAIL=manager@company.com
```

## Data Storage

### admin_settings.json
```json
{
  "employees": [
    {
      "name": "Ahmed Hassan",
      "employee_id": "5",
      "location": "Field Site A",
      "assigned_at": "2026-04-30T10:00:00"
    }
  ],
  "locations": ["Office", "Field Site A", "Field Site B"],
  "enable_location_tracking": true,
  "last_updated": "2026-04-30T10:30:00"
}
```

### employee_locations.json
```json
{
  "employees": {
    "5": {
      "name": "Ahmed Hassan",
      "location": "Field Site A",
      "checked_in_at": "2026-04-30T09:15:00",
      "latitude": 24.7136,
      "longitude": 46.6753
    }
  },
  "check_ins": [
    {
      "employee_id": "5",
      "name": "Ahmed Hassan",
      "location": "Field Site A",
      "timestamp": "2026-04-30T09:15:00",
      "latitude": 24.7136,
      "longitude": 46.6753
    }
  ],
  "last_updated": "2026-04-30T10:30:00"
}
```

## Troubleshooting

### Dashboard Won't Load
```bash
# Check if service is running
systemctl status iicc-admin-dashboard.service

# Check port availability
sudo lsof -i :5002

# View recent logs
sudo journalctl -u iicc-admin-dashboard.service -n 50
```

### Port Already in Use
```bash
# Find and kill process using port
sudo lsof -ti:5002 | xargs kill -9

# Restart service
sudo systemctl restart iicc-admin-dashboard.service
```

### JSON Database Errors
```bash
# Verify file permissions
ls -la /home/frappe/bt_attendance/*.json

# Reset to defaults if corrupted
rm /home/frappe/bt_attendance/admin_settings.json
rm /home/frappe/bt_attendance/employee_locations.json
sudo systemctl restart iicc-admin-dashboard.service
```

## Security Notes

1. **Change Default Password**: Update `ADMIN_PORTAL_PASSWORD` in `.env` immediately
2. **HTTPS with CF Tunnel**: Always use HTTPS for external access
3. **Firewall Rules**: Restrict port 5002 to internal network if not using CF Tunnel
4. **Session Timeout**: Sessions expire after 1 hour of inactivity
5. **Token Security**: Tokens are stored server-side and validated on each request

## Performance Tips

1. **Database Optimization**: Periodically backup and archive old check-ins
2. **Refresh Rate**: Adjust 30-second refresh in dashboard.js if needed
3. **Concurrent Users**: Service handles multiple simultaneous connections
4. **Logs Rotation**: Use logrotate to manage log file sizes

## Future Enhancements

- 📱 Mobile app integration
- 🗺️ Real-time map view with GPS
- 📈 Advanced analytics and reporting
- 🔔 Push notifications for admins
- 👤 Role-based access control
- 📸 Employee photo verification

## Support & Documentation

For issues or questions:
1. Check service logs: `journalctl -u iicc-admin-dashboard.service -f`
2. Review admin_settings.json for configuration
3. Verify network connectivity and ports
4. Check .env file for correct credentials

---

**Version**: 1.0  
**Last Updated**: 2026-04-30  
**License**: IICC Internal Use
