# Pipeline setup

1. Point docker to minikube
2. Build images

```
docker build -t convert:dev ./pipeline/convert
docker build -t metadata:dev ./pipeline/metadata
docker build -t validate:dev ./pipeline/validate
```

3. Upload imagery using uploader
4. Test Argo Workflow

```
argo submit -n argo --watch \
    --parameter s3-path="s3://testbucket/{userid}/{title}/raw.tif" \
    ./k8s/pipeline.yaml
```