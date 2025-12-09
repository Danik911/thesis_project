# Documentation

## Quick Navigation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, multi-agent design, Docker stack |
| [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) | AWS ECS/Fargate infrastructure, deployment commands |
| [GITHUB_ACTIONS_DEPLOYMENT.md](GITHUB_ACTIONS_DEPLOYMENT.md) | CI/CD pipeline with OIDC authentication |
| [DOCKER.md](DOCKER.md) | Local Docker Compose development |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Core files and directory layout |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions |

## Getting Started

1. **Local Development**: See [DOCKER.md](DOCKER.md) for Docker Compose quickstart
2. **AWS Deployment**: See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) or use `/deploy` command
3. **CI/CD**: Push to `deploy` branch triggers [GitHub Actions](GITHUB_ACTIONS_DEPLOYMENT.md)

## Live System

| Environment | URL |
|-------------|-----|
| Production | https://csvgeneration.com |
| API Health | https://csvgeneration.com/health |

## Issues

Active issues are tracked in [issues/](issues/) directory. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common solutions.
