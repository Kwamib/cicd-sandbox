FROM python:3.13-slim
WORKDIR /srv
COPY app/ app/
ENTRYPOINT ["python", "-m", "app"]
