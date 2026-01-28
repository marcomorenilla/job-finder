FROM alpine:latest AS builder
RUN apk update &&\
apk add python3 &&\
apk add py3-pip &&\
apk add py3-uv &&\
apk add chromium &&\
apk add chromium-chromedriver
WORKDIR /app
COPY requirements.txt .
COPY main.py .
RUN uv venv &&\
uv pip install -r requirements.txt
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT [ "python", "main.py" ]
