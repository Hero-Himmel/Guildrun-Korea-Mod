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
현재 `format: 1`은 아래 필드와 의미를 사용하는 첫 번째 규격이라는 뜻입니다.

```text
game, game_version, target_build, release, source_files
```

번역 추가, 폰트 교체, 해시 추가, `release` 변경에는 `format` 값을 올리지 않습니다.
패처가 읽는 필드 구조나 의미를 호환되지 않게 바꿀 때만 다음 번호로 올립니다.
