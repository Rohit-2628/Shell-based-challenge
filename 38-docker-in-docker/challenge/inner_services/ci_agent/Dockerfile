FROM alpine:3.18

RUN apk add --no-cache bash curl jq procps coreutils

WORKDIR /workspace

RUN mkdir -p /var/log/pipeline /var/run/latveria/deploy-config

COPY last_deploy.log /var/log/pipeline/deploy.log
COPY last_deploy.log /var/log/pipeline/last_deploy.log

CMD ["sh", "-c", "echo '[*] CI Pipeline Worker Active (Agent v3.2)' && tail -f /var/log/pipeline/last_deploy.log"]
