#!/bin/zsh
set -euo pipefail

repository="Hero-Himmel/Guildrun-Korea-Mod"
curl_bin="/usr/bin/curl"

fail() {
    print -u2 -- "설치 실패: $1"
    exit 1
}

[[ "$(/usr/bin/uname -s)" == "Darwin" ]] || fail "macOS에서만 실행할 수 있습니다"
[[ -x "$curl_bin" ]] || fail "curl을 찾지 못했습니다"

case "$(/usr/bin/uname -m)" in
    arm64 | aarch64)
        architecture="arm64"
        ;;
    x86_64 | amd64)
        architecture="x64"
        ;;
    *)
        fail "지원하지 않는 Mac 아키텍처입니다: $(/usr/bin/uname -m)"
        ;;
esac

latest_url="$($curl_bin -fsSL --proto '=https' --tlsv1.2 \
    -o /dev/null -w '%{url_effective}' \
    "https://github.com/$repository/releases/latest")"
tag="${latest_url##*/}"
[[ "$tag" == v* ]] || fail "최신 릴리즈 버전을 확인하지 못했습니다"
version="${tag#v}"

asset="Guildrun-Korean-$version-macos-$architecture.zip"
checksum="$asset.sha256"
download_base="https://github.com/$repository/releases/download/$tag"
temporary_root="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/guildrun-korean.XXXXXX")"

cleanup() {
    /bin/rm -rf "$temporary_root"
}
trap cleanup EXIT

print -- "Guildrun 한국어 패치 $version ($architecture)"
print -- "다운로드: $download_base/$asset"

$curl_bin -fL --retry 3 --proto '=https' --tlsv1.2 \
    -o "$temporary_root/$asset" "$download_base/$asset"
$curl_bin -fL --retry 3 --proto '=https' --tlsv1.2 \
    -o "$temporary_root/$checksum" "$download_base/$checksum"

(
    cd "$temporary_root"
    /usr/bin/shasum -a 256 -c "$checksum"
)

extract_root="$temporary_root/extracted"
/bin/mkdir "$extract_root"
/usr/bin/ditto -x -k "$temporary_root/$asset" "$extract_root"
/bin/chmod +x \
    "$extract_root/GuildrunKoreanPatcher" \
    "$extract_root/GuildrunKoreanPatcher.command"

"$extract_root/GuildrunKoreanPatcher" "$@"
