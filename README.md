# Martin Psychology App - Docker Deployment

This directory contains a Streamlit-based psychology application ready for deployment on remote servers using Docker and Docker Compose.

## 🚀 Remote Server Deployment Guide

### Prerequisites

Your remote server must have:
- **Docker Engine** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Open port** for web access (default: 8532)
- **Internet connection** for Docker image pulls

### Quick Remote Deployment

1. **Copy files to your server**:
   ```bash
   # Option 1: Using git clone
   git clone <repository-url> martin-app
   cd martin-app/Martin/
   
   # Option 2: Using scp
   scp -r Martin/ user@your-server:/opt/martin-app/
   ssh user@your-server
   cd /opt/martin-app/
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   nano .env  # Add your Groq API key
   ```

3. **Deploy with one command**:
   ```bash
   chmod +x quick-deploy.sh
   ./quick-deploy.sh
   ```

4. **Access your app**:
   - Local: `http://your-server-ip:8532`
   - Domain: `http://your-domain.com:8532`

### Manual Deployment Steps

If you prefer manual control:

```bash
# 1. Build and start
docker compose up -d --build

# 2. Verify deployment
docker ps
docker logs martin-psychology-app

# 3. Test health
curl http://localhost:8532/_stcore/health
```

## Files Structure

```
Martin/
├── app_psy_test.py          # Main Streamlit application
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker image configuration
├── docker-compose.yml      # Docker Compose configuration
├── .env.example           # Environment variables template
├── .dockerignore          # Docker ignore file
├── README.md              # This file
├── images/                # Static images
├── sounds/                # Audio files
└── data/                  # Application data (created automatically)
```

## Environment Variables

### Required
- `GROQ_API_KEY`: Your Groq API key for LLM functionality

### Optional
- `STREAMLIT_PORT`: Port to run the app (default: 8532)
- `STREAMLIT_HOST`: Host binding (default: 0.0.0.0)

## Server Configuration

### Firewall Setup

Make sure your server firewall allows the application port:

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 8532/tcp
sudo ufw reload

# CentOS/RHEL (firewalld) 
sudo firewall-cmd --add-port=8532/tcp --permanent
sudo firewall-cmd --reload

# Check if port is accessible
curl http://localhost:8532/_stcore/health
```

### Domain Setup (Optional)

If you have a domain name, point it to your server:

```bash
# DNS A Record
your-domain.com → your-server-ip

# Test access
curl http://your-domain.com:8532
```

## Configuration

### Setting up the API Key

1. Get your Groq API key from [https://console.groq.com/](https://console.groq.com/)
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and replace `your_groq_api_key_here` with your actual API key:
   ```
   GROQ_API_KEY=yourkey
   ```

### Custom Port

To run on a different port, modify `docker-compose.yml`:
```yaml
ports:
  - "8080:8501"  # External port 8080, internal port 8501
```

## �️ Deployment Scripts Explained

### 📄 **deploy.sh** - Full Interactive Management
**Purpose**: Complete deployment management with interactive menu system

**Features**:
- ✅ **Interactive menu** with 7 options (deploy, stop, restart, logs, status, update, exit)
- ✅ **Prerequisites checking** (Docker, Docker Compose installed)
- ✅ **Environment validation** (checks .env file, API key setup)
- ✅ **Health monitoring** (waits and checks if app is healthy)
- ✅ **Error handling** (colored output, detailed error messages)
- ✅ **Directory management** (creates necessary folders)
- ✅ **Multiple operations** (deploy, manage, monitor, troubleshoot)

**Usage**:
```bash
chmod +x deploy.sh

# Interactive mode (recommended)
./deploy.sh

