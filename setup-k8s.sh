#!/bin/bash
set -e

echo "========================================="
echo "K8s Kind Setup — DevOps Todo App"
echo "========================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
K8S_DIR="$REPO_DIR/k8s"

CLUSTER_NAME="basic-cluster"

log "Repo dir: $REPO_DIR"
log "K8s dir: $K8S_DIR"

if [ ! -d "$K8S_DIR" ]; then
    err "k8s directory not found at $K8S_DIR"
fi

for f in namespace.yml nginx-config.yml nginx-deployment.yml nginx-service.yml deployment.yml service.yml ingress.yml; do
    if [ ! -f "$K8S_DIR/$f" ]; then
        err "Missing required file: $K8S_DIR/$f"
    fi
done

command -v curl >/dev/null 2>&1 || err "curl is required but not installed."
command -v sudo >/dev/null 2>&1 || err "sudo is required but not installed."

if ! command -v kubectl >/dev/null 2>&1; then
    log "Installing kubectl..."
    sudo apt-get update -y
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
    sudo apt-get update -y
    sudo apt-get install -y kubectl
else
    log "kubectl already installed: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
fi

if ! command -v kind >/dev/null 2>&1; then
    log "Installing kind..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
else
    log "kind already installed: $(kind version)"
fi

if kind get clusters | grep -qw "$CLUSTER_NAME"; then
    warn "Kind cluster '$CLUSTER_NAME' already exists. Skipping creation."
else
    log "Creating kind cluster '$CLUSTER_NAME'..."
    kind create cluster --name "$CLUSTER_NAME"
fi

kubectl config use-context "kind-$CLUSTER_NAME"
kubectl cluster-info
kubectl get nodes

log "Installing NGINX Ingress Controller (static manifest, no Helm)..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

log "Waiting for ingress controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s

kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx

log "Applying k8s manifests in order..."
kubectl apply -f "$K8S_DIR/namespace.yml"
kubectl apply -f "$K8S_DIR/nginx-config.yml"
kubectl apply -f "$K8S_DIR/nginx-deployment.yml"
kubectl apply -f "$K8S_DIR/nginx-service.yml"
kubectl apply -f "$K8S_DIR/deployment.yml"
kubectl apply -f "$K8S_DIR/service.yml"
kubectl apply -f "$K8S_DIR/ingress.yml"

log "Verification:"
kubectl get all -n todo-app
kubectl get ingress -n todo-app

log "========================================="
log "Setup complete!"
log "========================================="
log ""
log "Access app:"
log "  kubectl port-forward svc/ingress-nginx-controller -n ingress-nginx 8080:80"
log "  curl http://localhost:8080/health"
log ""
log "Logs:"
log "  kubectl logs -l app=todo-app -n todo-app"
log ""
log "Known issues in existing manifests (not edited):"
log "  - k8s/deployment.yml: containerPort: 80 (Flask runs on 5000)"
log "  - k8s/nginx-config.yml: path typo /usr/share/nginx/.html"
log "  - k8s/deployment.yml: no image tag (defaults to :latest)"
log ""
