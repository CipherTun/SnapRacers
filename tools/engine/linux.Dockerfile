# Builds SnapRacers' Linux engines, x86_64 and arm64 (tools/build-engine.sh).
# Ubuntu 22.04 so the engines run on any Linux with glibc 2.35 or newer.
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config python3 python3-pip git ca-certificates \
    gcc-aarch64-linux-gnu g++-aarch64-linux-gnu \
    && pip3 install --no-cache-dir scons \
    && rm -rf /var/lib/apt/lists/*
