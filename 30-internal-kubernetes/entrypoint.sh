#!/bin/bash
set -e

# Default synthetic flag if not injected dynamically
DEFAULT_FLAG="YUVA{k8s_rb4c_s3rv1c3_4cc0unt_3x3c_p1v0t_9d82e1}"
CHALLENGE_FLAG="${FLAG:-$DEFAULT_FLAG}"

echo "[+] Initializing D30 — Internal Kubernetes Challenge Environment..."

# 1. Store flag in isolated defense controller storage
mkdir -p /opt/orbital-defense
echo "$CHALLENGE_FLAG" > /opt/orbital-defense/flag.txt

chown -R defense-pod:defense-pod /opt/orbital-defense
chmod 700 /opt/orbital-defense
chmod 600 /opt/orbital-defense/flag.txt

# 2. Generate Mock Kubernetes TLS certificate & CA
mkdir -p /etc/kubernetes/pki /tmp/k8s_mock
if [ ! -f /etc/kubernetes/pki/ca.crt ]; then
    openssl req -x509 -newkey rsa:2048 -nodes \
        -keyout /etc/kubernetes/pki/k8s_mock.key \
        -out /etc/kubernetes/pki/ca.crt \
        -days 365 \
        -subj "/CN=kubernetes.default.svc.cluster.local/O=Latveria-K8s-Mock" >/dev/null 2>&1
fi

chmod 644 /etc/kubernetes/pki/ca.crt
chmod 600 /etc/kubernetes/pki/k8s_mock.key
chown -R k8s-api:k8s-api /etc/kubernetes/pki

# 3. Mount Synthetic Service Account Token for Pod Identity
mkdir -p /var/run/secrets/kubernetes.io/serviceaccount
echo "latv_k8s_sa_sentinel_tok_9948270182749102" > /var/run/secrets/kubernetes.io/serviceaccount/token
echo "telemetry-system" > /var/run/secrets/kubernetes.io/serviceaccount/namespace
cp /etc/kubernetes/pki/ca.crt /var/run/secrets/kubernetes.io/serviceaccount/ca.crt

chmod 755 /var/run/secrets/kubernetes.io/serviceaccount
chmod 644 /var/run/secrets/kubernetes.io/serviceaccount/*

# 4. Set In-Cluster Kubernetes Environment Variables
export KUBERNETES_SERVICE_HOST=127.0.0.1
export KUBERNETES_SERVICE_PORT=6443

# Configure kubectl kubeconfig for in-cluster access if kubectl is present
mkdir -p /home/sentinel/.kube /root/.kube
cat <<EOF > /home/sentinel/.kube/config
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    server: https://127.0.0.1:6443
  name: latveria-cluster
contexts:
- context:
    cluster: latveria-cluster
    namespace: telemetry-system
    user: telemetry-sentinel
  name: default
current-context: default
users:
- name: telemetry-sentinel
  user:
    token: latv_k8s_sa_sentinel_tok_9948270182749102
EOF

cp /home/sentinel/.kube/config /root/.kube/config
chown -R sentinel:sentinel /home/sentinel/.kube
chmod 600 /home/sentinel/.kube/config

# 5. Start Mock Kubernetes API Server daemon
echo "[+] Starting Mock Kubernetes API Server (127.0.0.1:6443)..."
su -s /bin/bash k8s-api -c "
    export FLAG_PATH=/opt/orbital-defense/flag.txt
    export K8S_MOCK_HOST=127.0.0.1
    export K8S_MOCK_PORT=6443
    export K8S_CERT_PATH=/etc/kubernetes/pki/ca.crt
    export K8S_KEY_PATH=/etc/kubernetes/pki/k8s_mock.key
    export K8S_USE_TLS=true
    python3 /challenge/k8s_api/mock_k8s_server.py
" > /var/log/k8s-mock-api.log 2>&1 &

sleep 1

# 6. Start Fleet Sentinel Web Application
echo "[+] Starting Fleet Sentinel Web Gateway (127.0.0.1:8000)..."
su -s /bin/bash sentinel -c "
    export APP_HOST=127.0.0.1
    export APP_PORT=8000
    export KUBERNETES_SERVICE_HOST=127.0.0.1
    export KUBERNETES_SERVICE_PORT=6443
    python3 /challenge/app/server.py
" > /var/log/sentinel-app.log 2>&1 &

sleep 1

# 7. Start Nginx Ingress Gateway on Port 80
echo "[+] Starting Nginx Ingress Gateway (TCP/80)..."
nginx

echo "[+] D30 — Internal Kubernetes Challenge Ready on TCP/80."

# Supervisor Loop
trap "echo 'Shutting down...'; nginx -s stop; kill 0; exit 0" SIGINT SIGTERM
tail -f /var/log/sentinel-app.log /var/log/k8s-mock-api.log
