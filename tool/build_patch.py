from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import unity_patch
import UnityPy
from game_layout import SUPPORTED_PLATFORMS, detect_game_layout

TOOL_ROOT = Path(__file__).resolve().parent
MAIN_ROOT = (
    Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    if getattr(sys, "frozen", False)
    else TOOL_ROOT.parent
)
ROOT = MAIN_ROOT
RESOURCE_ROOT = MAIN_ROOT / "resource"
GAME_ROOT = RESOURCE_ROOT
FONT_ROOT = RESOURCE_ROOT / "fonts"
FONT_CONFIG = FONT_ROOT / "font-config.json"
VERSION_PATH = RESOURCE_ROOT / "version.json"
VERSION = json.loads(VERSION_PATH.read_text(encoding="utf-8"))
for required_version_key in ("game", "game_version", "target_build", "release"):
    if (
        not isinstance(VERSION.get(required_version_key), str)
        or not VERSION[required_version_key]
    ):
        raise RuntimeError(f"Invalid version.json field: {required_version_key}")
RELEASE = VERSION["release"]
GAME_VERSION = VERSION["game_version"]
TARGET_BUILD = VERSION["target_build"]
OUTPUT_ROOT = ROOT / "artifacts" / f"Guildrun-Korean-Port-{RELEASE}"

OLD_LOCALE_NAME = "中文（简体）"
NEW_LOCALE_NAME = "한국어（MOD）"


def language_table_trees(path: Path) -> dict[int, dict[str, Any]]:
    tables = unity_patch.language_objects(UnityPy.load(path.read_bytes()))
    return {shared_id: tree for shared_id, (_, tree) in tables.items()}


def load_font_data(
    font_root: Path, config_path: Path
) -> tuple[dict[str, bytes], dict[str, Any]]:
    font_config = json.loads(config_path.read_text(encoding="utf-8"))
    required_keys = {"asset_name_pattern", "expected_count", "weight_files"}
    if not required_keys <= font_config.keys() or not isinstance(
        font_config["weight_files"], dict
    ):
        raise RuntimeError(f"Invalid font config: {config_path}")
    fonts: dict[str, bytes] = {}
    for filename in {str(name) for name in font_config["weight_files"].values()}:
        path = font_root / filename
        data = path.read_bytes()
        if not data:
            raise RuntimeError(f"Korean font is empty: {path}")
        fonts[filename] = data
    return fonts, font_config


def write_readme(output: Path, report: dict[str, Any]) -> None:
    destination = "Guildrun Demo 설치 폴더"
    (output / "README.md").write_text(
        "# Guildrun Korean port\n\n"
        "Generated from the current Steam installation while preserving its current "
        "Addressables catalog format.\n\n"
        f"Platform: `{report['platform']}`. Copy the generated files into the "
        f"{destination}. Then select `한국어（MOD）` in Settings > Language. "
        "Use Steam's file integrity "
        "verification to remove the patch.\n\n"
        "Generated-file report: `report.json`.\n"
        f"Translated legacy IDs: {report['legacy_translation_ids']}.\n"
        f"Current zh-Hans string tables: {report['current_bundle_tables']}.\n",
        encoding="utf-8",
    )


