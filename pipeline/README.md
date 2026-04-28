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
docker build -t stac:dev ./pipeline/stac
```

3. Upload template

```
argo template create ./k8s/pipeline.yaml -n argo
```

TODO: More verbose failure messages