# Guildrun 한국어 MOD

Guildrun을 한국어로 플레이할 수 있도록 제작한 비공식 한글 패치입니다.

## 폴더 구조

- `tool/unity_patch.py` — Unity 번들·폰트·메타데이터·카탈로그 가공
- `tool/build_patch.py` — 사용자의 Steam 원본 4개를 읽어 패치 파일 4개 생성
- `tool/runtime_patcher.py` — 해시 검사·임시 생성·백업·교체·복원 담당
- `tool/package_release.py` — 원본 게임 파일 없이 Release용 EXE·ZIP 생성
- `tool/verify_release.py` — 생성된 Release에 원본 게임 파일이 없는지와 무결성 검사
- `resource/fonts/` — Noto Sans KR 7종과 `font-config.json`
- `resource/icons/GuildrunKoreanPatcher.ico` — 한국어 패처 EXE 아이콘
- `resource/guildrun-korean-source.json` — 버전·번역문·Unity 메타데이터를 포함한 원본
- `resource/version.json` — 게임 버전·대상 빌드·패치 릴리즈 버전의 단일 기준

게임 원본 4개는 저장소와 Release에 넣지 않습니다. Release ZIP에는 실행에 필요한 번역·폰트까지
내장한 `GuildrunKoreanPatcher.exe` 한 파일만 들어 있습니다. 설치기는 사용자의 Steam 설치본 원본
4개 해시를 검사한 뒤 임시 폴더에서 한국어 파일을 생성합니다.

기본 Steam 경로가 있으면 설치기가 바로 호환성 검사를 진행하고, 없을 때만 게임 경로를 묻습니다.
호환성 테스트 뒤에는 주의사항과 `1. Yes / 2. No` 확인을 표시합니다. `No`를 고르면 게임 파일을
변경하지 않고 종료합니다.

`main` 또는 Release 워크플로 파일을 main 브랜치에 push하면 GitHub Actions가 EXE와 ZIP을 만들고,
`version.json`의 `release` 값을 태그로 GitHub Release에 올립니다. 게임 원본 파일은 이 과정에도 포함되지 않습니다.

## 참고 및 감사

이 프로젝트는 [Guildrun Japanese Mod](https://github.com/tomate045/Guildrun-Japanese-Mod)를 참고하여 제작했습니다.

## 제작자

- 일본어 MOD 제작: [@tomathinn_G](https://x.com/tomathinn_G)
- 한국어 MOD 제작: [@himmel_dev](https://x.com/himmel_dev)

## 피드백

패치 관련 피드백은 [Guildrun 마이너 갤러리](https://gall.dcinside.com/mgallery/board/lists/?id=guildrun) 또는 이 저장소의 [Issues](https://github.com/Hero-Himmel/Guildrun-Korea-Mod/issues)에 올려 주세요.

## 주의 사항

이 MOD는 비공식입니다. 사용에 따른 책임은 사용자 본인에게 있습니다. MOD 사용으로 발생한 문제에 대해서는 책임질 수 없으니 양해 바랍니다.

게임 본체의 원문과 각종 소재에 대한 권리는 각각의 권리자에게 있습니다.

번역은 AI를 활용했습니다. 번역 데이터를 다른 MOD에 포함해 재배포하거나, 직접 만든 번역인 것처럼 배포하는 행위는 삼가 주세요.
