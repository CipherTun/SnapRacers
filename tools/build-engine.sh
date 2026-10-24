#!/usr/bin/env bash
# Builds SnapRacers' own cut down Godot engine for Android, with only what the
# game uses (see tools/engine/profile.py). The APK comes out far smaller than
# with the stock engine.
#
# The source and all the compiling go in build/godot, and scons keeps a cache
# there too, so building again after a small change is quick. The finished
# libraries are copied into tools/godot/custom, where tools/build-android.sh
# picks them up. This only needs running again for a new Godot version or a change
# to the profile.
#
# Everyday builds skip link time optimisation, which takes most of the time.
# With the compile cache warm, an architecture takes about a minute without
# it and about 13 with it. The engine comes out about 3 MB bigger without it.
# Use --release for a build going out to people, for the smallest engine.
#
#   tools/build-engine.sh             arm64 for phones and x86_64 for the emulator
#   tools/build-engine.sh arm64       just one (arm32 is for older 32 bit phones and tablets)
#   tools/build-engine.sh web         the engine for the web page (tools/build-web.sh)
#   tools/build-engine.sh desktop     the desktop engines below, all three
#   tools/build-engine.sh linux-x86_64 | linux-arm64 | windows-x86_64
#   tools/build-engine.sh --release   fully optimised, for a release
#
# The desktop release templates go in tools/godot/custom/desktop, which the
# Linux and Windows export presets use. They build in Docker, in images called
# snapracers-engine-linux (Ubuntu 22.04, so the engines run on older
# distributions) and snapracers-engine-windows (mingw), made from tools/engine
# the first time.
set -euo pipefail

LTO=none
if [ "${1:-}" = "--release" ]; then
	LTO=full
	shift
fi

cd "$(dirname "$0")/.."
VERSION=4.7.2
WORK="$PWD/build/godot"
mkdir -p "$PWD/build"
touch "$PWD/build/.gdignore"
SOURCE="$WORK/godot"
OUT=tools/godot/custom
PROFILE="$PWD/tools/engine/profile.py"
ARCHES=("${@:-arm64 x86_64}")
ARCHES=(${ARCHES[@]/desktop/linux-x86_64 linux-arm64 windows-x86_64})
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
CACHE="$WORK/cache"

mkdir -p "$WORK" "$CACHE"
if [ ! -d "$SOURCE" ]; then
	echo "Getting the Godot $VERSION source"
	git clone -q --depth 1 --branch "$VERSION-stable" https://github.com/godotengine/godot.git "$SOURCE"
fi
# Swappy paces frames on Android. Without it the game stutters.
if [ ! -f "$SOURCE/thirdparty/swappy-frame-pacing/arm64-v8a/libswappy_static.a" ]; then
	echo "Getting Swappy"
	(cd "$SOURCE" && python3 misc/scripts/install_swappy_android.py)
fi
if [ ! -x "$WORK/venv/bin/scons" ]; then
	echo "Setting up scons"
	uv venv -q --clear "$WORK/venv"
	uv pip install -q --python "$WORK/venv/bin/python" scons
fi

# Every option the profile sets, as name=value for scons.
OPTIONS="$(python3 -c '
import sys
options = {}
exec(open(sys.argv[1]).read(), options)
print(" ".join("%s=%s" % (k, v) for k, v in options.items() if not k.startswith("_")))
' "$PROFILE") lto=$LTO"
echo "Engine options: $OPTIONS"

# Runs scons in a Docker image (snapracers-engine-linux or -windows, made from
# tools/engine the first time), as this user, with the source and the cache
# mounted where they are on the host.
docker_scons() {
	local image="snapracers-engine-$1"
	shift
	if ! docker image inspect "$image" > /dev/null 2>&1; then
		echo "Making the $image Docker image"
		docker build -q -t "$image" -f "$PWD/tools/engine/${image#snapracers-engine-}.Dockerfile" "$PWD/tools/engine"
	fi
	docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$WORK:$WORK" -w "$SOURCE" \
		"$image" scons "$@" cache_path="$CACHE" -j"$(nproc)"
}

for arch in "${ARCHES[@]}"; do
	# The desktop release templates, with the same options as the phones.
	case "$arch" in
		linux-x86_64|linux-arm64|windows-x86_64)
			mkdir -p "$OUT/desktop"
			echo "Building the $arch engine"
			case "$arch" in
				linux-x86_64)
					docker_scons linux platform=linuxbsd arch=x86_64 target=template_release $OPTIONS
					cp "$SOURCE/bin/godot.linuxbsd.template_release.x86_64" "$OUT/desktop/linux_x86_64_release" ;;
				linux-arm64)
					docker_scons linux platform=linuxbsd arch=arm64 CC=aarch64-linux-gnu-gcc CXX=aarch64-linux-gnu-g++ target=template_release $OPTIONS
					cp "$SOURCE/bin/godot.linuxbsd.template_release.arm64" "$OUT/desktop/linux_arm64_release" ;;
				windows-x86_64)
					docker_scons windows platform=windows arch=x86_64 use_mingw=yes d3d12=no angle=no target=template_release $OPTIONS
					cp "$SOURCE/bin/godot.windows.template_release.x86_64.exe" "$OUT/desktop/windows_x86_64_release.exe" ;;
			esac
			ls -l "$OUT/desktop"
			continue ;;
	esac
	# The web page's engine, without threads, so it runs on any web host (a
	# threaded one needs the host to send special headers, which GitLab
	# Pages can't). It needs Emscripten, which is looked for in the usual
	# place.
	if [ "$arch" = web ]; then
		EMSDK="${EMSDK:-$HOME/.local/share/emsdk}"
		# shellcheck disable=SC1091
		source "$EMSDK/emsdk_env.sh" > /dev/null 2>&1
		echo "Building the engine for the web page"
		(cd "$SOURCE" && "$WORK/venv/bin/scons" platform=web target=template_release threads=no $OPTIONS cache_path="$CACHE" -j"$(nproc)")
		mkdir -p "$OUT/web"
		cp "$SOURCE/bin/godot.web.template_release.wasm32.nothreads.zip" "$OUT/web/web_nothreads_release.zip"
		ls -l "$OUT/web/web_nothreads_release.zip"
		continue
	fi
	# Phones get the release engine. The emulator gets a debug one, so the
	# game's debug switches (like the autopilot) work there.
	case "$arch" in
		arm64) abi=arm64-v8a; kind=release ;;
		arm32) abi=armeabi-v7a; kind=release ;;
		x86_64) abi=x86_64; kind=debug ;;
		*) echo "I don't know the architecture $arch" >&2; exit 1 ;;
	esac
	echo "Building the $kind engine for $abi"
	(cd "$SOURCE" && "$WORK/venv/bin/scons" platform=android arch="$arch" target="template_$kind" $OPTIONS cache_path="$CACHE" -j"$(nproc)")
	mkdir -p "$OUT/$abi"
	cp "$SOURCE/platform/android/java/lib/libs/$kind/$abi/libgodot_android.so" "$OUT/$abi/"
	ls -l "$OUT/$abi/libgodot_android.so"
done
