# 2Dto3D Video Converter - Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the 2Dto3D Video Converter service with GPU support, auto-scaling, load balancing, and high availability.

## Prerequisites

### Required
- Kubernetes cluster (v1.24+)
- kubectl configured to access your cluster
- NVIDIA GPU nodes with CUDA support
- NVIDIA GPU Operator or Kubernetes NVIDIA Device Plugin
- Metrics Server (for HPA)

### Optional (Recommended)
- NGINX Ingress Controller
- cert-manager (for TLS)
- Prometheus Adapter (for custom metrics HPA)
- Storage class with ReadWriteMany support (for shared storage - see pvc.yaml for details)

## Directory Structure

```
k8s/
├── base/                      # Base manifests (environment-agnostic)
│   ├── namespace.yaml         # Namespace definition
│   ├── configmap.yaml         # Application configuration
│   ├── secrets.yaml           # Secrets template
│   ├── pvc.yaml               # Persistent volume claims
│   ├── deployment.yaml        # GPU-enabled deployment
│   ├── service.yaml           # Service definitions
│   ├── hpa.yaml               # Horizontal pod autoscaler
│   ├── ingress.yaml           # Ingress configuration
│   ├── rbac.yaml              # Service account and RBAC
│   ├── pdb.yaml               # Pod disruption budget
│   ├── resource-quota.yaml    # Namespace resource quotas and limits
│   └── kustomization.yaml     # Base kustomization
├── overlays/
│   ├── dev/                   # Development overlay
│   │   └── kustomization.yaml
│   └── prod/                  # Production overlay
│       └── kustomization.yaml
└── README.md
```

## Quick Start

### 1. Build and Push Docker Image

```bash
# Build GPU image
docker build -t video2d3d:gpu -f Dockerfile .

# Tag for your registry
docker tag video2d3d:gpu your-registry.com/video2d3d:gpu

# Push to registry
docker push your-registry.com/video2d3d:gpu
```

### 2. Update Image Reference

Edit `k8s/base/kustomization.yaml` or overlay files to reference your image:

```yaml
images:
  - name: video2d3d
    newName: your-registry.com/video2d3d
    newTag: "gpu"
```

### 3. Configure Storage Class

Update `pvc.yaml` to match your cluster's storage classes:

```yaml
spec:
  storageClassName: your-storage-class  # e.g., standard, gp2, nfs, etc.
```

**IMPORTANT**: Most PVCs use `ReadWriteMany` access mode which requires storage classes like NFS, AWS EFS, Azure File, or GCP Filestore. See `pvc.yaml` for details.

### 4. Deploy to Development

```bash
# Deploy with development settings
kubectl apply -k k8s/overlays/dev/

# Verify deployment
kubectl get pods -n video2d3d-dev
kubectl get services -n video2d3d-dev
```

### 5. Deploy to Production

```bash
# Deploy with production settings
kubectl apply -k k8s/overlays/prod/

# Verify deployment
kubectl get pods -n video2d3d-prod
kubectl get services -n video2d3d-prod
kubectl get hpa -n video2d3d-prod
```

## Configuration

### Environment Variables

Key environment variables are configured in `configmap.yaml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `VIDEO2D3D_ENV` | `production` | Environment (development/production) |
| `VIDEO2D3D_LOG_LEVEL` | `INFO` | Logging level |
| `API_PORT` | `8000` | API server port |
| `VIDEO2D3D_BATCH_SIZE` | `4` | Processing batch size |
| `VIDEO2D3D_NUM_WORKERS` | `4` | Number of worker processes |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU device IDs |
| `VIDEO2D3D_USE_GPU` | `true` | Enable GPU processing |
| `INPUT_DIR` | `/app/inputs` | Input directory |
| `OUTPUT_DIR` | `/app/outputs` | Output directory |
| `UPLOAD_DIR` | `/app/uploads` | Upload directory |
| `MODELS_DIR` | `/app/models` | Model cache directory |

### Secrets

Copy `secrets.yaml` and update with your values:

```bash
# Create secrets manually
kubectl create secret generic video2d3d-secrets \
  --from-literal=API_KEY=your-api-key \
  -n video2d3d
```

### Ingress Configuration

1. Update the host in `ingress.yaml`:
   ```yaml
   spec:
     rules:
       - host: video2d3d.your-domain.com
   ```

2. For TLS with cert-manager:
   ```yaml
   spec:
     tls:
       - hosts:
           - video2d3d.your-domain.com
         secretName: video2d3d-tls
   annotations:
     cert-manager.io/cluster-issuer: "letsencrypt-prod"
   ```

**Note**: The ingress uses `ingressClassName: nginx` which is the modern approach (replacing the deprecated `kubernetes.io/ingress.class` annotation).

## GPU Scheduling

### Node Requirements

GPU nodes should have the following labels:

```bash
# Label GPU nodes
kubectl label nodes <gpu-node> nvidia.com/gpu.present=true
```

### GPU Resource Requests

The deployment requests 1 GPU per pod:

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
  requests:
    nvidia.com/gpu: 1
```

