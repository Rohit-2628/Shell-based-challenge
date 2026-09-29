FROM python:3.11-alpine

WORKDIR /app
COPY app.py /app/app.py

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

ENTRYPOINT ["python3", "/app/app.py"]
