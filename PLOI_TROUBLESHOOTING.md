# Ploi Deployment Troubleshooting Guide

## Recent Fixes Applied ✓

- ✓ Secured `.env.production` (removed exposed API keys)
- ✓ Fixed frontend API URL routing (`http://localhost/api` instead of `http://10.122.0.3:8080/api`)
- ✓ Updated `.ploi.yml` with proper working directory paths
- ✓ Added error handling and health checks

---

## Common Ploi Deployment Issues & Solutions

### 1. **Environment Variables Not Set**

**Error signs:**
- `GEMINI_API_KEY` / `NEWS_API_KEY` / `SERPER_API_KEY` errors
- `SECRET_KEY` not found
- Database connection refused

**Solution:**

In Ploi Dashboard → Environment Variables, set ALL of these:

```
SECRET_KEY=<your-random-secret-generate-with: openssl rand -hex 32>
DB_PASSWORD=<your-secure-password-min-16-chars>
GEMINI_API_KEY=<your-api-key>
NEWS_API_KEY=<your-api-key>
SERPER_API_KEY=<your-api-key>
```

**IMPORTANT**: These should NEVER be committed to git. They must be set in Ploi dashboard only.

---

### 2. **Docker Build Failures**

**Error signs:**
- `docker-compose build Failed`
- `npm ci Failed` (Next.js)
- `pip install Failed` (Python)

**Solutions:**

```bash
# SSH into server and check logs
ssh user@your-ploi-server

# Check Docker build status
docker-compose -f docker-compose.production.yml logs backend
docker-compose -f docker-compose.production.yml logs frontend

# Rebuild manually to troubleshoot
cd /opt/political-bias-detector
docker-compose -f docker-compose.production.yml build --no-cache backend
docker-compose -f docker-compose.production.yml build --no-cache frontend
```

---

### 3. **Port Already in Use**

**Error:** `Port 80 already in use` or `Port 443 already in use`

**Solution:**

```bash
# Find what's using the port
sudo lsof -i :80
sudo lsof -i :443

# Stop conflicting services
sudo systemctl stop apache2  # if Apache is running
sudo systemctl stop nginx    # if system nginx is running

# Or change port in docker-compose.production.yml
# Change: ports: - "80:80" to "8080:80"
```

---

### 4. **Database Connection Issues**

**Error:** `Can't connect to PostgreSQL` or `database does not exist`

**Debug:**

```bash
# Check if postgres container is running
docker-compose -f docker-compose.production.yml ps postgres

# Check postgres logs
docker-compose -f docker-compose.production.yml logs postgres

# Try connecting to database
docker-compose -f docker-compose.production.yml exec postgres psql -U pbd_user -d political_bias_detector

# Check if database was initialized
docker-compose -f docker-compose.production.yml exec postgres psql -U pbd_user -c "\l"
```

**Fix:**

```bash
# Remove old database volume and recreate
docker-compose -f docker-compose.production.yml down -v
docker-compose -f docker-compose.production.yml up -d
```

---

### 5. **Backend (API) Not Responding**

**Error:** `502 Bad Gateway` or backend returning errors

**Debug:**

```bash
# Check backend logs
docker-compose -f docker-compose.production.yml logs -f backend

# Check if backend is healthy
curl http://localhost:8000/health

# Check from nginx container
docker-compose -f docker-compose.production.yml exec nginx curl http://backend:8000/health
```

**Common backend issues:**
- Missing environment variables → Set in Ploi dashboard
- Model files not found → Check `models/` directory exists
- API keys invalid → Verify in Ploi environment

---

### 6. **Frontend (Next.js) Not Building**

**Error:** `npm run build Failed` or `npm ci Failed`

**Debug:**

```bash
# Check frontend logs
docker-compose -f docker-compose.production.yml logs -f frontend

# Manual build to see errors
cd frontend-nextjs
npm ci
npm run build
```

**Common issues:**
- Missing `next.config.js` configuration
- TypeScript errors
- Missing dependencies in `package.json`

---

