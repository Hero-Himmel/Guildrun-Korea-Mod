# 게임 업데이트 작업 절차

새 Guildrun 빌드가 나올 때마다 아래 절차를 따른다. Windows와 macOS는 서로 다른 시점에 업데이트될 수 있으므로, 한 플랫폼의 빌드 번호나 체크섬을 다른 플랫폼에 적용하지 않는다.

검증은 아래 절차대로 수행하되, 검증 일시·depot/manifest 정보·테스트 결과 등의 작업별 검증 기록을 README, AGENTS.md 등 저장소 문서에 추가하거나 별도 문서로 남기지 않는다. 검증 결과는 작업 완료 시 대화로만 전달한다. 패치에 필요한 버전·빌드·체크섬 값과 사용자용 지원 안내는 해당 파일에 반영한다.

## Windows 패치

1. **기준 브랜치 동기화 및 새 브랜치 생성**
   작업 트리가 깨끗한지 확인하고 `main`을 최신 원격 상태로 fast-forward한 뒤, 게임 버전을 사용해 `feat/<게임버전>` 브랜치를 만든다. 예: `feat/0.5.10`.

2. **게임 버전과 빌드 확인**
   Steam의 설치 기록과 공식 업데이트 정보를 확인해 게임 버전과 Windows 빌드 ID를 확인한다. macOS depot의 빌드도 따로 확인하며, Windows 빌드와 같다고 가정하지 않는다.

3. **문자열 비교 및 번역**
   현재 게임의 영문 문자열 테이블과 이전 `guildrun-korean-source.json`을 ID 기준으로 비교해 새 문구와 바뀐 문구를 찾는다. 현재 zh-Hans 테이블의 추가 ID도 확인해 번역한다. 영문에는 있지만 zh-Hans에서 빠진 ID는 폐기된 항목인지 확인하고, 중복 ID와 문자열 테이블 ID도 검증한다.

4. **번역 및 버전 정보 갱신**
   번역을 `resource/guildrun-korean-source.json`에 반영하고 `game_version`, `target_build`, `entry_count`를 맞춘다. `resource/version.json`의 게임 버전, 빌드 ID, 릴리스 버전(`<게임버전>-a`)도 갱신한다. 데이터 구조가 바뀌지 않으면 `format`은 올리지 않는다.

5. **Windows 원본 체크섬 갱신**
   Steam 무결성 검사를 마친 깨끗한 Windows 설치에서 패치 대상 원본 파일의 SHA-256을 계산해 `source_files.windows`에 반영한다. 과거 해시는 의도적으로 계속 지원할 때만 남긴다. 다른 OS의 파일 해시를 복사하지 않는다.

6. **검증**
   프로젝트 Python 환경에서 `python -m unittest discover -s test -v`를 실행하고, 깨끗한 Windows 게임 설치를 입력으로 `tool/build_patch.py`를 실행한다. 빌드 보고서의 번역 ID 수와 생성 결과가 번역 원본에 맞는지 확인한다. 릴리스 패키지를 만들면 `tool/verify_release.py`도 실행한다.

7. **Windows 1차 완료**
   번역 비교, Windows 체크섬, 테스트와 패치 생성이 모두 통과하면 Windows 패치를 1차 완료로 본다. 변경 diff를 검토하고 커밋한다.

## macOS 지원 확인

8. **macOS 빌드가 제공되는 경우**
   현재 Windows 대상 빌드에 대응하는 macOS depot을 Steam에서 확보하고, 깨끗한 원본 파일의 SHA-256을 계산해 `source_files.macos`에 반영한다. macOS 입력으로 패치 생성과 호환성을 별도로 확인한다.

9. **macOS 빌드가 아직 없는 경우**
   기존 macOS 체크섬을 추측해 바꾸지 않는다. 새 게임 버전과 macOS 빌드가 일치하는지 확인할 수 없으면 README에 macOS 미지원 사실을 표시하고 Windows 전용으로 배포한다. 최신 macOS 원본을 얻을 수 없으면 SteamCMD에서 macOS 플랫폼 depot을 받거나 깨끗한 Mac Steam 설치를 사용한다. SHA-256은 파일 바이트를 대상으로 하므로 OS 간 계산 알고리즘은 같지만, Windows용 게임 파일을 macOS 원본 대신 사용할 수는 없다.

10. **완료**
    변경 파일과 검증 결과를 확인하고 버전 브랜치를 원격에 푸시한다. macOS 지원을 나중에 추가하면 같은 브랜치에 섞지 말고 해당 버전의 macOS 원본으로 별도 검증한다.