# Command line mode
./deploy.sh deploy    # Deploy application
./deploy.sh stop      # Stop application  
./deploy.sh restart   # Restart application
./deploy.sh logs      # Show logs
./deploy.sh status    # Show status
./deploy.sh update    # Update application
```

### ⚡ **quick-deploy.sh** - One-Command Deployment
**Purpose**: Fast deployment with minimal interaction

**Features**:
- ✅ **One-command deployment** (no menu, runs immediately)
- ✅ **API key prompt** (asks for key if not set)
- ✅ **Basic checks** (Docker running)
- ✅ **Auto-setup** (creates .env, directories, deploys)
- ✅ **Quick health check** (simple success/failure)

**Usage**:
```bash
chmod +x quick-deploy.sh
./quick-deploy.sh
# App will be running in ~30 seconds
```

### 🤔 **When to Use Which?**

| Situation | Use Script | Reason |
|-----------|------------|---------|
| **First time setup** | `deploy.sh` | Better validation and error handling |
| **Production environment** | `deploy.sh` | More robust, interactive management |
| **Quick testing** | `quick-deploy.sh` | Faster, minimal setup |
| **Automated deployment** | `quick-deploy.sh` | Single command, scriptable |
| **Troubleshooting needed** | `deploy.sh` | Built-in logging and status tools |
| **CI/CD pipeline** | `quick-deploy.sh` | Non-interactive, predictable |

## 🌍 **Accessing Your App from Outside the Server**

### 1. **Find Your Server's External IP Address**

```bash
# Method 1: Check your public IP
curl ifconfig.me

# Method 2: Check network interfaces  
ip addr show
# or
ifconfig

# Method 3: Check cloud provider dashboard
# AWS: EC2 → Instances → Public IPv4 address
# DigitalOcean: Droplets → Your droplet → Public IP
# Google Cloud: Compute Engine → VM instances → External IP
```

### 2. **Access URLs for External Users**

Once deployed, your app will be accessible at:

```bash
# If you have a domain name:
http://your-domain.com:8532
https://your-domain.com:8532  # with SSL setup

# If using IP address:
http://YOUR_SERVER_IP:8532

# Examples:
http://123.45.67.89:8532
http://martin-app.yourdomain.com:8532
```

### 3. **Test External Access**

```bash
# From your local computer, test:
curl http://YOUR_SERVER_IP:8532/_stcore/health

# If this works, the app is accessible externally
# If it fails, check firewall settings below
```

### 4. **Firewall Configuration for External Access**

**Ubuntu/Debian (UFW)**:
```bash
# Allow the app port
sudo ufw allow 8532/tcp
sudo ufw status

# Allow from specific IP only (more secure)
sudo ufw allow from YOUR_IP to any port 8532
```

**CentOS/RHEL (firewalld)**:
```bash
# Allow the app port
sudo firewall-cmd --add-port=8532/tcp --permanent
sudo firewall-cmd --reload
sudo firewall-cmd --list-ports
```

**Cloud Provider Security Groups**:
- **AWS**: EC2 → Security Groups → Add inbound rule (Port 8532, Source: 0.0.0.0/0 or your IP)
- **DigitalOcean**: Droplet → Networking → Firewalls → Add rule
- **Google Cloud**: VPC network → Firewall → Create rule

### 5. **Production Setup for External Access (Recommended)**

For production, set up a reverse proxy instead of direct port access:

```bash
# Install nginx
sudo apt install nginx

# Create config
sudo nano /etc/nginx/sites-available/martin-app
```

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain
    
    location / {
        proxy_pass http://localhost:8532;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# Enable and test
sudo ln -s /etc/nginx/sites-available/martin-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Now accessible at: http://your-domain.com (port 80)
```

### 6. **SSL/HTTPS Setup for Secure External Access**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get free SSL certificate
sudo certbot --nginx -d your-domain.com

# Now accessible at: https://your-domain.com (secure)
```

### 7. **Troubleshooting External Access**

```bash
# Check if app is running locally
curl http://localhost:8532/_stcore/health

# Check if port is open on the server
sudo netstat -tlnp | grep 8532

# Check Docker port binding
docker port martin-psychology-app

# Test from outside (replace with your server IP)
telnet YOUR_SERVER_IP 8532

# Check firewall logs
sudo ufw status verbose  # Ubuntu
sudo firewall-cmd --list-all  # CentOS
```

### Start the application
```bash
docker compose up -d
```

### View logs
```bash
docker compose logs -f martin-psychology-app
```

### Stop the application
```bash
docker compose down
```

### Restart the application
```bash
docker compose restart
```

### Update the application
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Check container status
```bash
docker ps
docker stats martin-psychology-app
```

## Health Monitoring

The application includes health checks:
- Health endpoint: `http://your-server:8532/_stcore/health`
- Docker health checks run every 30 seconds
- Application restart on failure

## 🔧 Remote Server Troubleshooting

### Application won't start
1. **Check if Docker is running**:
   ```bash
   sudo systemctl status docker
   sudo systemctl start docker  # if stopped
   ```

2. **Check port availability**:
   ```bash
   sudo netstat -tulpn | grep 8532
   # Kill process if port is occupied
   sudo kill -9 $(sudo lsof -t -i:8532)
   ```

