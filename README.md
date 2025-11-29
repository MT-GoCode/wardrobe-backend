# WardrobeForge Backend

---

## Production Deployment (Complete Guide)

This guide sets up your Flask app to run **24/7 with HTTPS**, even after you close your terminal or reboot the server.

### Architecture Overview

```
Internet → Cloudflare (proxy/SSL) → Nginx (reverse proxy) → Gunicorn (WSGI) → Flask app
```

- **Gunicorn**: Production WSGI server that runs your Flask app (replaces `python app.py`)
- **Nginx**: Reverse proxy that handles SSL termination and forwards requests to Gunicorn
- **systemd**: Keeps Gunicorn running forever, auto-restarts on crash, starts on boot
- **Certbot**: Manages Let's Encrypt SSL certificates with auto-renewal

---

## Step 1: Install Dependencies

```bash
# Update system and install nginx + certbot
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# Install gunicorn (Python WSGI server)
pip install gunicorn
```

---

## Step 2: Create the systemd Service

This is what makes your app run **forever in the background**, even after closing your terminal.

Create the service file:

```bash
sudo nano /etc/systemd/system/wardrobe.service
```

Paste this content (adjust paths if your setup differs):

```ini
[Unit]
Description=Wardrobe Flask Application
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/wardrobe-backend/backend
Environment="PATH=/home/ubuntu/.local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/.local/bin/gunicorn --workers 4 --threads 2 --bind 127.0.0.1:8000 --timeout 300 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Understanding the service file:

| Line | What it does |
|------|--------------|
| `User=ubuntu` | Runs as the ubuntu user (not root) |
| `WorkingDirectory=...` | Sets the working directory to your backend folder |
| `Environment="PATH=..."` | Ensures gunicorn and python are found |
| `ExecStart=...` | The command to run your app |
| `app:app` | Means "import `app` from `app.py`, use the Flask instance named `app`" |
| `--bind 127.0.0.1:8000` | Listen on localhost port 8000 (nginx will proxy to this) |
| `--workers 4` | Run 4 worker processes for concurrent requests |
| `--timeout 300` | Allow requests up to 5 minutes (for long inference) |
| `Restart=always` | Auto-restart if it crashes |
| `WantedBy=multi-user.target` | Start automatically on boot |

### Enable and start the service:

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable wardrobe.service

# Start the service now
sudo systemctl start wardrobe.service

# Check status
sudo systemctl status wardrobe.service
```

### Common service commands:

```bash
# Stop the app
sudo systemctl stop wardrobe.service

# Restart (after code changes)
sudo systemctl restart wardrobe.service

# View live logs
sudo journalctl -u wardrobe.service -f

# View last 100 log lines
sudo journalctl -u wardrobe.service -n 100 --no-pager
```

---

## Step 3: Configure Nginx

Create the nginx config:

```bash
sudo nano /etc/nginx/sites-available/wardrobe
```

Paste this content:

```nginx
upstream wardrobe_app {
    server 127.0.0.1:8000;
}

server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name wardrobeforge.com api.wardrobeforge.com YOUR_SERVER_IP;

    client_max_body_size 64m;

    location /.well-known/acme-challenge/ {
        root /var/www/wardrobe;
    }

    location / {
        proxy_pass http://wardrobe_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

Enable the site and test:

```bash
# Create directory for SSL challenges
sudo mkdir -p /var/www/wardrobe

# Enable the site (create symlink)
sudo ln -sf /etc/nginx/sites-available/wardrobe /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test config syntax
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

---

## Step 4: Oracle Cloud Firewall

In Oracle Cloud Console:

1. Go to **Compute** → **Instances** → Click your instance
2. Under **Primary VNIC**, click the **Subnet** link
3. Click the **Security List** (e.g., "Default Security List for vcn-...")
4. Click **Add Ingress Rules**
5. Add these rules:

| Stateless | Source CIDR | Protocol | Dest Port |
|-----------|-------------|----------|-----------|
| No | `0.0.0.0/0` | TCP | `80` |
| No | `0.0.0.0/0` | TCP | `443` |

