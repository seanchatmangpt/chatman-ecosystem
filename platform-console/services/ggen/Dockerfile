FROM python:3.12-slim

WORKDIR /app

# facts.json and ggen-bin must already exist -- produced by ./prep.sh against the real,
# live project checkout (and its real compiled `ggen` binary) BEFORE `docker build` runs.
# The container itself never has access to the host repos.
COPY facts.json /app/facts.json
COPY ggen-bin /usr/local/bin/ggen
COPY app.py /app/app.py

RUN chmod +x /usr/local/bin/ggen \
    && mkdir -p /app/state/runs /app/state/keys \
    && chown -R nobody:nogroup /app/state

ENV FACTS_PATH=/app/facts.json
ENV GGEN_BIN=/usr/local/bin/ggen
ENV WORKSPACE_ROOT=/app/state/runs
ENV SIGNING_KEY_PATH=/app/state/keys/signing.key
ENV PORT=8080
EXPOSE 8080

USER nobody

CMD ["python3", "/app/app.py"]
