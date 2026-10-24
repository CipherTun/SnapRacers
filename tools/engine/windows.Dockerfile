# Builds SnapRacers' Windows engine with mingw (tools/build-engine.sh).
FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config python3 scons git ca-certificates \
    gcc-mingw-w64-x86-64-posix g++-mingw-w64-x86-64-posix \
    && update-alternatives --set x86_64-w64-mingw32-gcc /usr/bin/x86_64-w64-mingw32-gcc-posix \
    && update-alternatives --set x86_64-w64-mingw32-g++ /usr/bin/x86_64-w64-mingw32-g++-posix \
    && rm -rf /var/lib/apt/lists/*
