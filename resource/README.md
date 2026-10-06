# 패치 리소스

이 폴더의 파일은 `GuildrunKoreanPatcher.exe`에 내장됩니다. 게임 원본 파일은 포함하지 않습니다.

## 파일 역할

- `guildrun-korean-source.json` — 한국어 번역문과 Unity 패치에 필요한 메타데이터
- `fonts/` — Noto Sans KR 폰트와 Unity 폰트 연결 설정
- `icons/GuildrunKoreanPatcher.ico` — 패처 EXE 아이콘
- `version.json` — 지원 게임 빌드와 원본 파일 해시, 패치 릴리즈 정보

## 릴리즈 버전 규칙

`version.json`의 `release`는 `<게임 버전>-<알파벳>` 형식으로 표기합니다.

- 예: `0.5.7-a`, `0.5.7-b`, `0.5.7-c`
- 같은 게임 버전에서 패치 내용을 갱신할 때 마지막 알파벳을 `a`부터 `z` 순서로 올립니다.
- 게임 버전이 바뀌면 새 게임 버전에 맞는 릴리즈 표기로 다시 시작합니다.

## `format` 값

`format`은 패치나 게임의 버전이 아니라 `version.json`의 데이터 구조 규격 번호입니다.
현재 `format: 2`는 운영체제별 원본 파일 경로와 해시를 구분합니다.

```text
game, game_version, target_build, release
source_files.windows, source_files.macos
```

번역 추가, 폰트 교체, 해시 추가, `release` 변경에는 `format` 값을 올리지 않습니다.
패처가 읽는 필드 구조나 의미를 호환되지 않게 바꿀 때만 다음 번호로 올립니다.

## macOS 원본 체크섬 수집

0.5.12 검증 기록 (2026-10-07): Mac Steam 설치의 앱 버전 `0.5.12`, 빌드 `25751498`,
macOS depot `4425972`, manifest `7486977727052746079`를 확인했습니다. Steam 무결성 검사
완료 후 원본 4개 파일의 SHA-256을 확인했으며, 이전 값에서 `resources.assets`만 변경됐습니다.
원본 체크섬 호환성 검사와 macOS 패치 생성(번역 3,927개, 문자열 테이블 16개), 단위 테스트 4개를
통과했습니다. 게임 실행을 통한 화면 확인은 포함하지 않습니다.

체크섬은 운영체제가 아니라 파일 바이트로 계산하므로, 깨끗한 macOS Steam 설치에서 원본 파일을
읽어 SHA-256을 계산하면 됩니다. 패치된 게임이나 Steam 무결성 검사를 하지 않은 설치는 사용하지 마세요.

```bash
GAME="$HOME/Library/Application Support/Steam/steamapps/common/Guildrun Demo"
shasum -a 256 \
  "$GAME/Guildrun.app/Contents/Resources/Data/resources.assets" \
  "$GAME/Guildrun.app/Contents/Resources/Data/il2cpp_data/Metadata/global-metadata.dat" \
  "$GAME/Guildrun.app/Contents/Resources/Data/StreamingAssets/aa/catalog.bin" \
  "$GAME/Guildrun.app/Contents/Resources/Data/StreamingAssets/aa/StandaloneOSX/localization-string-tables-chinese(simplified)(zh-hans)_assets_all.bundle"
```

Mac을 사용할 수 없다면 SteamCMD에서 macOS 플랫폼을 지정해 macOS depot 원본을 내려받은 뒤 동일하게
SHA-256을 계산할 수 있습니다. Windows용 대응 파일의 체크섬을 macOS 경로에 복사해서는 안 됩니다.
