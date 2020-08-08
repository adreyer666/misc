#!/usr/bin/env make

BUILD = default

  DIR := $(shell pwd)
IMAGE := $(shell basename $(DIR))

build: Makefile Dockerfile run.sh
	buildah bud -f Dockerfile -t $(IMAGE)

run:
	podman run --rm -d --name radicale \
	    -p 127.0.0.1:5232:5232 \
	    --read-only \
	    --init \
	    --cap-drop ALL \
	    --cap-add CHOWN \
	    --cap-add SETUID \
	    --cap-add SETGID \
	    --cap-add KILL \
	    --health-cmd="curl --fail https://localhost:5232 || exit 1" \
	    --health-interval=30s \
	    --health-retries=3 \
	    -v `pwd`/data:/data \
	    -v `pwd`/config:/config:ro \
	    $(IMAGE)
	    #--security-opt="no-new-privileges:true" \
	    #--memory 256M \
	    #--pids-limit 50 \

stop:
	set -x; \
	  CTR=`podman ps -a --format "{{.ID}}  {{.Image}}" | grep $(IMAGE) | cut -d\  -f1`; \
	  test "$$CTR" = "" || podman stop $${CTR}; \
	  sleep 3; \
	  test "$$CTR" = "" || podman container rm $${CTR}

clean: stop
	podman image rm localhost/$(IMAGE)

