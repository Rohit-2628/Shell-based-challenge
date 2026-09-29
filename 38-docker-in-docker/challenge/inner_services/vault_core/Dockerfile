FROM python:3.11-alpine

WORKDIR /app
COPY app.py /app/app.py

ENV PORT=8443
ENV PYTHONUNBUFFERED=1

EXPOSE 8443

ENTRYPOINT ["python3", "/app/app.py"]
