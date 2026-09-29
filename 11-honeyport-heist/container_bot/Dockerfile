FROM python:3.9-slim
COPY start_bots.py /opt/start_bots.py
RUN apt-get update && apt-get install -y curl
ENTRYPOINT ["python3", "/opt/start_bots.py"]
