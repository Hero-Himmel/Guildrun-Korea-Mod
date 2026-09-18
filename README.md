# Guildrun 한국어 MOD

Guildrun을 한국어로 플레이할 수 있도록 제작한 비공식 한글 패치입니다.

## 설치 방법

Windows는 GitHub Release 파일을 사용하고, macOS는 아래 터미널 설치 명령을 사용합니다.

### Windows

1. `Guildrun-Korean-<버전>-windows.zip` 안의 `GuildrunKoreanPatcher.exe`를 실행합니다.
2. 일반적인 Steam 설치 환경에서는 아래 게임 경로를 자동으로 찾습니다.

   ```text
   C:\Program Files (x86)\Steam\steamapps\common\Guildrun Demo
   ```

3. 다른 Steam 라이브러리에 설치했다면 패처가 묻는 입력란에 `Guildrun.exe`가 있는 게임 폴더를 입력합니다.

### macOS

터미널을 열고 아래 명령을 붙여 넣어 실행합니다.

```bash
/bin/zsh -c "$(/usr/bin/curl -fsSL https://raw.githubusercontent.com/Hero-Himmel/Guildrun-Korea-Mod/main/install-macos.sh)"
```

설치 스크립트는 최신 릴리즈와 Mac 아키텍처를 확인하고, 맞는 패처와 SHA-256 체크섬을 내려받아
검증한 뒤 임시 폴더에서 실행합니다. `sudo`를 요구하거나 Gatekeeper 설정을 변경하지 않으며,
패처가 종료되면 다운로드한 임시 파일을 삭제합니다.

일반적인 Steam 설치 환경에서는 아래 게임 경로를 자동으로 찾습니다.

```text
~/Library/Application Support/Steam/steamapps/common/Guildrun Demo
```

다른 Steam 라이브러리에 설치했다면 패처가 묻는 입력란에 `Guildrun Demo` 폴더 또는
`Guildrun.app` 경로를 입력합니다.

원격 스크립트를 먼저 확인하려면 다음 순서로 실행할 수 있습니다.

```bash
/usr/bin/curl -fsSLO https://raw.githubusercontent.com/Hero-Himmel/Guildrun-Korea-Mod/main/install-macos.sh
/usr/bin/less install-macos.sh
/bin/zsh install-macos.sh
```

GitHub Release의 아키텍처별 macOS ZIP을 직접 내려받는 방법도 제공하지만, 브라우저로 받은
서명되지 않은 실행 파일은 Gatekeeper가 차단할 수 있으므로 위 설치 명령을 권장합니다.

## 패치 제거 및 복구

이미 한글 패치를 적용했거나 게임이 업데이트되어 호환성 테스트에 실패했다면, 먼저
[Steam 게임 파일 무결성 검사 안내](https://help.steampowered.com/ko/faqs/view/0C48-FCBD-DA71-93EB)를 따라
게임 파일을 복구하세요. 이후 게임 버전에 맞는 최신 한글 패치 ZIP을 내려받아 압축을 풀고 다시 적용하면 됩니다.

패처는 영구 백업을 남기지 않습니다. 패치 생성이 끝난 뒤 원본 파일을 임시 보관하고, 설치 도중 문제가
발생하면 자동으로 되돌립니다. 정상 설치 후 패치를 제거할 때는 Steam 게임 파일 무결성 검사를 사용하세요.

## 폴더 구조

- `tool/unity_patch.py` — Unity 번들·폰트·메타데이터·카탈로그 가공
- `tool/game_layout.py` — Windows/macOS 게임 경로와 플랫폼별 파일 구조 탐색
- `tool/build_patch.py` — 사용자의 Steam 원본 4개를 읽어 패치 파일 4개 생성
- `tool/runtime_patcher.py` — 해시 검사·임시 생성·트랜잭션 교체·실패 시 롤백 담당
- `tool/package_release.py` — 원본 게임 파일 없이 운영체제별 실행 파일·ZIP 생성
- `tool/verify_release.py` — 생성된 Release에 원본 게임 파일이 없는지와 무결성 검사
- `install-macos.sh` — 최신 macOS 패처를 검증·임시 실행하는 설치 스크립트
- `resource/fonts/` — Noto Sans KR 7종과 `font-config.json`
- `resource/icons/GuildrunKoreanPatcher.ico` — 한국어 패처 EXE 아이콘
- `resource/guildrun-korean-source.json` — 버전·번역문·Unity 메타데이터를 포함한 원본
- `resource/version.json` — 게임 버전·대상 빌드·패치 릴리즈 버전의 단일 기준

## OFL

이 패치에는 Noto Sans KR 폰트가 포함되어 있으며, 해당 폰트는
[SIL Open Font License 1.1](https://openfontlicense.org/open-font-license-official-text/)에 따라 배포됩니다.

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
