FROM debian:bullseye-slim

ARG COMMIT_ID
ENV COMMIT_ID ${COMMIT_ID}

ARG VERSION
ENV VERSION ${VERSION:-0.0.1}

ARG UID
ENV UID ${UID:-5232}

ARG BUILD_GID
ENV BUILD_GID ${BUILD_GID:-5232}

LABEL maintainer="Achim Dreyer <ml10625@adreyer.com>" \
      org.label-schema.name="Radicale Docker Image" \
      org.label-schema.description="Enhanced Docker image for Radicale, the CalDAV/CardDAV server" \
      org.label-schema.url="https://github.com/Kozea/Radicale" \
      org.label-schema.version=$VERSION \
      org.label-schema.vcs-ref=$COMMIT_ID \
      org.label-schema.vcs-url="https://github.com/adreyer666/CalSrv" \
      org.label-schema.schema-version="1.0"


ARG DEBIAN_FRONTEND=noninteractive

# install just enough system
RUN apt-get update \
    && apt-get install -q -y --no-install-recommends \
	bash git curl ca-certificates vim-tiny psmisc
# RUN apt-get upgrade -q -y


RUN apt-get install -q -y --no-install-recommends \
	tzdata wget apache2-utils python3 python3-pip
RUN python3 -m pip install --upgrade radicale passlib[bcrypt]

RUN mkdir -p /data/store /data/log /config \
    && ln -s /data/store /var/lib/radicale \
    && ln -s /data/log /var/log/radicale \
    && ln -s /config /etc/radicale \
    && mkdir -p /var/lib/radicale/collections \
    && chmod -R o= /var/lib/radicale/collections

HEALTHCHECK --interval=30s --retries=3 CMD curl --fail https://localhost:5232 || exit 1
VOLUME /config /data
EXPOSE 5232
COPY run.sh /usr/local/bin

ENTRYPOINT ["/usr/local/bin/run.sh"]
CMD ["radicale"]

