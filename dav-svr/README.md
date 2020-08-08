# DavSvr

## Cal-/Card-CAD
Based on radicale 3 with InfCloud added on top..


## Build
```
make
```

## Run
```
make run
```

### run manually with a lot of parameters
```
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
    -v `pwd`/data:/data:rw \
    -v `pwd`/config:/config:ro \
    radicale
```

