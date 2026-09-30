# Guildrun Demo 0.5.11 macOS 검증

## 원본 확인

- 검증 날짜: 2026-09-30 (KST)
- macOS 앱 `Info.plist`: `CFBundleShortVersionString`, `CFBundleVersion` 모두 `0.5.11`
- Mac Steam 설치 기록 `appmanifest_4425970.acf`: Build ID `25604606`
- macOS depot: `4425972`, manifest `4751633551822551778`
- Steam 무결성 검사: 10:29:01 시작, 10:29:16 `No Error`로 완료
- 체크섬: 무결성 검사 후 Mac 설치의 파일 바이트에서 SHA-256 계산, `resource/version.json`에 반영

Windows 빌드 번호를 복사하지 않고 Mac 설치 기록에서 별도로 확인했다.
`resources.assets`와 `global-metadata.dat`의 체크섬이 변경되었으며,
카탈로그와 zh-Hans 번들의 체크섬은 기존 값과 같았다.

## 문자열 및 패치 검증

- 영문: 16개 테이블, 3,923개 ID. 번역 원본 대비 누락, 영문 변경, 테이블 ID 불일치 없음.
- zh-Hans: 16개 테이블, 3,922개 ID. 번역 누락과 테이블 ID 불일치 없음.
- 두 언어 테이블에서 중복 ID 없음.
- 번역 원본: 기존 Windows 검증에서 유지한 항목을 포함한 3,927개 ID.
- Mac 패치 생성: 16개 테이블, 번역 3,927개, 폰트 18개 처리 성공.
- 생성한 번들을 다시 읽어 번역문과 메타데이터가 번역 JSON과 일치하는지 확인.
- `python -m unittest discover -s test -v`: 4개 통과.

## 배포 검증

- 로컬 환경: macOS arm64, Python 3.14.7, UnityPy 1.25.3, PyInstaller 6.22.2.
- `tool/package_release.py --platform macos`로 arm64 패처 ZIP 생성.
- `tool/verify_release.py --platform macos`로 ZIP 내용, 실행 권한, 파일 체크섬 검증.
- 배포 실행 파일의 `--action check`로 Mac 원본 호환성 검사.
- 원본 대상 파일을 복사한 임시 게임 폴더에서 배포 실행 파일로 설치 후,
  네 파일이 `build_patch.py` 출력과 바이트 단위로 같은지 확인.
- 검증 후 Steam 설치 원본 네 파일의 SHA-256이 그대로인지 확인.

게임을 실행해 화면과 플레이를 확인하는 검증은 수행하지 않았다.
Intel Mac 실행 검증은 수행하지 않았으며, x64 배포 빌드는 복구한 GitHub Actions의
`macos-15-intel` 작업에서 별도로 생성·검증한다. 로컬 산출물은 Git에 포함하지 않는다.
