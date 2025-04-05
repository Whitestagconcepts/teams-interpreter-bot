# Deploying Teams Interpreter Bot on Hostinger WordPress Hosting

This guide walks through the steps to deploy the Teams Interpreter Bot on Hostinger WordPress hosting using Python and a reverse proxy configuration.

## Prerequisites

- Hostinger WordPress hosting account
- SSH access to your hosting account
- Domain or subdomain for the bot (e.g., bot.yourdomain.com)
- Microsoft Teams Bot registered in Azure

## 1. Set Up Python Environment

Hostinger WordPress hosting does support Python through SSH access. Here's how to set up the environment:

```bash
# Connect via SSH
ssh u123456789@yourdomain.com

# Navigate to the home directory
cd ~

# Create a directory for the bot (outside of public_html)
mkdir -p teams_bot
cd teams_bot

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Clone your bot repository or upload files
git clone https://github.com/yourusername/teams-interpreter-bot.git
# Or upload files via SFTP

cd teams-interpreter-bot

# Install dependencies
pip install -r requirements.txt
```

## 2. Configure the Bot

Create and configure the `.env` file:

```bash
cp config/.env.example .env
nano .env
```

Update with your bot credentials:

```
BOT_ID=your-bot-id
BOT_PASSWORD=your-bot-password
APP_ID=your-app-id
APP_PASSWORD=your-app-password
TENANT_ID=your-tenant-id

# Server Configuration
HOST=127.0.0.1  # Use localhost for the app itself
PORT=8080       # Use a port not conflicting with others

DOMAIN_NAME=bot.yourdomain.com
```

## 3. Download Models

Run the model download script (this might take some time):

```bash
python src/download_models.py
```

## 4. Set Up Supervisor

Supervisor will keep your bot running. Create a configuration file:

```bash
mkdir -p ~/supervisor/conf.d
touch ~/supervisor/conf.d/teams_bot.conf
nano ~/supervisor/conf.d/teams_bot.conf
```

Add the following configuration:

```ini
[program:teams_bot]
command=/home/u123456789/teams_bot/venv/bin/gunicorn --bind 127.0.0.1:8080 --workers 2 --threads 2 src.server.app:app
directory=/home/u123456789/teams_bot/teams-interpreter-bot
autostart=true
autorestart=true
stderr_logfile=/home/u123456789/teams_bot/logs/teams_bot.err.log
stdout_logfile=/home/u123456789/teams_bot/logs/teams_bot.out.log
environment=PYTHONPATH="/home/u123456789/teams_bot/teams-interpreter-bot"
```

Create the logs directory:

```bash
mkdir -p ~/teams_bot/logs
```

Start Supervisor:

```bash
supervisord -c ~/supervisor/supervisord.conf
```

## 5. Configure Nginx Reverse Proxy

Create an Nginx configuration file:

```bash
mkdir -p ~/nginx/conf.d
touch ~/nginx/conf.d/teams_bot.conf
nano ~/nginx/conf.d/teams_bot.conf
```

Add the following:

```nginx
server {
    listen 80;
    server_name bot.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 6. Set Up SSL with Let's Encrypt

Install Certbot and obtain an SSL certificate:

```bash
# Contact Hostinger support to help with SSL setup
# Or follow their documentation for Let's Encrypt setup
```

## 7. Update Teams Bot Endpoint

In the Azure Bot registration, update the messaging endpoint to:
`https://bot.yourdomain.com/api/messages`

## 8. Testing the Deployment

1. Check if the bot is running:
   ```bash
   curl http://127.0.0.1:8080/api/status
   ```

2. Check external access:
   ```bash
   curl https://bot.yourdomain.com/api/status
   ```

3. Test from Microsoft Teams by adding the bot to a team or chat.

## Monitoring and Troubleshooting

### Supervisor Commands

```bash
# Check status
supervisorctl status teams_bot

# Restart the bot
supervisorctl restart teams_bot

# View logs
tail -f ~/teams_bot/logs/teams_bot.out.log
tail -f ~/teams_bot/logs/teams_bot.err.log
```

### Common Issues

1. **504 Gateway Timeout**: Increase the timeout in Nginx configuration
2. **Memory Issues**: Check your hosting memory limits and reduce model sizes if needed
3. **Permission Errors**: Ensure proper file permissions

## Resource Management

Since Hostinger WordPress hosting has limited resources (1536 MB RAM, 2 CPU cores), consider:

1. Using the smallest models possible (tiny Whisper model, distilled NLLB model)
2. Limiting concurrent workers in Gunicorn
3. Monitoring memory usage and optimizing as needed

## Updating the Bot

To update the bot:

```bash
cd ~/teams_bot/teams-interpreter-bot
git pull  # If using git

# Update dependencies
source ~/teams_bot/venv/bin/activate
pip install -r requirements.txt

# Restart the service
supervisorctl restart teams_bot
```

## Security Considerations

1. Keep your `.env` file secure and never commit it to repositories
2. Regularly update dependencies for security patches
3. Consider adding basic auth to the `/api/status` endpoint
4. Ensure your bot token storage is secure

---

For additional assistance, contact Hostinger support or refer to their Python application hosting documentation. 