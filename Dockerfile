FROM python:3.13-slim
RUN python -m pip uninstall -y pip
WORKDIR /srv
COPY app/ app/
ENTRYPOINT ["python", "-m", "app"]