### 7. **Nginx Routing Issues**

**Error:** `404 Not Found` for API calls

**Signs:**
- Frontend loads but API calls fail
- `http://server/api/` returns 404
- Backend is running fine locally

**Debug:**

```bash
# Check nginx configuration
docker-compose -f docker-compose.production.yml exec nginx cat /etc/nginx/conf.d/default.conf

# Check nginx logs
docker-compose -f docker-compose.production.yml logs nginx

# Test routing
curl -v http://localhost/api/health
curl -v http://localhost/health
```

**Solution:** Verify `nginx/conf.d/default.conf` has correct upstream configuration.

---

## Full Deployment Checklist

Before deploying, verify:

### Ploi Dashboard Settings:
- [ ] Git repository connected (GitHub URL set)
- [ ] Branch set to `main`
- [ ] All environment variables set (see step 1)
- [ ] Deployment trigger set to auto-deploy on push
- [ ] Server has minimum 2GB RAM
- [ ] Port 80 and 443 are available (not blocked by firewall)

### Repository:
- [ ] `.ploi.yml` is updated and committed
- [ ] `docker-compose.production.yml` exists
- [ ] `Dockerfile.backend` exists
- [ ] `frontend-nextjs/Dockerfile` exists
- [ ] `.env.production` exists (with placeholders only)
- [ ] NO sensitive values in `.env.production` or `.ploi.yml`

### Commands to Verify Setup Locally:

```bash
# Test docker-compose locally
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up

# Should see all 4 services running:
# - postgres
# - backend (http://localhost:8000/health)
# - frontend (http://localhost:3000/)
# - nginx (http://localhost/)
```

---

## Manual Deploy Steps (if auto-deploy fails)

```bash
# SSH into server
ssh user@your-ploi-server

# Navigate to project
cd /opt/political-bias-detector

# Pull latest code
git pull origin main

# Set environment variables
export SECRET_KEY="<your-key>"
export DB_PASSWORD="<your-password>"
export GEMINI_API_KEY="<your-api-key>"
export NEWS_API_KEY="<your-api-key>"
export SERPER_API_KEY="<your-api-key>"

# Deploy
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml build --pull
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

---

## Still Not Working?

### Collect Debug Information:

```bash
# System information
uname -a
docker --version
docker-compose --version

# Check disk space
df -h

# Check memory
free -h

# Docker system info
docker system info

# Service status
docker-compose -f docker-compose.production.yml ps
docker-compose -f docker-compose.production.yml logs

# Network check
docker network ls
docker network inspect pbd-network
```

### Common Environment Issues:

1. **API Keys are test/invalid**
   - Verify GEMINI_API_KEY is active in Google Cloud Console
   - Verify NEWS_API_KEY from NewsAPI.org
   - Verify SERPER_API_KEY from Serper.dev

2. **Models missing**
   ```bash
   mkdir -p models/custom_bias_detector
   mkdir -p models/intensity
   # Models will auto-download on first backend startup
   ```

3. **Permission issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER /opt/political-bias-detector
   chmod +x scripts/*.sh
   ```

---

## Ploi-Specific Tips

1. **Enable Ploi SSH Access**: Ploi Dashboard → Site → SSH Keys → Generate
2. **Monitor Logs Live**: Ploi Dashboard → Deployments → View Logs
3. **Rollback Deploy**: Ploi Dashboard → Deployments → Previous → Rollback
4. **Restart Services**: Ploi Dashboard → Restart Site
5. **Check Uptime**: Ploi Dashboard → Health → Monitor Services

---

## Need Help?

1. **Check Ploi Console Logs**: Ploi Dashboard → Deployments → Latest
2. **SSH to server**: `ssh user@your-ploi-server`
3. **Run diagnostics**: `docker-compose -f docker-compose.production.yml logs --tail 50`
4. **Check GitHub webhooks**: Settings → Webhooks → Verify delivery

---

**Last Updated**: February 17, 2026  
**For Issues**: Contact your platform administrator or check Ploi documentation
