# Deploy slop.at to Digital Ocean

## Quick Deploy

### 1. Create a Droplet

- **Image**: Ubuntu 24.04 LTS
- **Size**: Basic ($6/month is plenty)
- **Datacenter**: Choose closest to you
- **Add SSH key**: Your public key

### 2. Install Docker on Droplet

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt-get install docker-compose-plugin
```

### 3. Configure DNS

Point your domain to the droplet IP:
- `A` record: `slop.at` → `your-droplet-ip`

### 4. Deploy

```bash
# Clone repo
git clone https://github.com/slop-at/slop-at-www.git
cd slop-at-www

# Start services (includes Caddy for automatic HTTPS)
docker compose up -d

# Check logs
docker compose logs -f
```

Done! Caddy will automatically get HTTPS certificates from Let's Encrypt.

Your server is live at **https://slop.at**

## Update

```bash
cd slop-at-www
git pull
docker compose down
docker compose up -d --build
```

## Backup

Data is stored in Docker volumes:
- `oxigraph-data` - RDF graph database
- `slop-data` - Rendered slop files

```bash
# Backup
docker run --rm -v slop-at-www_oxigraph-data:/data -v $(pwd):/backup ubuntu tar czf /backup/oxigraph-backup.tar.gz /data
docker run --rm -v slop-at-www_slop-data:/data -v $(pwd):/backup ubuntu tar czf /backup/slops-backup.tar.gz /data

# Restore
docker run --rm -v slop-at-www_oxigraph-data:/data -v $(pwd):/backup ubuntu tar xzf /backup/oxigraph-backup.tar.gz -C /
docker run --rm -v slop-at-www_slop-data:/data -v $(pwd):/backup ubuntu tar xzf /backup/slops-backup.tar.gz -C /
```
