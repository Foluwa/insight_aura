#!/bin/bash
# VPS Setup Script for Insight Aura

set -e

echo "🚀 Setting up VPS for Insight Aura System..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    htop \
    nginx \
    certbot \
    python3-certbot-nginx

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose (standalone)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create project directory
sudo mkdir -p /opt/sentiment
sudo chown $USER:$USER /opt/sentiment
cd /opt/sentiment

# Clone repository (replace with your repo)
git clone https://github.com/yourusername/your-repo.git .

# Create .env file from template
cat > .env << 'EOF'
# Production Environment Configuration
DATABASE_URL=postgresql://airflow:airflow@postgres:5432/airflow
SENTRY_DSN=your_sentry_dsn_here
ENVIRONMENT=production

# Airflow Admin User Configuration
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=secure_production_password_here
AIRFLOW_ADMIN_FIRSTNAME=Admin
AIRFLOW_ADMIN_LASTNAME=User
AIRFLOW_ADMIN_EMAIL=admin@yourcompany.com
AIRFLOW_ADMIN_ROLE=Admin

# Airflow Configuration
AIRFLOW_FERNET_KEY=your_fernet_key_here
AIRFLOW_WEBSERVER_SECRET_KEY=your_secret_key_here

# Notification Configuration (optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
SLACK_WEBHOOK_URL=
TELEGRAM_ALERTS_ENABLED=false
SLACK_ALERTS_ENABLED=false

# Proxy Configuration (if needed)
PROXY_ENABLED=false
HTTP_PROXY=
HTTPS_PROXY=

# Grafana Configuration
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin_password_here
EOF

echo "📝 Please edit /opt/sentiment/.env with your actual configuration"

# Set up nginx reverse proxy
sudo tee /etc/nginx/sites-available/sentiment << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    # Airflow UI
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Grafana (optional)
    location /grafana/ {
        proxy_pass http://localhost:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/sentiment /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

# Set up firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Create systemd service for auto-start
sudo tee /etc/systemd/system/sentiment.service << EOF
[Unit]
Description=Insight Aura System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/sentiment
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=root

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable sentiment.service

# Set up log rotation
sudo tee /etc/logrotate.d/sentiment << 'EOF'
/opt/sentiment/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        docker-compose -f /opt/sentiment/docker-compose.yml restart > /dev/null 2>&1 || true
    endscript
}
EOF

echo ""
echo "✅ VPS setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit /opt/sentiment/.env with your configuration"
echo "2. Replace 'your-domain.com' in /etc/nginx/sites-available/sentiment"
echo "3. Set up SSL: sudo certbot --nginx -d your-domain.com"
echo "4. Start services: cd /opt/sentiment && docker-compose up -d"
echo "5. Configure GitHub secrets for CI/CD"
echo ""
echo "🔐 GitHub Secrets needed:"
echo "  - VPS_HOST: your VPS IP address"
echo "  - VPS_USERNAME: your VPS username"
echo "  - VPS_SSH_KEY: your private SSH key"
echo "  - VPS_PROJECT_PATH: /opt/sentiment"
echo ""
echo "🌐 Access your services:"
echo "  - Airflow: http://your-domain.com"
echo "  - Backend API: http://your-domain.com/api"
echo "  - Grafana: http://your-domain.com/grafana"