# ScheduleHub — VPS Deployment Guide

Deploy Django on your VPS with Gunicorn, Nginx, and SSL in ~20 minutes.

**Target:** `schedulehub.johneytech.com.ng`

---

## Prerequisites on VPS

- Ubuntu 20.04+ 
- Python 3.9+
- Nginx installed
- Git configured with GitHub SSH

---

## PART 1: Setup GitHub SSH (First time only)

```bash
ls ~/.ssh
cat ~/.ssh/id_ed25519.pub
```

Copy output → GitHub → Settings → SSH and GPG Keys → Add.

Test:

```bash
ssh -T git@github.com
```

---

## PART 2: Create app directory & clone

```bash
sudo mkdir -p /var/www/schedulehub
sudo chown -R $USER:$USER /var/www/schedulehub
cd /var/www/schedulehub

git clone git@github.com:Kingjohneycodey/schedulehub.git .
```

---

## PART 3: Setup Python environment

```bash
sudo apt install -y python3-venv python3-pip

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install gunicorn
```

---

## PART 4: Environment variables

```bash
nano .env
```

Paste:

```
DJANGO_SECRET_KEY=replace-with-a-long-random-string
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=schedulehub.johneytech.com.ng
```

---

## PART 5: Django setup

```bash
source venv/bin/activate

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_demo
```

Quick test:

```bash
gunicorn schedulehub.wsgi:application --bind 0.0.0.0:8100
```

Then `curl http://localhost:8100` — you should get HTML. Press Ctrl+C to stop.

---

## PART 6: Systemd service (keeps it running)

```bash
sudo nano /etc/systemd/system/schedulehub.service
```

Paste:

```ini
[Unit]
Description=ScheduleHub Django App
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/schedulehub
EnvironmentFile=/var/www/schedulehub/.env
ExecStart=/var/www/schedulehub/venv/bin/gunicorn schedulehub.wsgi:application --bind 127.0.0.1:8100 --workers 3
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable schedulehub
sudo systemctl start schedulehub
sudo systemctl status schedulehub
```

Check it's running:

```bash
curl http://localhost:8100
```

---

## PART 7: Configure DNS

Go to your domain provider. Create an **A Record**:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | schedulehub | YOUR_VPS_IP | Auto |

Wait 1–5 minutes. Test:

```bash
ping schedulehub.johneytech.com.ng
```

---

## PART 8: Nginx reverse proxy

```bash
sudo nano /etc/nginx/sites-available/schedulehub
```

Paste:

```nginx
server {
    listen 80;
    server_name schedulehub.johneytech.com.ng;

    client_max_body_size 20M;

    location /static/ {
        alias /var/www/schedulehub/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/schedulehub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Test:

```bash
curl http://schedulehub.johneytech.com.ng
```

---

## PART 9: Enable SSL (HTTPS)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d schedulehub.johneytech.com.ng
```

Test: visit `https://schedulehub.johneytech.com.ng`

---

## PART 10: GitHub Actions auto-deploy (optional)

Create deploy key:

```bash
cat ~/.ssh/github_actions
```

Add private key as `DEPLOY_KEY` in GitHub repo → Settings → Secrets.

Create `.github/workflows/deploy.yml` in your repo:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1
        with:
          host: YOUR_VPS_IP
          username: root
          key: ${{ secrets.DEPLOY_KEY }}
          script: |
            cd /var/www/schedulehub
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            python manage.py migrate
            python manage.py collectstatic --noinput
            sudo systemctl restart schedulehub
```

Push to main → check GitHub Actions for status.

---

## Useful commands

```bash
# View logs
sudo journalctl -u schedulehub -f

# Restart after code changes
sudo systemctl restart schedulehub

# Pull latest code manually
cd /var/www/schedulehub && git pull origin main

# Check status
sudo systemctl status schedulehub
```