### GPU Node Taints

If your GPU nodes are tainted:

```bash
# Taint GPU nodes
kubectl taint nodes <gpu-node> nvidia.com/gpu=true:NoSchedule
```

The deployment includes tolerations for this taint.

## Auto-Scaling

### HPA Configuration

The Horizontal Pod Autoscaler scales based on:

- **CPU**: Scale up when > 70% utilization
- **Memory**: Scale up when > 80% utilization

**Note**: Only ONE HPA can target a deployment at a time. Custom metrics HPA (for queue depth, GPU utilization) is provided as an alternative - see `hpa.yaml` for details.

### Scaling Behavior

- **Scale up**: Aggressive - can double pods every 15 seconds
- **Scale down**: Conservative - 10% reduction every 60 seconds, 5-minute stabilization

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment video2d3d-api -n video2d3d --replicas=5

# Check HPA status
kubectl get hpa -n video2d3d
```

## Resource Management

### Resource Quotas

The deployment includes `resource-quota.yaml` which sets namespace-level limits:

- **CPU**: 20 requests / 40 limits
- **Memory**: 128Gi requests / 256Gi limits
- **GPUs**: 10 requests / 10 limits
- **Storage**: 500Gi total
- **Pods**: Maximum 20

### Limit Ranges

Default container limits are set:

| Resource | Request | Limit |
|----------|---------|-------|
| CPU | 500m | 2 |
| Memory | 2Gi | 8Gi |

Adjust these values in `resource-quota.yaml` based on your cluster capacity.

## Monitoring

### Health Endpoints

- `/health` - Basic health check (returns 200 if healthy)
- `/health/detailed` - Comprehensive health with GPU, memory, and queue stats

### Prometheus Metrics

Prometheus metrics are exposed at port 8000. Configure your Prometheus to scrape:

```yaml
# Prometheus scrape config
- job_name: 'video2d3d'
  kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
          - video2d3d
  relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: true
```

### Log Aggregation

Application logs are written to `/app/logs` and stdout. Configure your log aggregator to collect from pods.

## Security Features

The deployment includes several security hardening measures:

1. **Run as non-root**: Pods run as user 1000 by default
2. **Seccomp profile**: Uses `RuntimeDefault` seccomp profile
3. **Read-only root filesystem**: Partially enabled (temp files needed)
4. **Drop capabilities**: All Linux capabilities dropped
5. **Network policies**: Configured to restrict ingress and egress traffic
6. **Service account**: Token not auto-mounted unless needed
7. **Secrets**: Use external secret management in production
8. **TLS**: Enable TLS for production ingress

## Troubleshooting

### Check Pod Status

```bash
# List pods
kubectl get pods -n video2d3d

# Describe pod
kubectl describe pod <pod-name> -n video2d3d

# View logs
kubectl logs <pod-name> -n video2d3d
kubectl logs -f <pod-name> -n video2d3d  # Follow logs
```

### Common Issues

1. **Pod stuck in Pending**
   - Check if GPU nodes are available
   - Verify storage class exists and supports ReadWriteMany (if using RWX)
   - Check resource quotas
   - Verify node affinity requirements

2. **GPU not detected**
   - Verify NVIDIA GPU Operator is running
   - Check node has `nvidia.com/gpu` resource
   - Verify CUDA is installed

3. **Health check failing**
   - Check pod logs for errors
   - Verify API server is running on port 8000
   - Increase `initialDelaySeconds` for slower startup

4. **Ingress not working**
   - Verify ingress controller is installed
   - Check DNS resolution
   - Verify TLS certificate
   - Check `ingressClassName` matches your controller

5. **PVC stuck in Pending**
   - Verify storage class exists
   - Check if storage class supports ReadWriteMany access mode
   - Verify sufficient storage available

### Debug Mode

Enable debug logging:

```bash
# Update configmap
kubectl patch configmap video2d3d-config -n video2d3d \
  --type merge -p '{"data":{"VIDEO2D3D_LOG_LEVEL":"DEBUG"}}'

# Restart pods to apply
kubectl rollout restart deployment video2d3d-api -n video2d3d
```

## Cleanup

```bash
# Delete development deployment
kubectl delete -k k8s/overlays/dev/

# Delete production deployment
kubectl delete -k k8s/overlays/prod/

# Delete namespace (removes all resources)
kubectl delete namespace video2d3d
```

## Production Checklist

- [ ] Update image registry URL
- [ ] Configure production TLS certificates
- [ ] Set up external secret management
- [ ] Configure log aggregation
- [ ] Set up Prometheus monitoring
- [ ] Configure backup for PVs
- [ ] Review and update resource limits/quotas
- [ ] Configure alerting rules
- [ ] Set up CI/CD pipeline
- [ ] Document runbooks for incidents
- [ ] Verify storage class supports required access modes
- [ ] Test failover and scaling scenarios
