# Pipeline setup

1. Point docker to minikube

```
minikube -p minikube docker-env --shell powershell | Invoke-Expression
```


2. Build images

```
docker build -t convert:wacko ./pipeline/convert --no-cache
docker build -t metadata:next ./pipeline/metadata 
docker build -t validate:next ./pipeline/validate 
docker build -t stac:next ./pipeline/stac 

minikube image load convert:next
minikube image load metadata:next
minikube image load validate:next
minikube image load stac:next
```

3. Create template

```
argo template delete --all -n argo
argo template create ./k8s/pipeline.yaml -n argo
```

NOTE:
To process large files please reserve ~2-4x the size of the largest expected file.

Example:
```
minikube start --cpus 6 --memory 12288 --disk-size 80g
```

TODO: More verbose failure messages