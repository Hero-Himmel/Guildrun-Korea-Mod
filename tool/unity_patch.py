"""Minimal Unity binary operations required to build the Guildrun Korean patch."""
from __future__ import annotations

import hashlib
import copy
import re
import struct
import zlib
from pathlib import Path
from typing import Any

import UnityPy
from UnityPy.enums import ArchiveFlags
from UnityPy.streams import EndianBinaryReader


class PatchCompatibilityError(RuntimeError):
    """Raised when a game file does not match the supported Unity layout."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def root_file(env: Any) -> Any:
    files = list(env.files.values())
    if len(files) != 1:
        raise PatchCompatibilityError(f"Unity 루트 파일 수가 예상과 다릅니다: {len(files)}")
    return files[0]


def root_bundle(env: Any) -> Any:
    root = root_file(env)
    if root.__class__.__name__ != "BundleFile":
        raise PatchCompatibilityError(f"AssetBundle이 아닙니다: {root.__class__.__name__}")
    return root


def language_objects(env: Any) -> dict[int, tuple[Any, dict[str, Any]]]:
    """Return string-table MonoBehaviours keyed by their shared table ID."""
    result: dict[int, tuple[Any, dict[str, Any]]] = {}
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            tree = obj.read_typetree()
        except Exception:
            continue
        if "m_TableData" not in tree or "m_SharedData" not in tree:
            continue
        shared_id = int(tree["m_SharedData"]["m_PathID"])
        if shared_id in result:
            raise PatchCompatibilityError(f"문자열 테이블 참조가 중복됩니다: {shared_id}")
        result[shared_id] = (obj, tree)
    if not result:
        raise PatchCompatibilityError("문자열 테이블을 찾지 못했습니다")
    return result


def build_translation_bundle(
    source_bundle: Path,
    output: Path,
    translations: dict[int, dict[str, Any]],
    target_locale_code: str,
) -> dict[str, Any]:
    """Build every string-table row from the Korean JSON map.

    The zh-Hans bundle supplies the Unity table containers; the JSON supplies
    every current row ID, table ID, and Korean text. This permits newer English
    rows and retired Chinese rows without reading the English bundle.
    """
    env = UnityPy.load(source_bundle.read_bytes())
    tables = language_objects(env)
    expected_output: dict[int, dict[str, Any]] = {}
    grouped: dict[int, list[tuple[int, str, dict[str, Any]]]] = {
        shared_id: [] for shared_id in tables
    }

    for entry_id, translation in translations.items():
        table_id = int(translation["shared_table_id"])
        korean = translation["korean"]
        metadata = translation.get("metadata", {"m_Items": []})
        if table_id not in grouped:
            raise PatchCompatibilityError(f"번역 JSON의 문자열 테이블이 없습니다: {table_id}")
        if not isinstance(korean, str) or not korean:
            raise PatchCompatibilityError(f"비어 있거나 잘못된 번역입니다: {entry_id}")
        if not isinstance(metadata, dict) or not isinstance(metadata.get("m_Items"), list):
            raise PatchCompatibilityError(f"잘못된 문자열 메타데이터입니다: {entry_id}")
        grouped[table_id].append((entry_id, korean, metadata))
        expected_output[entry_id] = {"korean": korean, "metadata": metadata}

    for shared_id, (obj, tree) in tables.items():
        existing_rows = tree["m_TableData"]
        if not existing_rows:
            raise PatchCompatibilityError(f"행 템플릿이 없는 문자열 테이블입니다: {shared_id}")
        template = copy.deepcopy(existing_rows[0])
        rows = []
        for entry_id, korean, metadata in sorted(grouped[shared_id]):
            row = copy.deepcopy(template)
            row["m_Id"] = entry_id
            row["m_Localized"] = korean
            row["m_Metadata"] = copy.deepcopy(metadata)
            rows.append(row)
        tree["m_TableData"] = rows
        tree["m_LocaleId"]["m_Code"] = target_locale_code
        obj.save_typetree(tree)

    output.write_bytes(root_bundle(env).save(packer="lz4"))
    verify_env = UnityPy.load(output.read_bytes())
    actual: dict[int, dict[str, Any]] = {}
    for _, tree in language_objects(verify_env).values():
        if tree["m_LocaleId"]["m_Code"] != target_locale_code:
            raise RuntimeError("생성 후 언어 코드가 일치하지 않습니다")
        for entry in tree["m_TableData"]:
            entry_id = int(entry["m_Id"])
            if entry_id in actual:
                raise RuntimeError(f"생성 후 문자열 ID가 중복됩니다: {entry_id}")
            actual[entry_id] = {
                "korean": entry.get("m_Localized", ""),
                "metadata": entry.get("m_Metadata", {"m_Items": []}),
            }
    if actual != expected_output:
        raise RuntimeError("생성 후 번들이 번역 JSON과 일치하지 않습니다")
    return {"rows": len(actual), "sha256": sha256(output.read_bytes())}


def build_resources(
    source: Path,
    output: Path,
    fonts: dict[str, bytes],
    font_config: dict[str, Any],
) -> dict[str, Any]:
    asset_pattern = str(font_config["asset_name_pattern"])
    weight_files = {str(k): str(v) for k, v in font_config["weight_files"].items()}
    expected_count = int(font_config["expected_count"])
    env = UnityPy.load(source.read_bytes())
    expected: dict[int, tuple[str, bytes]] = {}
    for obj in env.objects:
        if obj.type.name != "Font":
            continue
        tree = obj.read_typetree()
        name = tree.get("m_Name", "")
        match = re.fullmatch(asset_pattern, name)
        if not match:
            continue
        weight = match.group(1)
        font_name = weight_files.get(weight)
        if font_name is None:
            raise PatchCompatibilityError(f"지원하지 않는 폰트 웨이트입니다: {name}")
        font_data = fonts.get(font_name)
        if not font_data:
            raise PatchCompatibilityError(f"필요한 폰트 파일이 없습니다: {font_name}")
        tree["m_FontData"] = font_data
        obj.save_typetree(tree)
        expected[int(obj.path_id)] = (name, font_data)
    if len(expected) != expected_count:
        raise PatchCompatibilityError(
            f"교체할 폰트 수가 다릅니다: {len(expected)} / {expected_count}"
        )

    output.write_bytes(root_file(env).save())
    verify_env = UnityPy.load(output.read_bytes())
    checked = 0
    for obj in verify_env.objects:
        expected_font = expected.get(int(obj.path_id))
        if expected_font is None:
            continue
        if bytes(obj.read_typetree().get("m_FontData", b"")) != expected_font[1]:
            raise RuntimeError(f"생성 후 폰트 검증 실패: {expected_font[0]}")
        checked += 1
    if checked != expected_count:
        raise RuntimeError(f"생성 후 폰트 수가 다릅니다: {checked} / {expected_count}")
    return {"fonts": checked, "sha256": sha256(output.read_bytes())}


def build_metadata(
    source: Path, output: Path, old_locale_name: str, new_locale_name: str
) -> dict[str, Any]:
    data = bytearray(source.read_bytes())
    old = old_locale_name.encode("utf-8")
    new = new_locale_name.encode("utf-8")
    if len(old) != len(new):
        raise PatchCompatibilityError("기존/새 언어명 UTF-8 길이가 다릅니다")
    old_count = data.count(old)
    new_count = data.count(new)
    if old_count == 1 and new_count == 0:
        offset = data.find(old)
        data[offset : offset + len(old)] = new
        state = "patched"
    elif old_count == 0 and new_count == 1:
        offset = data.find(new)
        state = "already_patched"
    else:
        raise PatchCompatibilityError(
            f"언어명을 한 곳에서 찾지 못했습니다: old={old_count}, new={new_count}"
        )
    output.write_bytes(data)
    return {"state": state, "offset": offset, "sha256": sha256(bytes(data))}


def unity_bundle_crc(path: Path) -> int:
    raw = path.read_bytes()
    bundle = root_bundle(UnityPy.load(raw))
    reader = EndianBinaryReader(raw)
    reader.read_string_to_null()
    reader.read_u_int()
    reader.read_string_to_null()
    reader.read_string_to_null()
    reader.read_long()
    compressed_size = reader.read_u_int()
    uncompressed_size = reader.read_u_int()
    reader.read_u_int()
    if bundle._uses_block_alignment:
        reader.align_stream(16)
    start = reader.Position
    if int(bundle.dataflags) & int(ArchiveFlags.BlocksInfoAtTheEnd):
        reader.Position = reader.Length - compressed_size
        compressed_info = reader.read_bytes(compressed_size)
        reader.Position = start
        data_start = start
    else:
        compressed_info = reader.read_bytes(compressed_size)
        if int(bundle.dataflags) & 0x200:
            reader.align_stream(16)
        data_start = reader.Position
    info_data = bundle.decompress_data(compressed_info, uncompressed_size, bundle.dataflags)
    info_reader = EndianBinaryReader(info_data)
    info_reader.read_bytes(16)
    blocks = [
        (info_reader.read_u_int(), info_reader.read_u_int(), info_reader.read_u_short())
        for _ in range(info_reader.read_int())
    ]
    reader.Position = data_start
    crc = 0
    for index, (raw_size, packed_size, flags) in enumerate(blocks):
        crc = zlib.crc32(
            bundle.decompress_data(reader.read_bytes(packed_size), raw_size, flags, index), crc
        )
    return crc & 0xFFFFFFFF


def build_catalog(
    source: Path,
    current_bundle: Path,
    new_bundle: Path,
    output: Path,
    target_bundle_name: str,
    crc_search_bytes: int = 256,
) -> dict[str, Any]:
    data = bytearray(source.read_bytes())
    name = target_bundle_name.encode("ascii")
    if data.count(name) != 1:
        raise PatchCompatibilityError(f"카탈로그의 대상 번들을 식별할 수 없습니다: {data.count(name)}")
    old_crc = unity_bundle_crc(current_bundle)
    new_crc = unity_bundle_crc(new_bundle)
    search_start = data.find(name) + len(name)
    search_end = min(len(data), search_start + crc_search_bytes)
    old_bytes = struct.pack("<I", old_crc)
    offsets: list[int] = []
    position = data.find(old_bytes, search_start, search_end)
    while position >= 0:
        offsets.append(position)
        position = data.find(old_bytes, position + 1, search_end)
    if len(offsets) != 1:
        raise PatchCompatibilityError(f"기존 번들 CRC를 식별할 수 없습니다: {old_crc:08x}")
    offset = offsets[0]
    data[offset : offset + 4] = struct.pack("<I", new_crc)
    output.write_bytes(data)
    if output.read_bytes()[offset : offset + 4] != struct.pack("<I", new_crc):
        raise RuntimeError("생성 후 카탈로그 CRC 검증 실패")
    return {
        "old_crc": f"{old_crc:08x}",
        "new_crc": f"{new_crc:08x}",
        "offset": offset,
        "sha256": sha256(bytes(data)),
    }
