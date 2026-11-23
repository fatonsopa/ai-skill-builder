#!/bin/sh
# Install the Skill Builder CLI from a GitHub release.
# Verifies the payload against the release's SHA256SUMS before changing anything.
# Environment: SKILL_BUILDER_VERSION (tag, default latest), SKILL_BUILDER_PREFIX
# (default ~/.local), SKILL_BUILDER_RELEASE_BASE (asset folder URL, for testing a
# candidate before publication).
set -eu

repository=fatonsopa/ai-skill-builder
tag=${SKILL_BUILDER_VERSION:-latest}
prefix=${SKILL_BUILDER_PREFIX:-$HOME/.local}
root=$prefix/share/skill-builder
launcher=$prefix/bin/skill-builder
marker='# skill-builder launcher: managed by the GitHub release installer'

fail() { printf 'skill-builder install: %s\n' "$1" >&2; exit "${2:-1}"; }

if [ -n "${SKILL_BUILDER_RELEASE_BASE:-}" ]; then
  base=$SKILL_BUILDER_RELEASE_BASE
elif [ "$tag" = latest ]; then
  base=https://github.com/$repository/releases/latest/download
else
  base=https://github.com/$repository/releases/download/$tag
fi

case $(uname -s) in
  Darwin|Linux) ;;
  *) fail "unsupported platform $(uname -s); use macOS, Linux or WSL." ;;
esac
command -v curl >/dev/null 2>&1 || fail 'curl is required. Install curl, then run this installer again.'
if command -v sha256sum >/dev/null 2>&1; then
  hash_file() { sha256sum "$1" | cut -d ' ' -f 1; }
elif command -v shasum >/dev/null 2>&1; then
  hash_file() { shasum -a 256 "$1" | cut -d ' ' -f 1; }
else
  fail 'sha256sum or shasum is required to verify the release.'
fi
python=
for candidate in python3.14 python3.13 python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
    python=$(command -v "$candidate"); break
  fi
done
[ -n "$python" ] || fail 'Python 3.11 or later is required. Install it, make sure python3.11 or newer is on PATH, then run this installer again.'

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
curl -fsSL "$base/SHA256SUMS" -o "$work/SHA256SUMS" || fail "could not download SHA256SUMS from $base."
asset=$(awk '$2 ~ /^skill-builder-.*\.tar\.gz$/ { print $2 }' "$work/SHA256SUMS")
[ "$(printf '%s\n' "$asset" | grep -c .)" = 1 ] || fail "SHA256SUMS at $base does not list exactly one skill-builder payload."
expected=$(awk -v name="$asset" '$2 == name { print $1 }' "$work/SHA256SUMS")
curl -fsSL "$base/$asset" -o "$work/$asset" || fail "could not download $asset from $base."
actual=$(hash_file "$work/$asset")
[ "$actual" = "$expected" ] || fail "checksum mismatch for $asset: SHA256SUMS lists $expected, the download is $actual. Nothing was changed; the current installation stays in place." 4

mkdir -p "$work/payload"
tar -xzf "$work/$asset" -C "$work/payload"
version=$("$python" -c 'import json, sys; print(json.load(open(sys.argv[1]))["version"])' "$work/payload/config/release.json")
release=$root/releases/$version
if [ -e "$launcher" ] && ! grep -qF "$marker" "$launcher"; then
  fail "$launcher exists and was not written by this installer. Move it, then run the installer again." 3
fi

if [ -f "$release.sha256" ] && [ "$(cat "$release.sha256")" = "$actual" ]; then
  printf 'skill-builder %s is already installed at %s\n' "$version" "$release"
else
  mkdir -p "$root/releases"
  staging=$root/releases/.staging-$$
  rm -rf "$staging"
  mv "$work/payload" "$staging"
  if ! "$python" -m venv "$staging/.venv" || ! "$staging/.venv/bin/python" -m pip install --quiet --disable-pip-version-check -r "$staging/scripts/requirements-lock.txt"; then
    rm -rf "$staging"
    fail 'could not set up the Python environment. The current installation stays in place.'
  fi
  rm -rf "$release"
  mv "$staging" "$release"
  printf '%s\n' "$actual" > "$release.sha256"
fi
ln -sfn "releases/$version" "$root/current"
mkdir -p "$prefix/bin"
cat > "$launcher.tmp" <<LAUNCHER
#!/bin/sh
$marker
SKILL_BUILDER_LAUNCHER="\$0" exec "$root/current/.venv/bin/python" "$root/current/scripts/release_cli.py" "\$@"
LAUNCHER
chmod 755 "$launcher.tmp"
mv "$launcher.tmp" "$launcher"

printf 'Installed skill-builder %s from %s\n' "$version" "$asset"
printf 'Owned paths: %s, %s, %s, %s\n' "$launcher" "$release" "$release.sha256" "$root/current"
case ":$PATH:" in
  *":$prefix/bin:"*) ;;
  *) printf 'Add %s to PATH to run skill-builder.\n' "$prefix/bin" ;;
esac
printf 'Next: skill-builder --version, then skill-builder host init --tools codex,claude\n'
