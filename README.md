# OAM Uploader

Updated imagery uploader that integrates with the modernized backend, replacing the current uploader which is unreliable for large files and lacks modern resilience features.

# Development
```
docker compose up --build -d
docker compose down
```

# TODO
 - Setup workflows

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

Build production containers
```
docker build -t oam-uploader-public:latest -f public/Dockerfile . 
docker build -t oam-uploader-private:latest -f private/Dockerfile . 
```

Apply deployments and services

```
kubectl apply -f ./k8s/pv.yaml
kubectl apply -f ./k8s/pvc.yaml
kubectl apply -f ./k8s/private-deployment.yaml
kubectl apply -f ./k8s/public-deployment.yaml
kubectl apply -f ./k8s/private-service.yaml
kubectl apply -f ./k8s/public-service.yaml
```

Get URL for viewing
```
minikube service public-service --url    # for public
minikube service private-service --url   # for private
```

## Useful commands

Get pods and services
```
kubectl get pods
kubectl get services
```

Delete all pods/services
```
kubectl delete pv temp-pv    # kills persistent volume
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