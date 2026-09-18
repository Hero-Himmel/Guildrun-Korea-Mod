# Guildrun 한국어 MOD

Guildrun을 한국어로 플레이할 수 있도록 제작한 비공식 한글 패치입니다.

## 설치 방법

GitHub Release에서 운영체제에 맞는 파일을 내려받아 압축을 풉니다.

### Windows

1. `Guildrun-Korean-<버전>-windows.zip` 안의 `GuildrunKoreanPatcher.exe`를 실행합니다.
2. 일반적인 Steam 설치 환경에서는 아래 게임 경로를 자동으로 찾습니다.

   ```text
   C:\Program Files (x86)\Steam\steamapps\common\Guildrun Demo
   ```

3. 다른 Steam 라이브러리에 설치했다면 패처가 묻는 입력란에 `Guildrun.exe`가 있는 게임 폴더를 입력합니다.

### macOS

1. Apple Silicon Mac은 `Guildrun-Korean-<버전>-macos-arm64.zip`, Intel Mac은
   `Guildrun-Korean-<버전>-macos-x64.zip`을 내려받습니다.
2. 압축을 풀고 `GuildrunKoreanPatcher.command`를 실행합니다.
3. 일반적인 Steam 설치 환경에서는 아래 게임 경로를 자동으로 찾습니다.

   ```text
   ~/Library/Application Support/Steam/steamapps/common/Guildrun Demo
   ```

4. macOS가 실행을 차단하면 Finder에서 `.command` 파일을 Control-클릭한 뒤 `열기`를 선택하거나,
   시스템 설정의 `개인정보 보호 및 보안`에서 실행을 허용합니다.
5. 다른 Steam 라이브러리에 설치했다면 `Guildrun Demo` 폴더 또는 `Guildrun.app` 경로를 입력합니다.

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
