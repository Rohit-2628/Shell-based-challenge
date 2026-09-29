FROM ubuntu:22.04
RUN apt-get update && apt-get install -y iputils-ping && apt-get clean
COPY watcher.sh /watcher.sh
RUN chmod 700 /watcher.sh
ENTRYPOINT ["/watcher.sh"]
