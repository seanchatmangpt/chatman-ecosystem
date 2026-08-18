#!/usr/bin/env bash
# Loads the real, official `aquasec/trivy` scanner image into this kind
# cluster's node containerd, so k8s/paas-rbac.yaml's
# platform-console-vuln-scan Job (lib/vuln-scan.ts) can run it with
# `imagePullPolicy: IfNotPresent` and no in-cluster registry pull.
#
# `kind load docker-image aquasec/trivy:<tag>` was tried first and
# genuinely failed on this real setup (confirmed live, not assumed): the
# official image is multi-platform, and kind's own `ctr images import
# --all-platforms` path errored with a real
# `content digest ...: not found` against this manifest. The real,
# working alternative (also confirmed live) is the one this script
# automates: `docker save` the already-pulled image to a tar, `docker cp`
# it into the kind control-plane container (NOT /tmp -- that path is a
# separate tmpfs mount inside the node container that does not retain
# `docker cp`'d files, confirmed live), then `ctr images import` it
# directly, which correctly resolves the manifest list to this node's
# real platform (linux/arm64 on this host).
set -euo pipefail

TRIVY_TAG="${TRIVY_TAG:-0.67.2}"
KIND_NODE="${KIND_NODE:-platform-eng-colima-control-plane}"
TAR_PATH="/root/trivy-scanner-image.tar"

echo "==> docker pull aquasec/trivy:${TRIVY_TAG}"
docker pull "aquasec/trivy:${TRIVY_TAG}"

TMP_TAR="$(mktemp -t trivy-scanner-image-XXXXXX.tar)"
trap 'rm -f "${TMP_TAR}"' EXIT

echo "==> docker save -> ${TMP_TAR}"
docker save "aquasec/trivy:${TRIVY_TAG}" -o "${TMP_TAR}"

echo "==> docker cp into ${KIND_NODE}:${TAR_PATH}"
docker cp "${TMP_TAR}" "${KIND_NODE}:${TAR_PATH}"

echo "==> ctr images import (real containerd import, resolves this node's real platform)"
docker exec "${KIND_NODE}" ctr --namespace=k8s.io images import "${TAR_PATH}"
docker exec "${KIND_NODE}" rm -f "${TAR_PATH}"

echo "==> verifying real image is present in the node's containerd"
docker exec "${KIND_NODE}" crictl images | grep -i trivy
