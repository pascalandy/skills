FROM python:3.12.7-slim

WORKDIR /app
COPY pantry/ pantry/

# The deploy mounts the pool's config here.
ENV PANTRY_CONFIG=/etc/pantry/config.toml
EXPOSE 8080
USER nobody
CMD ["python", "-m", "pantry.server"]
