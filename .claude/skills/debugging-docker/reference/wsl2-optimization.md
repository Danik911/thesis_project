# WSL2 Docker Performance Optimization

Performance tips and troubleshooting for running Docker in WSL2 environment.

---

## Memory Management

### Problem: vmmem Process Consuming Excessive RAM

**Symptom:** Task Manager shows `vmmem` using 8GB+ RAM even when idle

**Root Cause:** WSL2 VM doesn't automatically release memory back to Windows

**Solution:** Configure `.wslconfig` to limit resources

Create/edit `C:\Users\<username>\.wslconfig`:
```ini
[wsl2]
memory=8GB          # Limit VM memory
processors=4        # Limit CPU cores
swap=2GB            # Swap size
localhostForwarding=true
guiApplications=false
nestedVirtualization=false
```

**Apply changes:**
```powershell
wsl --shutdown
# Wait 8 seconds, then restart WSL
wsl
```

### Reclaiming Memory

```powershell
# Force WSL shutdown to reclaim all memory
wsl --shutdown

# Verify WSL is stopped
wsl --list --running  # Should be empty
```

---

## Filesystem Performance

### Critical: Where You Store Files Matters

| Location | Performance | Use Case |
|----------|-------------|----------|
| `/home/user/` (WSL2 filesystem) | **Fast** | Docker projects, builds |
| `/mnt/c/...` (Windows mount) | **5-10x slower** | Windows-only files |

### Symptoms of Cross-Filesystem Slowdown

- Docker builds take 5-10x longer than expected
- `npm install` extremely slow
- File watchers (hot reload) lag significantly

### Best Practice

```bash
# GOOD: Work in WSL2 filesystem
cd ~/projects/my-docker-app
docker build -t myapp .

# BAD: Working from Windows mount
cd /mnt/c/Users/me/projects/my-docker-app
docker build -t myapp .  # Much slower!
```

### Migrating Projects

```bash
# Copy project from Windows to WSL2 filesystem
cp -r /mnt/c/Users/me/projects/myapp ~/projects/

# Or clone fresh in WSL2
cd ~/projects
git clone <repo-url>
```

---

## Docker-Specific WSL2 Issues

### Docker Daemon Not Starting

**Symptom:** `Cannot connect to the Docker daemon`

**Check Docker status:**
```bash
sudo service docker status
```

**Start Docker:**
```bash
sudo service docker start

# Or enable systemd (Ubuntu 22.04+)
sudo systemctl enable docker
sudo systemctl start docker
```

### WSL2 Integration Issues (Docker Desktop)

If using Docker Desktop with WSL2 backend:

1. Check Docker Desktop → Settings → Resources → WSL Integration
2. Enable integration for your distro
3. Restart Docker Desktop

### Native Docker in WSL2 (Recommended)

For better performance, install Docker Engine directly in WSL2:
```bash
# Install Docker Engine (Ubuntu)
sudo apt update
sudo apt install docker.io

# Add user to docker group
sudo usermod -aG docker $USER

# Enable and start
sudo systemctl enable docker
sudo systemctl start docker
```

---

## Network Configuration

### localhost Forwarding

Ensure `.wslconfig` has:
```ini
localhostForwarding=true
```

### Port Access from Windows

Containers running in WSL2 should be accessible via `localhost:<port>` from Windows.

**If not working:**
```bash
# Check container is binding to 0.0.0.0
docker ps  # Check PORTS column

# Run with explicit bind
docker run -p 0.0.0.0:8080:8080 myapp
```

---

## Quick Checklist

- [ ] `.wslconfig` configured with memory limits
- [ ] Projects stored in WSL2 filesystem (`~/`), not Windows mount (`/mnt/c/`)
- [ ] Docker daemon running (`service docker status`)
- [ ] User in docker group (`groups` should show docker)
- [ ] Periodic `wsl --shutdown` to reclaim memory
