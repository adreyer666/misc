FROM debian:bullseye-slim

LABEL maintainer="Achim Dreyer <ml10625@adreyer.com>" \
      org.label-schema.name="Radicale 3 Docker Image" \
      org.label-schema.description="Docker image for Radicale 3, the CalDAV/CardDAV server" \
      org.label-schema.url="https://github.com/Kozea/Radicale" \
      org.label-schema.vcs-url="https://github.com/adreyer666/CalSrv" \
      org.label-schema.schema-version="1.0"

# install just enough system
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -q -y --no-install-recommends \
	bash git curl ca-certificates vim-tiny psmisc less
# RUN apt-get upgrade -q -y

RUN apt-get install -q -y --no-install-recommends \
	tzdata apache2-utils python3 python3-pip
RUN python3 -m pip install --upgrade radicale passlib[bcrypt] pytz
RUN python3 -m pip install --upgrade https://github.com/Unrud/RadicaleInfCloud/archive/master.tar.gz

RUN mkdir -p /data/store /data/log /config \
    && ln -s /data/store /var/lib/radicale \
    && ln -s /data/log /var/log/radicale \
    && ln -s /config /etc/radicale \
    && mkdir -p /var/lib/radicale/collection-root \
    && chmod -R o= /var/lib/radicale/collection-root \
    && mkdir -p /root/.config/radicale \
    && touch /root/.config/radicale/config

HEALTHCHECK --interval=30s --retries=3 CMD curl --fail https://localhost:5232 || exit 1
VOLUME /config /data
EXPOSE 5232
COPY run.sh /usr/local/bin

ENTRYPOINT ["/usr/local/bin/run.sh"]
CMD ["radicale"]

