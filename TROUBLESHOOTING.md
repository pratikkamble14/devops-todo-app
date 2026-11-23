# K8s Troubleshooting — DevOps Todo App

Focused Kubernetes troubleshooting based on actual commands run (kind cluster, kubectl ops, devops-todo-app k8s manifests).

---

## 1. Kind Cluster Setup (what you ran)

```bash
kubectl version --client
which kubectl
sudo apt install kubectl
kind create cluster --config kind-config.yml
kubectl cluster-info
kubectl config current-context
kubectl config use-context kind-basic-cluster
kubectl get nodes
kubectl describe node basic-cluster-control-plane
kind get nodes --name basic-cluster
docker ps -a --filter "name=basic-cluster"
```

### Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `kubectl: command not found` | kubectl not installed | `sudo apt install kubectl` |
| `The connection to the server localhost:8080 was refused` | No cluster / wrong context | `kind create cluster --config kind-config.yml` then `kubectl config use-context kind-basic-cluster` |
| `kind create cluster` fails | Docker not running / inotify limits | Start Docker; raise inotify: `sudo sysctl -w fs.inotify.max_user_watches=524288` |
| `No nodes found` | Cluster not created | `kind get clusters`; `kind create cluster --name basic-cluster` |
| `Kubelet stopped posting node status` | Kind control-plane container issue | `docker exec basic-cluster-control-plane systemctl status kubelet`; `docker exec -it basic-cluster-control-plane crictl ps` |

### Verify kind is working
```bash
kubectl cluster-info
kubectl get nodes
kubectl config current-context
# Should show: kind-basic-cluster
```

---

## 2. kubectl Basic Operations (what you ran)

```bash
kubectl run nginx --image=nginx
kubectl get pods
kubectl get pods -o wide
kubectl get pods -w
kubectl delete pod nginx-<hash>
kubectl create deployment nginx --image=nginx --replicas=2
kubectl create deployment nginx --image=nginx --replicas=2 --port=5678
kubectl delete deployments.apps nginx
kubectl describe pod nginx-<hash>
kubectl explain deployment.spec.template
kubectl explain deployment.spec.selector
kubectl api-resources | head -40
kubectl config view
kubectl config get-contexts
kubectl config get-clusters
```

### Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `Error from server (NotFound): pods "nginx" not found` | Pod name wrong / deleted | `kubectl get pods` to see actual name |
| `deployment.apps "nginx" not found` | Deployment doesn't exist | `kubectl create deployment nginx --image=nginx` first |
| `kubectl explain` returns nothing | Wrong field path | Use `kubectl explain deployment --recursive` to find valid paths |
| `Pod stuck in Pending` | No node / resources | `kubectl describe pod <pod>`; check `kubectl get nodes` |

---

## 3. Namespace & Pod Operations in `nginx` Namespace (what you ran)

```bash
mkdir nginx
cd nginx/
vim namespace.yml
kubectl apply -f namespace.yml
kubectl get ns
kubectl get pods -n nginx
vim pod.yml
kubectl apply -f pod.yml
kubectl get pod -n nginx
kubectl exec -it pod/nginx-pod -n nginx -- bash
kubectl describe pod -n nginx
kubectl delete -f pod.yml
```

### Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `namespace "nginx" not found` | `namespace.yml` not applied | `kubectl apply -f namespace.yml` first |
| `Error from server (NotFound): pods "nginx-pod" not found` | Pod not created or wrong namespace | `kubectl get pods -n nginx`; apply `pod.yml` |
| `kubectl exec` fails | Pod not running / no shell | Ensure pod is `Running`; try `-- sh` if `bash` missing |
| `kubectl get pods -n nginx` empty | Wrong namespace | `kubectl get ns` to confirm; `kubectl get pods --all-namespaces` |

---

## 4. Deployment & Scaling (what you ran)

```bash
vim deployment.yml
kubectl apply -f deployment.yml
kubectl get deployment -n nginx
kubectl get pods -n nginx
kubectl scale deployment/nginx-deployment -n nginx --replicas=5
kubectl scale deployment/nginx-deployment -n nginx --replicas=2
kubectl scale deployment/nginx-deployment -n nginx --replicas=1
```

### Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `deployment.apps "nginx-deployment" not found` | Deployment not created | `kubectl apply -f deployment.yml` |
| `Replicas not changing` | Scale command failed | Check `kubectl describe deployment nginx-deployment -n nginx` for errors |
| `Pods not scaling up` | Resource limits / node capacity | `kubectl describe pod <pod> -n nginx`; check events |
| `ImagePullBackOff` | Image not available | Confirm image exists; for private repo, `docker login` or imagePullSecrets |

---

## 5. CronJob Operations (what you ran)

```bash
cat cron-job.yml
vim cron-job.yml
rm cron-job.yml
kubectl apply -f cron-job.yml
kubectl get pods -n nginx -w
kubectl exec -it -n nginx minute-backup-<hash> -- sh
kubectl exec -n nginx minute-backup-<hash> -- ls
```

### Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `cronjob.batch "minute-backup" not found` | CronJob not applied | `kubectl apply -f cron-job.yml` |
| `CronJob not running` | Schedule not reached / no schedule | Check `kubectl describe cronjob minute-backup -n nginx`; verify `schedule` field |
| `exec: sh: not found` | Container lacks shell | Try `-- bash` or check container image |
| `Job never completes` | Pod stuck | `kubectl get jobs -n nginx`; `kubectl describe job minute-backup -n nginx` |

---

## 6. PersistentVolume (what you ran)

```bash
kubectl apply -f persistentVolume.yml
```

### Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `persistentvolumes "pv" not found` | PV not created | `kubectl apply -f persistentVolume.yml` |
| `PV stuck in Pending` | No matching PVC / storage class | `kubectl describe pv <pv-name>`; ensure PVC exists and matches |
| `VolumeBindingFailed` | No storage class / node affinity | Check storage class; ensure PVC requests match PV capacity |

---

## 7. devops-todo-app K8s Manifests (files you copied into `k8s/`)

Files in `k8s/`:
- `namespace.yml`
- `nginx-config.yml` (ConfigMap)
- `nginx-deployment.yml`
- `nginx-service.yml`
- `deployment.yml`
- `service.yml`
- `ingress.yml`

### Apply order (important)
```bash
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/nginx-config.yml
kubectl apply -f k8s/nginx-deployment.yml
kubectl apply -f k8s/nginx-service.yml
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/ingress.yml

# Or all at once (after namespace exists)
kubectl apply -f k8s/
```

### What you did with nginx files
```bash
cd nginx/
mv deployment.yml nginx-deployment.yml
mv service.yml nginx-service.yml
cp nginx-deployment.yml nginx-service.yml /home/pratik/data/K8s/K8s-agentic-tws/devops-todo-app/k8s
```

### Known Bugs in the K8s Manifests

**Bug 1 — Port mismatch (`k8s/deployment.yml`)**
```yaml
# Line 26: containerPort: 80
# But Flask app runs on port 5000; service targets port 5000
```
**Fix:** Change `containerPort: 80` → `containerPort: 5000`.

**Bug 2 — Nginx config path typo (`k8s/nginx-config.yml`)**
```yaml
# Line 19: root /usr/share/nginx/.html;
# Extra dot causes 404
```
**Fix:** Change `/usr/share/nginx/.html` → `/usr/share/nginx/html`.

**Bug 3 — Image tag missing (`k8s/deployment.yml`)**
```yaml
# Line 24: image: pratik140404/devops-todo-app
# No tag → defaults to :latest
```
**Fix:** Pin a tag: `image: pratik140404/devops-todo-app:latest`.

**Bug 4 — ConfigMap dependency order**
`nginx-deployment.yml` mounts `nginx-config` ConfigMap. Apply `nginx-config.yml` BEFORE `nginx-deployment.yml`, otherwise pod stays in `ContainerCreating`.

**Bug 5 — Ingress class**
`ingress.yml` uses `ingressClassName: nginx`. Requires NGINX Ingress Controller installed:
```bash
helm install ingress-nginx ingress-nginx/ingress-nginx
```

---

## 8. Verification Commands

```bash
kubectl get all -n todo-app
kubectl get all -n nginx
kubectl get pods -n todo-app -o wide
kubectl get svc -n todo-app
kubectl get ingress -n todo-app
kubectl describe pod <pod-name> -n todo-app
kubectl logs <pod-name> -n todo-app
kubectl logs <pod-name> -n todo-app --previous
kubectl exec -it <pod-name> -n todo-app -- sh
kubectl describe ingress nginx-todo-ingress -n todo-app
kubectl get events -n todo-app --sort-by='.lastTimestamp'
```

### Quick health checks
```bash
curl http://localhost:5000/health          # local Flask
curl http://localhost:80                   # via nginx / ingress
ss -tlnp | grep 5000                       # port 5000 listener
ss -tlnp | grep 80                         # port 80 listener
```

---

## 9. Common Error Messages & Fixes (K8s-specific)

| Error | Meaning | Fix |
|-------|---------|-----|
| `ImagePullBackOff` | K8s can't pull image | Push image to Docker Hub; check image name/tag; ensure `docker login` on cluster nodes |
| `CrashLoopBackOff` | Container keeps crashing | `kubectl logs <pod>`; fix app error; check env vars / port |
| `ContainerCreating` | ConfigMap/secret missing | Apply `nginx-config.yml` before `nginx-deployment.yml` |
| `namespace not found` | Namespace missing | Apply `namespace.yml` first |
| `Ingress class "nginx" not found` | NGINX IC not installed | Install NGINX Ingress Controller |
| `404 on /nginx` | Nginx root path typo | Fix `/usr/share/nginx/.html` → `/usr/share/nginx/html` |
| `502 Bad Gateway` | Nginx can't reach backend | Backend not on expected port; fix `containerPort` to 5000 |
| `pod has unbound immediate PersistentVolumeClaims` | No PV available | `kubectl apply -f persistentVolume.yml`; check storage class |

---

**Files referenced:** `k8s/namespace.yml`, `k8s/nginx-config.yml`, `k8s/nginx-deployment.yml`, `k8s/nginx-service.yml`, `k8s/deployment.yml`, `k8s/service.yml`, `k8s/ingress.yml`