Also run on the server (one-time):

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

---

## Step 5: Cloudflare DNS

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select `wardrobeforge.com` → **DNS** → **Records**
3. Add A records:

| Type | Name | Content | Proxy status |
|------|------|---------|--------------|
| A | `@` | `146.235.196.147` | **DNS only** (gray cloud) |
| A | `api` | `146.235.196.147` | **DNS only** (gray cloud) |

⚠️ **Important:** Start with "DNS only" (gray cloud) for SSL certificate setup.

---

## Step 6: Get SSL Certificate

Once DNS is pointing to your server:

```bash
sudo certbot --nginx -d wardrobeforge.com -d api.wardrobeforge.com --redirect
```

This will:
- Obtain a free Let's Encrypt certificate
- Auto-configure nginx for HTTPS
- Set up automatic renewal (runs via systemd timer)

Test renewal:

```bash
sudo certbot renew --dry-run
```

---

## Step 7: Enable Cloudflare Proxy (Optional)

After certbot succeeds, you can enable Cloudflare's proxy for DDoS protection:

1. In Cloudflare DNS, change both A records to **Proxied** (orange cloud)
2. Go to **SSL/TLS** → **Overview** → Set mode to **Full (strict)**

---

## Endpoints

| Endpoint | URL |
|----------|-----|
| Health check | `https://wardrobeforge.com/health` |
| Health check (api) | `https://api.wardrobeforge.com/health` |
| Settings | `https://wardrobeforge.com/settings` |
| Generate | `POST https://wardrobeforge.com/generate_request` |

---

## Quick Reference

### After code changes:

```bash
sudo systemctl restart wardrobe.service
```

### Check if app is running:

```bash
curl http://127.0.0.1:8000/health
```

### View logs:

```bash
sudo journalctl -u wardrobe.service -f
```

### Nginx commands:

```bash
sudo nginx -t                    # Test config
sudo systemctl reload nginx      # Reload config
sudo tail -f /var/log/nginx/error.log  # View errors
```

---

## File Locations

| Component | Location |
|-----------|----------|
| Flask app | `/home/ubuntu/wardrobe-backend/backend/app.py` |
| Systemd service | `/etc/systemd/system/wardrobe.service` |
| Nginx config | `/etc/nginx/sites-available/wardrobe` |
| SSL certificates | `/etc/letsencrypt/live/wardrobeforge.com/` |
| Nginx logs | `/var/log/nginx/` |
| App logs | `journalctl -u wardrobe.service` |

---

## FAQ

### Q: Will my app keep running after I close the terminal?
**Yes!** The systemd service runs independently of your terminal session. It will run forever until you stop it, and auto-starts on server reboot.

### Q: How do I update my code?
```bash
cd /home/ubuntu/wardrobe-backend
git pull  # or however you update
sudo systemctl restart wardrobe.service
```

### Q: Why gunicorn instead of `python app.py`?
Flask's built-in server is for development only. Gunicorn is a production WSGI server that:
- Handles multiple concurrent requests
- Is more stable and performant
- Can spawn multiple worker processes

### Q: What's the `app:app` in the ExecStart?
It means: "from `app.py`, use the Flask instance named `app`". If your Flask app was in `main.py` with `application = Flask(__name__)`, you'd use `main:application`.

# Personal Setup

## Local Development Setup

### 1. Install Miniconda and UV

```bash
# Install miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
bash /tmp/miniconda.sh -b -p $HOME/miniconda3
rm /tmp/miniconda.sh

# Add to PATH and initialize
export PATH="$HOME/miniconda3/bin:$PATH"
conda init bash
source ~/.bashrc

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### 2. Create Conda Environment

```bash
# Create environment with Python 3.10
conda create -n wardrobe python=3.10 -y
conda activate wardrobe

# Install dependencies
cd backend
uv pip install -r requirements.txt
```

### 3. Run Development Server

```bash
python app.py  # runs on http://localhost:4000
```

Oracle VM RAM is quite small. You can add swap space:

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```