"""Build and install the Guildrun Korean patch from the user's local game files."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from build_patch import RELATIVE, RELEASE, VERSION, build_patch


DEFAULT_GAME_ROOT = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Guildrun Demo")
APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
SOURCE_FILES = tuple(RELATIVE[key] for key in ("resources", "metadata", "catalog", "target"))


def configure_console() -> None:
    """Use UTF-8 directly from the EXE; no CMD launcher is required."""
    if os.name != "nt" or not sys.stdout.isatty():
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        if sys.stdin.isatty():
            kernel32.SetConsoleCP(65001)
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def safe_path(root: Path, relative: Path | str) -> Path:
    root = root.resolve()
    target = (root / relative).resolve()
    if target != root and root not in target.parents:
        raise RuntimeError(f"Unsafe path: {relative}")
    return target


def load_source_hashes() -> dict[str, set[str]]:
    configured = VERSION.get("source_files")
    expected_paths = {path.as_posix() for path in SOURCE_FILES}
    if not isinstance(configured, dict) or set(configured) != expected_paths:
        raise RuntimeError("version.json의 source_files 구성이 잘못되었습니다")
    result: dict[str, set[str]] = {}
    for relative, hashes in configured.items():
        if not isinstance(hashes, list) or not hashes or not all(isinstance(value, str) for value in hashes):
            raise RuntimeError(f"version.json의 해시 목록이 잘못되었습니다: {relative}")
        result[relative] = set(hashes)
    return result


def verify_game_root(game_root: Path) -> None:
    if not game_root.is_dir():
        raise RuntimeError(f"게임 폴더가 없습니다: {game_root}")
    if not safe_path(game_root, "Guildrun.exe").is_file():
        raise RuntimeError("Guildrun.exe가 들어 있는 게임 폴더를 지정하세요")


def verify_source_files(game_root: Path) -> dict[str, str]:
    verify_game_root(game_root)
    allowed = load_source_hashes()
    observed: dict[str, str] = {}
    for relative in SOURCE_FILES:
        path = safe_path(game_root, relative)
        if not path.is_file():
            raise RuntimeError(f"필수 게임 파일이 없습니다: {relative.as_posix()}")
        digest = sha256(path)
        observed[relative.as_posix()] = digest
        if digest not in allowed[relative.as_posix()]:
            raise RuntimeError(
                f"지원하지 않는 게임 파일입니다: {relative.as_posix()}. "
                "Steam 무결성 검사 후 다시 시도하세요"
            )
    return observed


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_backup(game_root: Path, hashes: dict[str, str]) -> tuple[Path, dict[str, Any]]:
    backup_root = safe_path(game_root, ".guildrun-ko-backups")
    backup_root.mkdir(exist_ok=True)
    backup_dir = backup_root / f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex}"
    backup_dir.mkdir()
    state: dict[str, Any] = {
        "format": 1,
        "release": RELEASE,
        "status": "prepared",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_hashes": hashes,
        "files": [path.as_posix() for path in SOURCE_FILES],
    }
    for relative in SOURCE_FILES:
        source = safe_path(game_root, relative)
        destination = safe_path(backup_dir, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    write_state(backup_dir / "state.json", state)
    return backup_dir, state


def replace_from_payload(game_root: Path, payload_root: Path, backup_dir: Path, state: dict[str, Any]) -> None:
    state["status"] = "applying"
    write_state(backup_dir / "state.json", state)
    replaced: list[Path] = []
    try:
        for relative in SOURCE_FILES:
            source = safe_path(payload_root, relative)
            destination = safe_path(game_root, relative)
            if not source.is_file():
                raise RuntimeError(f"생성된 패치 파일이 없습니다: {relative.as_posix()}")
            temporary = destination.with_name(destination.name + f".guildrun-ko-{uuid.uuid4().hex}.tmp")
            shutil.copy2(source, temporary)
            os.replace(temporary, destination)
            replaced.append(relative)
    except Exception:
        for relative in replaced:
            shutil.copy2(safe_path(backup_dir, relative), safe_path(game_root, relative))
        state["status"] = "failed_restored"
        write_state(backup_dir / "state.json", state)
        raise
    state["status"] = "installed"
    write_state(backup_dir / "state.json", state)


def format_duration(seconds: int) -> str:
    hours, remaining = divmod(seconds, 3600)
    minutes, seconds = divmod(remaining, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"


class ProgressTimer:
    """Keep a single elapsed-time line below the current patch stage."""

    def __init__(self) -> None:
        self.started_at = time.monotonic()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_second = -1

    def elapsed_seconds(self) -> int:
        return int(time.monotonic() - self.started_at)

    def _render(self) -> None:
        print(f"\r진행 시간: {format_duration(self.elapsed_seconds())}", end="", flush=True)

    def _clear_line(self) -> None:
        print("\r" + " " * 32 + "\r", end="", flush=True)

    def _tick(self) -> None:
        while not self._stop_event.wait(0.1):
            with self._lock:
                elapsed = self.elapsed_seconds()
                if elapsed != self._last_second:
                    self._last_second = elapsed
                    self._render()

    def start(self) -> None:
        with self._lock:
            self._last_second = self.elapsed_seconds()
            self._render()
        if sys.stdout.isatty():
            self._thread = threading.Thread(target=self._tick, name="progress-timer", daemon=True)
            self._thread.start()

    def stage(self, message: str) -> None:
        with self._lock:
            self._clear_line()
            print(message)
            self._render()

    def stop(self) -> int:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1)
        with self._lock:
            elapsed = self.elapsed_seconds()
            self._clear_line()
            print(f"진행 시간: {format_duration(elapsed)}")
        return elapsed


def install(game_root: Path, hashes: dict[str, str], progress: ProgressTimer) -> None:
    progress.stage("[2/4] 한글 문장과 폰트로 패치 파일을 생성하는 중... (약 1분 소요)")
    with tempfile.TemporaryDirectory(prefix="guildrun-korean-") as temporary_root:
        payload_root = Path(temporary_root) / "payload"
        build_patch(game_root=game_root, output=payload_root)
        progress.stage("[3/4] 원본 게임 파일을 백업하는 중...")
        backup_dir, state = create_backup(game_root, hashes)
        progress.stage("[4/4] 한글 패치 파일을 게임 폴더에 적용하는 중...")
        replace_from_payload(game_root, payload_root, backup_dir, state)


def restore(game_root: Path) -> None:
    verify_game_root(game_root)
    backup_root = safe_path(game_root, ".guildrun-ko-backups")
    candidates = sorted((path for path in backup_root.glob("*") if path.is_dir()), reverse=True) if backup_root.is_dir() else []
    for backup_dir in candidates:
        state_path = backup_dir / "state.json"
        if not state_path.is_file():
            continue
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("status") not in {"installed", "failed_restored"}:
            continue
        for relative in SOURCE_FILES:
            source = safe_path(backup_dir, relative)
            if not source.is_file():
                raise RuntimeError(f"백업 파일이 없습니다: {relative.as_posix()}")
            destination = safe_path(game_root, relative)
            temporary = destination.with_name(destination.name + f".guildrun-ko-{uuid.uuid4().hex}.tmp")
            shutil.copy2(source, temporary)
            os.replace(temporary, destination)
        state["status"] = "restored"
        write_state(state_path, state)
        return
    raise RuntimeError("복원할 한글 패치 백업이 없습니다")


def choose_game_root(given: str | None) -> Path:
    if given:
        game_root = Path(given).expanduser().resolve()
        print("게임 경로 확인 완료.")
        return game_root
    if DEFAULT_GAME_ROOT.is_dir() and (DEFAULT_GAME_ROOT / "Guildrun.exe").is_file():
        print("기본 게임 경로 확인 완료.")
        return DEFAULT_GAME_ROOT
    print("기본 게임 경로를 찾지 못했습니다.")
    while True:
        answer = input("Guildrun Demo 게임 경로를 입력하세요: ").strip().strip('"')
        if not answer:
            raise RuntimeError("게임 경로를 입력하지 않아 종료합니다")
        game_root = Path(answer).expanduser().resolve()
        if game_root.is_dir() and (game_root / "Guildrun.exe").is_file():
            print("게임 경로 확인 완료.")
            return game_root
        print("Guildrun.exe가 있는 올바른 게임 폴더를 입력하세요.")


def set_warning_color() -> tuple[object, int] | None:
    """Set bright-green text in a Windows console and retain its original color."""
    if os.name != "nt":
        return None
    try:
        import ctypes

        class Coord(ctypes.Structure):
            _fields_ = [("x", ctypes.c_short), ("y", ctypes.c_short)]

        class SmallRect(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_short),
                ("top", ctypes.c_short),
                ("right", ctypes.c_short),
                ("bottom", ctypes.c_short),
            ]

        class ConsoleScreenBufferInfo(ctypes.Structure):
            _fields_ = [
                ("size", Coord),
                ("cursor_position", Coord),
                ("attributes", ctypes.c_ushort),
                ("window", SmallRect),
                ("maximum_window_size", Coord),
            ]

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        info = ConsoleScreenBufferInfo()
        if handle in (0, -1) or not kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(info)):
            return None
        original = int(info.attributes)
        bright_green = (original & 0xFFF0) | 0x000A
        kernel32.SetConsoleTextAttribute(handle, bright_green)
        return kernel32, original
    except Exception:
        return None


def restore_console_color(state: tuple[object, int] | None) -> None:
    if state is not None:
        kernel32, original = state
        kernel32.SetConsoleTextAttribute(kernel32.GetStdHandle(-11), original)


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def read_confirmation() -> str:
    if os.name == "nt" and sys.stdin.isatty():
        import msvcrt

        while True:
            print("계속하시겠습니까?  1. Yes  2. No : ", end="", flush=True)
            answer = msvcrt.getwch()
            if answer in {"1", "2"}:
                print(answer)
                return answer
            print("\n1 또는 2를 입력하세요.")
    while True:
        answer = input("계속하시겠습니까?  1. Yes  2. No : ").strip()
        if answer in {"1", "2"}:
            return answer
        print("1 또는 2를 입력하세요.")


def confirm_install() -> bool:
    color_state = set_warning_color()
    try:
        print(
            "\n[주의 사항]\n"
            "이 MOD는 비공식 한글 패치입니다. 사용에 따른 책임은 사용자 본인에게 있습니다.\n"
            "게임 파일은 백업한 뒤 교체되며, 게임 업데이트 후에는 호환성 확인이 필요합니다.\n"
            "번역은 AI를 활용했으며, 번역 데이터를 다른 MOD에 포함해 재배포하지 마세요.\n"
        )
        if read_confirmation() == "1":
            return True
        print("패치를 취소했습니다.")
        return False
    finally:
        restore_console_color(color_state)


def main() -> int:
    configure_console()
    parser = argparse.ArgumentParser(description="Guildrun Korean runtime patcher")
    parser.add_argument("--game-path")
    parser.add_argument("--action", choices=("install", "check", "restore"), default="install")
    parser.add_argument("--no-pause", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "install" and not confirm_install():
            return 0
        if args.action == "install":
            clear_screen()
        game_root = choose_game_root(args.game_path)
        print(f"Guildrun 한국어 패치 {RELEASE}")
        if args.action == "restore":
            print("원본 게임 파일을 복원하는 중...")
            restore(game_root)
            print("한글 패치 복원 완료.")
        elif args.action == "check":
            verify_source_files(game_root)
            print("[1/1] 호환성 테스트 완료.")
        else:
            progress = ProgressTimer()
            progress.start()
            try:
                hashes = verify_source_files(game_root)
                progress.stage("[1/4] 호환성 테스트 완료.")
                install(game_root, hashes, progress)
            finally:
                elapsed = progress.stop()
            print(f"Done. 한글 패치 완료. (총 소요 시간: {format_duration(elapsed)})")
    except Exception as error:
        print(f"한글 패치 실패: {error}")
        return 1
    finally:
        if not args.no_pause and getattr(sys, "frozen", False):
            input("계속하려면 Enter를 누르세요 . . .")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
