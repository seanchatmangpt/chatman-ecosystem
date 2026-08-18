# Real sidecar for the real autofde-lab OpenClaw MCP bridge
# (autofde_lab.openclaw_bridge / autofde_lab.openclaw_runtime,
# autofde_lab.openclaw_http) -- this is NOT the services/autofde-lab
# facts.json stub. That stub serves build-time-baked repo metadata; this
# image runs the actual package's catalog()/execute() dispatch, imported
# and called for real on every request (see openclaw_http.py's module
# docstring).
#
# Only the base runtime dependency set `autofde_lab.__init__` actually
# imports at module load time is installed here -- NOT the full
# pyproject.toml dependency closure (domains/solvers extras pull in
# matplotlib/cartopy/pygrib/unified-planning/ray/etc., none of which
# `catalog()`/`describe()` touch; they matter only if a caller executes
# `run` against a domain that itself needs them, out of scope for this
# sidecar's read-only discovery surface). `gymact` is deliberately
# excluded too -- a real dependency of
# autofde_lab.hub.domain.azuregoat_privesc.gymact_bridge specifically,
# resolved from a local path (`[tool.uv.sources]`) that does not exist
# inside this image; importlib.metadata.entry_points() never imports it
# just to list its name.
#
# No `pip install -e .` here, deliberately: autofde-lab's real build
# backend (scikit-build-core, pyproject.toml's [build-system]) expects a
# `cpp/` CMake source tree (a real, ~2.3GB, vendored-SDK C++ project --
# `cpp.source-dir = "cpp"`, `ONLY_PYTHON = true` still requires CMake to
# configure against it) that is not part of this build context and is
# not needed here: `ONLY_PYTHON = true` means the wheel it produces is
# pure Python anyway, identical to what's already on disk at
# src/autofde_lab. Verified live (see the platform-console integration
# commit message): plain `PYTHONPATH=/app/src` import of
# `autofde_lab.openclaw_bridge` and a real `tools/list` call succeed with
# zero build step, so this image sets PYTHONPATH instead of building/
# installing a wheel.
#
# prep.sh (this directory) copies the real src/autofde_lab tree from the
# live ~/autofde-lab checkout at build time -- same "COPY real files in,
# no network access to the host repo at runtime" convention
# services/autofde-lab/Dockerfile already uses.
FROM python:3.13-slim

WORKDIR /app

# pynng's compiled `_nng` extension dynamically links libatomic, which
# python:3.13-slim's Debian base does not carry by default (verified live:
# `from pynng import Push0` raised `ImportError: libatomic.so.1: cannot
# open shared object file` without this).
RUN apt-get update && apt-get install -y --no-install-recommends libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# Real base runtime deps `import autofde_lab` actually needs (verified
# live: PYTHONPATH import + these five installed, then
# `python -m autofde_lab.openclaw_http` served real tools/list and
# tools/call responses).
RUN pip install --no-cache-dir \
    "wrapt>=2.2.1" \
    "numpy>=2.0" \
    "pathos>=0.2.7" \
    "discrete-optimization>=0.9.0" \
    "pynng>=0.6.2"

COPY src/autofde_lab /app/src/autofde_lab
COPY src/autofde_lab-0.0.0.dist-info /app/src/autofde_lab-0.0.0.dist-info

ENV PYTHONPATH=/app/src
ENV PORT=8090
EXPOSE 8090
USER nobody

CMD ["python3", "-m", "autofde_lab.openclaw_http"]
