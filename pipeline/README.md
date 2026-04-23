# Pipeline setup

1. Point docker to minikube

```
minikube -p minikube docker-env --shell powershell | Invoke-Expression
```


2. Build images

```
docker build -t convert:dev ./pipeline/convert
docker build -t metadata:dev ./pipeline/metadata
docker build -t validate:dev ./pipeline/validate
```

3. Upload template

```
argo template create pipeline.yaml -n argo
```

Retain original filename for raw file
Add failure messages back to the user