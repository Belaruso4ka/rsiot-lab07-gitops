# syntax=docker/dockerfile:1

FROM python:3.12-alpine AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-alpine
ARG APP_VERSION=dev
LABEL org.opencontainers.image.source="https://github.com/Belaruso4ka/rsiot-lab07-gitops" \
      org.bstu.course="RSIOT" \
      org.bstu.student.id="230233" \
      org.bstu.variant="44" \
      org.bstu.slug="230233-v44"
ENV PYTHONUNBUFFERED=1 \
    PORT=8124 \
    APP_VERSION=${APP_VERSION}
WORKDIR /app
COPY --from=build /install /usr/local
COPY main.py .
USER 10001:10001
EXPOSE 8124
CMD ["python", "main.py"]