3. **Check Docker logs**:
   ```bash
   docker compose logs martin-psychology-app
   ```

4. **Verify Docker Compose syntax**:
   ```bash
   docker compose config
   ```

### Connection issues from outside
1. **Check server firewall**:
   ```bash
   sudo ufw status
   curl http://localhost:8532  # Test locally first
   ```

2. **Check if service is accessible**:
   ```bash
   # Test from another machine
   curl http://your-server-ip:8532/_stcore/health
   ```

3. **Verify Docker port binding**:
   ```bash
   docker port martin-psychology-app
   ```

### API Key issues
1. **Verify your API key** is correctly set in `.env`:
   ```bash
   cat .env | grep GROQ_API_KEY
   ```
2. **Test the API key**:
   ```bash
   curl -H "Authorization: Bearer your_api_key" https://api.groq.com/openai/v1/models
   ```
3. **Restart after changing .env**:
   ```bash
   docker compose restart
   ```

### Performance issues
1. **Check container resources**:
   ```bash
   docker stats martin-psychology-app
   ```
2. **Check server resources**:
   ```bash
   free -h    # Memory usage
   df -h      # Disk usage
   top        # CPU usage
   ```
3. **Adjust memory limits** in `docker-compose.yml` if needed

## 🌐 Production Deployment on Remote Server

### 1. Install Docker on Your Server

**Ubuntu/Debian:**
```bash
# Update package index
sudo apt update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

**CentOS/RHEL:**
```bash
# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
```

### 2. Secure Your Deployment

**Basic Security Setup:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8532/tcp

# Create non-root user for deployment
sudo adduser martin-app
sudo usermod -aG docker martin-app
```

### 3. Set Up Reverse Proxy (Recommended)

**Nginx Configuration:**
```bash
# Install nginx
sudo apt install nginx

# Create config file
sudo nano /etc/nginx/sites-available/martin-app
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8532;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/martin-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. SSL/HTTPS Setup (Production)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 5. Auto-start on Boot

**Create systemd service:**
```bash
sudo nano /etc/systemd/system/martin-app.service
```

```ini
[Unit]
Description=Martin Psychology App
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/martin-app
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0
User=martin-app

[Install]
WantedBy=multi-user.target
```

```bash
# Enable auto-start
sudo systemctl enable martin-app.service
sudo systemctl start martin-app.service
```

## 📊 Data Persistence

The following directories are mounted for data persistence:
- `./data` - Application data and user sessions
- `./sounds` - Audio files  
- `./images` - Static images

These directories will persist data even when containers are recreated.

## 🔒 Security Considerations

1. **API Key Security**: Never commit your `.env` file to version control
2. **Network Security**: Use a reverse proxy (nginx) for production deployments
3. **SSL/TLS**: Enable HTTPS in production with Let's Encrypt
4. **Firewall**: Restrict access to necessary ports only
5. **User Permissions**: Run containers as non-root user
6. **Updates**: Keep Docker and system packages updated

## 📈 Monitoring and Maintenance

### Check Application Health
```bash
# Health check endpoint
curl http://your-server:8532/_stcore/health

# Container status
docker ps
docker stats martin-psychology-app

# Application logs
docker compose logs -f martin-psychology-app
```

### Regular Maintenance
```bash
# Update application
cd /opt/martin-app
git pull  # if using git
docker compose down
docker compose build --no-cache
docker compose up -d

# Clean up unused Docker resources
docker system prune -f
```

## 🆘 Support and Troubleshooting

### Common Issues

1. **Port already in use**: Change port in `docker-compose.yml`
2. **Permission denied**: Add user to docker group
3. **Cannot connect externally**: Check firewall and port binding
4. **API errors**: Verify Groq API key and connectivity
5. **Performance issues**: Check server resources and Docker limits

### Getting Help

1. Check the application logs: `docker compose logs martin-psychology-app`
2. Verify environment configuration: `cat .env`
3. Test API connectivity: `curl https://api.groq.com/openai/v1/models`
4. Check Docker/system resources: `docker stats` and `free -h`

### Remote Access Examples

```bash
# Local access
http://localhost:8532

# Remote IP access  
http://123.45.67.89:8532

# Domain access (with nginx)
http://your-domain.com

# HTTPS access (with SSL)
https://your-domain.com
```

## License

This application is for internal use. Please ensure compliance with all relevant licenses for dependencies.
