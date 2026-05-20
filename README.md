# OAM Uploader

Updated imagery uploader that integrates with the modernized backend, replacing the current uploader which is unreliable for large files and lacks modern resilience features.

Note that testing was done on a Windows machine and all commands below are under the assumption of Windows powershell.

# Requirements
- Docker
- Minikube (or similar)
- Argo Workflows
- Localstack (AWS)
- Local <a href="https://docs.imagery.hotosm.org/dev/local-setup/">OpenAerialMap</a>
- Python 3.14

Argo quickstart
```
kubectl create namespace argo
kubectl apply --server-side -n argo -f "https://github.com/argoproj/argo-workflows/releases/download/v4.0.4/quick-start-minimal.yaml"
```

Make sure to download all required packages through pip. The `requirements.txt` in the root folder is for running any potential script in this repo (i.e. including the pipeline steps). There is another in the public folder which holds only the requirements for running the FastAPI front end servers.

# Components

### ./k8s
Kubernetes manifests
- `front.yaml` - Publicly exposed server
- `keys.yaml` - API keys and other secrets (see `keysstub.yaml`for a template).
- `pipeline.yaml` - Argo Workflows template for data processing
- `stac.yaml` - Helper stac server

### ./pipeline
Scripts and dockerfiles for each data processing step. Each folder should be relatively self explanatory.

Notably however, metadata regarding registration to pgStac is handled in the metadata step of the pipeline. Custom properties can be added under the properities parameter of the item.

### ./public
All files relating to the public API and uploader page.
- `front.py` - FastAPI server for the uploader page and related endpoints
- `stac.py` - FastAPI server for communicating with the pgStac database in OpenAerialMap
- `static` - Static web files

# Pipeline setup


1. Point docker to minikube

```
minikube -p minikube docker-env --shell powershell | Invoke-Expression
```


2. Build images

```
docker build -t convert:v1 ./pipeline/convert --no-cache
docker build -t metadata:v1 ./pipeline/metadata --no-cache
docker build -t validate:v1 ./pipeline/validate --no-cache
docker build -t stac:v1 ./pipeline/stac --no-cache
```

3. Create workflow template

```
argo template delete --all -n argo
argo template create ./k8s/pipeline.yaml -n argo
```

Note: Processing large files will require a lot of disk space, adjust your Minikube configuration appropriately. We found that our 5gb test file took up close to ~45gb oftotal storage space at once to process.

# Frontend Startup

If you're actively making changes to the front end start the server in uvicorn (or similar).

### Uvicorn
Open two terminals to `./public`
1. `uvicorn front:app --port 12345 --host 0.0.0.0 --reload`
2. `uvicorn stac:app --reload --port 8082 --host 0.0.0.0`

Open the following in your browser
http://127.0.0.1:12345/

Note: Ensure you've created a proper .env file. See stub.env for an example.

### Kubernetes

1. Point docker commands to minikube

```
minikube -p minikube docker-env --shell powershell | Invoke-Expression
```

2. Build production containers (cd into the public directory)
```
docker build -t oam-uploader-front:latest -f .\public\front.Dockerfile .
docker build -t oam-uploader-stac:latest -f .\public\stac.Dockerfile .
```

3. Apply kubernetes manifests
```
kubectl apply -f .\k8s\front.yaml
kubectl apply -f .\k8s\stac.yaml
kubectl apply -f .\k8s\keys.yaml 
```

Port forward front facing server
```
kubectl port-forward svc/oam-uploader-front 12345:12345
```

Open the following in your browser
http://127.0.0.1:12345/