def build_patch(
    game_root: Path,
    output: Path,
    translations_path: Path = RESOURCE_ROOT / "guildrun-korean-source.json",
    font_root: Path = FONT_ROOT,
    font_config_path: Path = FONT_CONFIG,
    platform: str | None = None,
) -> dict[str, Any]:
    """Generate four patched files in ``output`` without changing ``game_root``."""
    layout = detect_game_layout(game_root, platform)
    game_root = layout.install_root
    font_root = font_root.resolve()
    font_config_path = font_config_path.resolve()
    translations_path = translations_path.resolve()
    output = output.resolve()
    required = [
        layout.path_for(key) for key in ("resources", "metadata", "catalog", "target")
    ] + [
        translations_path,
        font_config_path,
    ]
    if font_config_path.is_file():
        config = json.loads(font_config_path.read_text(encoding="utf-8"))
        if isinstance(config.get("weight_files"), dict):
            required.extend(
                font_root / str(filename)
                for filename in set(config["weight_files"].values())
            )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("Required files are missing:\n" + "\n".join(missing))
    if len(OLD_LOCALE_NAME.encode("utf-8")) != len(NEW_LOCALE_NAME.encode("utf-8")):
        raise RuntimeError(
            "The Korean locale display name must preserve the metadata byte length"
        )

    current_target = layout.path_for("target")
    source_json = json.loads(translations_path.read_text(encoding="utf-8-sig"))
    for version_key in ("game", "game_version", "target_build"):
        if source_json.get(version_key) != VERSION[version_key]:
            raise RuntimeError(
                f"Translation JSON {version_key} does not match version.json"
            )
    translations: dict[int, dict[str, Any]] = {}
    for entry in source_json["entries"]:
        entry_id = int(entry["id"])
        if (
            entry_id in translations
            or not isinstance(entry["korean"], str)
            or "shared_table_id" not in entry
        ):
            raise RuntimeError(f"Invalid or duplicate translation: {entry_id}")
        translations[entry_id] = {
            "korean": entry["korean"],
            "shared_table_id": int(entry["shared_table_id"]),
            "metadata": entry.get("metadata", {"m_Items": []}),
        }
    if source_json.get("entry_count") != len(translations):
        raise RuntimeError("translation JSON entry_count does not match its entries")
    current_table_ids = set(language_table_trees(current_target))
    translation_table_ids = {
        entry["shared_table_id"] for entry in translations.values()
    }
    if current_table_ids != translation_table_ids:
        raise RuntimeError(
            "Translation JSON tables do not match the current zh-Hans bundle: "
            f"missing={len(current_table_ids - translation_table_ids)}, "
            f"unexpected={len(translation_table_ids - current_table_ids)}"
        )

    bundle_output = output / layout.source_files["target"]
    resources_output = output / layout.source_files["resources"]
    metadata_output = output / layout.source_files["metadata"]
    catalog_output = output / layout.source_files["catalog"]
    for target in (bundle_output, resources_output, metadata_output, catalog_output):
        target.parent.mkdir(parents=True, exist_ok=True)

    translation_report = unity_patch.build_translation_bundle(
        current_target,
        bundle_output,
        translations,
        "zh-Hans",
    )
    fonts, font_config = load_font_data(font_root, font_config_path)
    font_report = unity_patch.build_resources(
        layout.path_for("resources"), resources_output, fonts, font_config
    )
    metadata_report = unity_patch.build_metadata(
        layout.path_for("metadata"), metadata_output, OLD_LOCALE_NAME, NEW_LOCALE_NAME
    )
    catalog_report = unity_patch.build_catalog(
        layout.path_for("catalog"),
        current_target,
        bundle_output,
        catalog_output,
        layout.source_files["target"].name,
        256,
    )
    report = {
        "source_game": str(game_root),
        "platform": layout.platform,
        "translation_source": str(translations_path),
        "font_source": str(font_root),
        "target_locale_name": NEW_LOCALE_NAME,
        "legacy_translation_ids": sum(
            e.get("source") == "legacy_patch" for e in source_json["entries"]
        ),
        "additional_translated_ids": sum(
            e.get("source") == "manual_current" for e in source_json["entries"]
        ),
        "json_translation_ids": len(translations),
        "current_bundle_tables": len(current_table_ids),
        "translation": translation_report,
        "fonts": font_report,
        "metadata": metadata_report,
        "catalog": catalog_report,
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the Guildrun Korean patch from a local game installation."
    )
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--platform", choices=SUPPORTED_PLATFORMS)
    parser.add_argument("--font-root", type=Path, default=FONT_ROOT)
    parser.add_argument("--font-config", type=Path, default=FONT_CONFIG)
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    parser.add_argument(
        "--translations",
        type=Path,
        default=RESOURCE_ROOT / "guildrun-korean-source.json",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate the generated files in an existing output folder.",
    )
    args = parser.parse_args()
    if args.output.resolve().exists() and not args.overwrite:
        raise RuntimeError(
            f"Output already exists; refusing to overwrite: {args.output.resolve()}"
        )
    report = build_patch(
        game_root=args.game_root,
        output=args.output,
        translations_path=args.translations,
        font_root=args.font_root,
        font_config_path=args.font_config,
        platform=args.platform,
    )
    write_readme(args.output.resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
