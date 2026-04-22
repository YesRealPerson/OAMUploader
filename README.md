# OAM Uploader

Updated imagery uploader that integrates with the modernized backend, replacing the current uploader which is unreliable for large files and lacks modern resilience features.

# Development
```

```

# K8s
## Running
Start minikube
```
minikube start
```

Point docker commands to minikube

```
minikube -p minikube docker-env --shell powershell | Invoke-Expression
```

Install Argo Workflows
```
kubectl create namespace argo
kubectl apply --server-side -n argo -f "https://github.com/argoproj/argo-workflows/releases/download/v4.0.4/quick-start-minimal.yaml"
```
This uses the quick start commands which should be changed later.

Build production containers (cd into the public directory)
```
docker build -t oam-uploader-front:latest -f Dockerfile . 
```

Apply deployment and service
```
kubectl apply -f ./k8s/public.yaml
```

Port forward service
```
kubectl port-forward svc/oam-front-service 12345:12345
```

Open the following in your browser
http://127.0.0.1:12345/

## Useful commands

Get pods and services
```
kubectl get pods
kubectl get services
```

Delete all pods/services
```
kubectl delete all --all     # kills all pods & services
```

View logs of pod
```
kubectl logs [pod name]
```

SSH into pod
```
kubectl exec -it [pod_name] -- /bin/bash
```