ARG BUILD_FROM=ghcr.io/home-assistant/base:3.22
FROM ${BUILD_FROM}

RUN apk add --no-cache nginx gettext-envsubst \
    && mkdir -p /run/nginx

COPY rootfs /
RUN chmod +x /etc/services.d/nginx/run
