FROM alpine:3.18

RUN apk add --no-cache bash curl jq python3 py3-pip net-tools bind-tools iputils iproute2 nmap-ncat

LABEL maintainer="devops@latveria.mil" \
      service="vault-admin-toolkit" \
      version="1.0-release"

WORKDIR /root

CMD ["/bin/sh"]
