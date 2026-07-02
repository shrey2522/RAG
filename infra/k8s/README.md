# Deploying to Kubernetes (Docker Desktop)

## Prerequisites
- Docker Desktop with Kubernetes enabled
  - Settings → Kubernetes → "Enable Kubernetes" → Apply & Restart
- kubectl (comes with Docker Desktop)

## Steps

### 1. Build the Docker image
```powershell
# From the Rag/ directory
docker build -t rag-mcp-api:latest .
```

### 2. Set up the API key secret
```powershell
kubectl create secret generic rag-secrets --from-literal=google_api_key="YOUR_GEMINI_API_KEY"
```

### 3. Deploy to Kubernetes
```powershell
kubectl apply -f infra/k8s/deployment.yaml
kubectl apply -f infra/k8s/service.yaml
```

### 4. Check status
```powershell
kubectl get pods
kubectl get services
```

### 5. Access the API
The service runs on `localhost:8000` via Docker Desktop's LoadBalancer.

### 6. Scale (if needed)
```powershell
kubectl scale deployment rag-mcp-api --replicas=3
```

### Teardown
```powershell
kubectl delete -f infra/k8s/
```
