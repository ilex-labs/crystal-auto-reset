#!/bin/bash
# Fetch the exact toolchain used to build and verify the released plugins on
# x86_64 Linux. Usage: tools/setup_toolchain_linux.sh [DIR] (default .toolchain)
# Then: source DIR/env.sh && python3 tools/build_legacy.py
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
T=$(mkdir -p "${1:-$ROOT/.toolchain}" && cd "${1:-$ROOT/.toolchain}" && pwd)
cd "$T"

# devkitARM from the devkitpro/devkitarm Docker Hub image
# (amd64 manifest sha256:15b79ce75822c289538d8153da5fa7aafe5e6adc32ad8a575a197beca0f0761b).
mkdir -p dka && cd dka
TOKEN=$(curl -sS -m 30 "https://auth.docker.io/token?service=registry.docker.io&scope=repository:devkitpro/devkitarm:pull" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')
for d in ea5d3216df1fb580c54c016ee13ff58eb965c0a0b0ef08afd8dfd5a1c03e95a8 \
         3c5026e520aeec9e208399f6d0a62098d5ee4c13d8cca97cdb9adbc6bb56a1c0; do
  [ -f "layer_$d.tgz" ] || curl -sSL -m 900 -H "Authorization: Bearer $TOKEN" -o "layer_$d.tgz" \
    "https://registry-1.docker.io/v2/devkitpro/devkitarm/blobs/sha256:$d"
  echo "$d  layer_$d.tgz" | sha256sum -c -
done
mkdir -p root
for f in layer_ea5d*.tgz layer_3c50*.tgz; do tar -xzf "$f" -C root opt/devkitpro 2>/dev/null || true; done
cd "$T"

# libctru svc.s (the only libctru source the build compiles)
rm -rf libctru-src && git clone -q --depth 1 https://github.com/devkitPro/libctru libctru-src
mkdir -p dka/root/opt/devkitpro/libctru/source
cp libctru-src/libctru/source/svc.s dka/root/opt/devkitpro/libctru/source/

# Rust nightly-2024-03-21 with rust-src
curl -sSf -m 60 https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init -o rustup-init
chmod +x rustup-init
export RUSTUP_HOME="$T/rustup" CARGO_HOME="$T/cargo"
./rustup-init -y --no-modify-path --default-toolchain none -q
"$CARGO_HOME/bin/rustup" toolchain install nightly-2024-03-21 --profile minimal -c rust-src

# 3gxtool pinned to commit 57e3160ab7
rm -rf 3gxtool && git clone -q https://gitlab.com/thepixellizeross/3gxtool.git 3gxtool
(cd 3gxtool && git checkout -q 57e3160ab7 && git submodule update --init --depth 1 \
  && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build . -j"$(nproc)")
mkdir -p bin && cp 3gxtool/build/3gxtool bin/

cat > env.sh <<EOF
export RUSTUP_HOME="$T/rustup" CARGO_HOME="$T/cargo"
export DEVKITPRO="$T/dka/root/opt/devkitpro"
export CRYSTAL_RUST_HOST=x86_64-unknown-linux-gnu
export PATH="$T/cargo/bin:$T/dka/root/opt/devkitpro/devkitARM/bin:$T/bin:\$PATH"
EOF
echo "Toolchain ready. Run: source $T/env.sh"
