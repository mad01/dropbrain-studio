---
title: "Docker alpine smaller image footprint"
date: 2016-07-20
slug: docker-apline-image-size-improvments
description: "Working with docker images to minimise the footprint i.e the size if a image. There is a few things that you can do to get smaller images. I will show some examples for a small go…"
tags: docker, python, python3, alpine, linux, golang, go
---
Working with docker images to minimise the footprint i.e the size if a image. There is a few things that you can do to get smaller images. I will show some examples for a small go and python3 service built in a Debian and alpine linux based image to compare the result and the footprint that a image. 

The key to building small docker images is only use `one` `RUN` step in the Dockerfile. Why you might think. Every RUN in docker is a layer. The layer will contain what you do in that layer like adding package cache. If you then remove the cache in a later RUN you will still have it in the parent layers. So what you do is use al lot of `&&` in the same RUN and in the end remove the files and cache you don't need. Selecting the base image will affect you the most when it comes to footprint. I will look on Debian and alpine based images. 

I will use the python official images as a reference like `python:3.5` that is based on jessie with a size of `694 MB`, and the Alpine Linux version `python:3.5-alpine` with a size of `73 MB` .

One of Alpines key features i see other then the base size of `4.8 MB` , is `virtual package` it lets you assign packages to one or multiple virtual packages. When you are done just remove the virtual package.

The reference app is a small rest service returning status 200 with a body containing json `{"status": "OK"}` for both python and go.

Lets start with creating a image based on the `python:3.5` image with a starting size of `694 MB`, after build the result is `702.5 MB`
```dockerfile
FROM python:3.5

# adding code
WORKDIR /app/pikachu
ADD requirements.txt /app/pikachu

# install
RUN pip install -r requirements.txt

ADD . /app/pikachu

EXPOSE 8080
ENTRYPOINT gunicorn --bind 0.0.0.0:8080 pikachu.app:api
```


If we do the same but now use the `python:3.5-alpine` image with a starting size of `73 MB` after build the result is `82 MB` . Just using the alpine base you will have saved `612 MB` 
```dockerfile
FROM python:3.5-alpine

# adding code
WORKDIR /app/pikachu
ADD requirements.txt /app/pikachu

# install
RUN apk add --update openssl \
    && apk --update add --no-cache --virtual build-dependencies libc-dev autoconf gcc \
    && pip install --no-cache-dir -r requirements.txt \
    \ 
    && rm -rf ~/.cache \
    && apk del build-dependencies

ADD . /app/pikachu

EXPOSE 8080
ENTRYPOINT gunicorn --bind 0.0.0.0:8080 pikachu.app:api
```

For go we will use 3 base images, Debian, alpine, and scratch. We need to compile go with it's deps. The resulting file will be about `11 MB`
```bash
$ CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .
```

Lets start with a creating a image based on the `debian:8` image with a starting size of `125 MB`, after build the result is `136 MB`
```dockerfile
FROM debian:8
ADD main /
CMD ["/main"]
```


If we do the same but now use the `alpine:3.4` image with a starting size of `4.8 MB` after build the result is `16.1 MB`
```dockerfile
FROM alpine:3.4
ADD main /
CMD ["/main"]
```


If we now take a look on the scratch base image we have `0 MB` as a starting point and the result should be about `11 MB`
```dockerfile
FROM alpine:3.4
ADD main /
CMD ["/main"]
```


The conclusion is that if you need to get small images base it on `alpine` and use the official alpine images that most project like python, java have official version of. 



A note here is that most of the official images now have a alpine option
The examples can be found here. [Source](https://github.com/mad01/examples/tree/master/alpine)
