# Ubuntu Deployment Guide

Simple deployment guide for running Manimations API on Ubuntu server using `uv`.

## Prerequisites

- Ubuntu 20.04+ server
- Python 3.11+ 
- Git
- Domain name (optional, for public access)

## Step 1: System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip python3-dev git curl

# Install system dependencies for Manim
sudo apt install -y ffmpeg
sudo apt install -y libcairo2-dev libpango1.0-dev
sudo apt install -y texlive texlive-latex-extra texlive-fonts-extra texlive-latex-recommended texlive-science

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

## Step 2: Clone and Setup Project

```bash
# Clone your repository
git clone https://github.com/your-username/manimations.git
cd manimations

# Install Python dependencies
uv sync

# Setup environment variables
cp .env.example .env
nano .env  # Edit with your API keys
```

## Step 3: Configure Environment Variables

Edit your `.env` file:

```bash
# Required
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Optional (for TTS narration)
OPENAI_API_KEY=your-openai-api-key-here

# Server configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

## Step 4: Test the Application

```bash
# Test run (single worker for testing)
uv run uvicorn app:app --host 0.0.0.0 --port 8000

# Test API (in another terminal)
curl http://localhost:8000/health
```

## Step 5: Production Setup with Systemd

Create a systemd service for automatic startup:

```bash
# Create service file
sudo nano /etc/systemd/system/manimations.service
```

Add this content:

```ini
[Unit]
Description=Manimations API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/manimations
Environment=PATH=/home/ubuntu/.cargo/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/home/ubuntu/.cargo/bin/uv run uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable manimations
sudo systemctl start manimations

# Check status
sudo systemctl status manimations

# View logs
sudo journalctl -u manimations -f
```

## Step 6: Firewall Configuration

```bash
# Allow HTTP traffic
sudo ufw allow 8000
sudo ufw enable
```

## Step 7: Optional - Reverse Proxy with Nginx

If you want to use a domain name and SSL:

```bash
# Install nginx
sudo apt install -y nginx

# Create nginx configuration
sudo nano /etc/nginx/sites-available/manimations
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the configuration:

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/manimations /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Optional: Setup SSL with Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## API Usage

Once deployed, your API will be available at:
- `http://your-server-ip:8000` (direct access)
- `http://your-domain.com` (with nginx)

### Create Animation

```bash
curl -X POST "http://your-server-ip:8000/generate-animation" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain the Pythagorean theorem with a visual proof"}'
```

### Check Status

```bash
curl "http://your-server-ip:8000/animation/{animation_id}/status"
```

### Download Video

```bash
curl "http://your-server-ip:8000/animation/{animation_id}/download" -o animation.mp4
```

## Management Commands

```bash
# View logs
sudo journalctl -u manimations -f

# Restart service
sudo systemctl restart manimations

# Stop service
sudo systemctl stop manimations

# Update application
cd /home/ubuntu/manimations
git pull
uv sync
sudo systemctl restart manimations
```

## Troubleshooting

### Service won't start
```bash
# Check service status
sudo systemctl status manimations

# Check logs
sudo journalctl -u manimations --no-pager

# Check if port is available
sudo netstat -tlnp | grep :8000
```

### Environment issues
```bash
# Test environment loading
uv run python -c "from utils.config import validate_environment; validate_environment()"
```

### Dependencies issues
```bash
# Reinstall dependencies
uv sync --reinstall
```

## Security Notes

- Keep your `.env` file secure and never commit it to git
- Regularly update your system and dependencies
- Consider using a firewall to restrict access
- Use HTTPS in production with SSL certificates
- Monitor your API usage and implement rate limiting if needed

## Performance Tips

- **Multiple workers**: The systemd service uses 4 workers for better performance
- **Worker scaling**: Adjust `--workers` based on CPU cores (typically CPU cores x 2)
- **Memory monitoring**: Each worker uses 200-500MB, monitor total memory usage
- **Disk space**: Monitor disk space (video files can be large)
- **Log rotation**: Set up log rotation for application logs
- **Cleanup**: Consider implementing cleanup for old generated videos
- **Load balancing**: Multiple workers handle concurrent requests automatically