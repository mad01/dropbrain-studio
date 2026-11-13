---
title: "bulding a debian docker base build for a flask app"
date: 2015-04-03
slug: docker-basic-build
description: "Start by pulling down a debian base build. docker pull debian:8.0 .Creating a Dockerfile for a base build to a python flask app. based on debian 8"
tags: docker, debian
---
Start by pulling down a debian base build. `docker pull debian:8.0` .Creating a `Dockerfile` for a base build to a python flask app. based on debian 8

```dockerfile
FROM debian:8.0

RUN apt-get -y update \
	&& apt-get upgrade -y \
	&& apt-get install -y \
		python-setuptools \
		python-pip

RUN pip install flask \
				flask-restful \
				pymongo

```

build the docker base image. the `-t` gives the build a name, the `--rm=true` means "Remove intermediate containers after a successful build", the `--no-cache=false` means "Do not use cache when building the image". the dot means look for the `Dockerfile` in the current folder. using the flags together means that all of the steps in the docker build is done every time since i want to make the full docker build. Not just from a commit a few steps in to the build. 

```bash
docker build -t foobar --rm=true --no-cache=false .
```



build the flask app docker image based on the base docker build foobar. 
```dockerfile
FROM foobar

RUN mkdir -p /opt/app
COPY app* /opt/app

WORKDIR /opt/app/
ENTRYPOINT ["python", "api.py"]
```


building the api docker image. the assumption is that there is a folder named app in the same folder as the `Dockerfile`. This folder contains the api and the support modules and files needed for the api. 'COPY app* /opt/app' will copy all files in the app folder and copy them to the /opt/app folder in the docker image. using the `WORKDIR` and `ENTRYPOINT` makes the docker image start the api on start of the image. 

```bash
docker build -t api --rm=true --no-cache=false .
```


Now you can start the docker image named api and the api will be started when the docker image is started. 

```bash
docker run -i api
```
