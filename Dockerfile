FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pillow colorama yt-dlp

COPY . ./
COPY fonts/ /app/fonts/

RUN chmod +x entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV MODE=update
ENV RUN_TIME=03:00
ENV TZ=Europe/Stockholm

ENTRYPOINT ["/app/entrypoint.sh"]
