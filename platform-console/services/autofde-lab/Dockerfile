FROM python:3.12-slim

WORKDIR /app

# facts.json must already exist -- produced by ./prep.sh against the real,
# live project checkout BEFORE `docker build` runs. The container itself
# never has access to the host repos.
COPY facts.json /app/facts.json
COPY app.py /app/app.py

ENV FACTS_PATH=/app/facts.json
ENV PORT=8080
# Defaults matching platform-feature-flags exactly (see app.py's module
# docstring) -- overridable, but the Deployment manifest sets them
# explicitly too, so this is redundant with services-and-deployments.yaml
# by design, same convention as FACTS_PATH/PORT above.
ENV FEATURE_FLAGS_NAMESPACE=platform-console
ENV FEATURE_FLAGS_CONFIGMAP=platform-feature-flags
EXPOSE 8080

USER nobody

CMD ["python3", "/app/app.py"]
