FROM python:3.9-slim

# Create non-root user
RUN groupadd -r kitsu && useradd -r -g kitsu kitsu

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY kitsu_ingest/ /app/kitsu_ingest/
COPY pyproject.toml /app/
COPY .env /app/

RUN pip install --no-cache-dir .

RUN mkdir -p /app/kitsu_ingest/processed && chmod 777 /app/kitsu_ingest/processed

# Make the Python module available as a command
RUN echo '#!/bin/bash\npython -m kitsu_ingest "$@"' > /usr/local/bin/kitsu-ingest && \
    chmod +x /usr/local/bin/kitsu-ingest

USER kitsu

VOLUME ["/app/kitsu_ingest/processed"]

CMD ["/bin/bash"]