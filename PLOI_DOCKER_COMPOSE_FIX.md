# Ploi Server Setup - Docker Compose Fix

## Problem
```
docker-compose: command not found
```

This means Docker Compose (either v1 or v2) is not available on the Ploi server.

---

## Solution

### Option 1: Automatic (Using Wrapper Script) ✓ 
The `.ploi.yml` now uses a wrapper script (`scripts/docker-compose-wrapper.sh`) that automatically handles both:
- **Docker Compose v2** (`docker compose` - built into newer Docker)
- **Docker Compose v1** (`docker-compose` - standalone binary)

This should work automatically on your next deployment.

### Option 2: Manual - SSH to Server & Install

```bash
# SSH into your Ploi server
ssh user@your-ploi-server

# Check what's available
docker --version
docker compose version   # Try v2 first
docker-compose --version  # Try v1

# If neither work, install Docker Compose v2
# (Most modern Ploi servers have this, but just in case)
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o docker-compose
sudo mv docker-compose /usr/local/bin/
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker-compose --version
```

---

## Steps to Deploy Now

### 1. Commit the fixes
```bash
git add scripts/docker-compose-wrapper.sh .ploi.yml
git commit -m "Fix: Add Docker Compose wrapper for v1/v2 compatibility"
git push origin main
```

### 2. In Ploi Dashboard
- Go to your site settings
- Click "Deploy" or "Re-deploy"
- Wait for the deployment to complete

### 3. Monitor the logs
- You should see the wrapper script execute
- If still failing, check the server manually

---

## Manual Deployment (if Ploi fails again)

```bash
ssh user@your-ploi-server

cd /opt/political-bias-detector

# Test the wrapper
chmod +x scripts/docker-compose-wrapper.sh
./scripts/docker-compose-wrapper.sh --version

# If it works, deploy manually
./scripts/docker-compose-wrapper.sh -f docker-compose.production.yml build --pull
./scripts/docker-compose-wrapper.sh -f docker-compose.production.yml up -d
./scripts/docker-compose-wrapper.sh -f docker-compose.production.yml ps
```

---

## Verify After Deployment

Once deployed, check:

```bash
# SSH into server
ssh user@your-ploi-server

# Check container status
docker ps -a

# Check logs
docker-compose -f docker-compose.production.yml logs --tail 50

# Test endpoints
curl http://localhost/health
curl http://localhost/api/docs
```

Expected running containers:
- `pbd-postgres` (database)
- `pbd-backend` (API on port 8000)
- `pbd-frontend` (Next.js on port 3000)
- `pbd-nginx` (reverse proxy on ports 80/443)

---

## Still Having Issues?

### Check Docker Installation
```bash
which docker
which docker-compose
docker ps
```

### View Ploi Deployment Log
In Ploi Dashboard → **Deployments** → Click the failed deployment → View full logs

### Common Issues

| Issue | Solution |
|-------|----------|
| `docker: command not found` | Docker not installed. Contact Ploi support. |
| `permission denied` | Run with `sudo` or add user to docker group: `sudo usermod -aG docker $USER` |
| `Connection refused` | Check firewall. Ports 80, 443, 5432 might be blocked. |
| `Out of disk space` | Run `docker system prune` to clean up |

---

## Need More Help?

1. **Ploi Docs**: https://docs.ploi.io/
2. **Docker Compose Install**: https://docs.docker.com/compose/install/
3. **GitHub Issues**: Check if there are known deployment issues

