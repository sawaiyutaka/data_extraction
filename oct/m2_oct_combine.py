#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETDRS集計CSV（新規: etdrs_aggregated.csv）と、同じ構造の既存CSVをIDでマージします。

マージのルール（セル単位）:
- old と new の両方に数値がある → new を優先
- old のみに数値がある         → old を残す
- new のみに数値がある         → new を採用
- 両方とも数値でない（空欄）   → 空欄のまま

行単位:
- その ID が old にしかいない      → old の行をそのまま使う
- その ID が new にしかいない      → new の行をそのまま使う
- 両方にいる                       → 上のセル単位ルールでマージ

PyCharmでそのまま実行可能:
1) 下の `new_csv_path` に 新しいCSVのパス
2) 下の `old_csv_path` に 既存CSVのパス
3) `output_csv_path` に 出力先ファイル名
4) ▶実行
"""

from __future__ import annotations
import csv
from pathlib import Path
from typing import Dict, List, Tuple

# ==== 設定 ================================================================
new_csv_path = Path(r"D:\ttc5oct\oct20251126\output20251125\m0_ALL-LAYERS_793_900_aggregated.csv")   # 新規CSV（優先）
old_csv_path = Path(r"D:\ttc5oct\oct20251126\output20251125\m0_ALL-LAYERS_001_792_aggregated.csv")     # 既存の同構造CSV（統合元）
output_csv_path = Path(r"D:\ttc5oct\oct20251126\output20251125\m0_ALL-LAYERS_aggregated.csv")    # 出力ファイル
# =========================================================================

ENCODINGS = ("utf-8-sig", "cp932", "utf-8")


def read_csv_any_encoding(path: Path) -> Tuple[List[str], List[List[str]]]:
    """ヘッダ+データ行を返す。エンコーディングは候補で順次トライ。"""
    for enc in ENCODINGS:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
                if not rows:
                    return [], []
                header = rows[0]
                data = rows[1:]
                return header, data
        except UnicodeDecodeError:
            continue
    # 最後のフォールバック
    with path.open("rb") as f:
        text = f.read().decode("utf-8", errors="replace")
    reader = csv.reader(text.splitlines())
    rows = list(reader)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def to_dicts(header: List[str], data: List[List[str]]) -> List[Dict[str, str]]:
    """行リストを Dict のリストへ（ヘッダ名→値）。欠損列は "" で補完。"""
    idx = {i: h for i, h in enumerate(header)}
    out: List[Dict[str, str]] = []
    for row in data:
        d: Dict[str, str] = {}
        for i, val in enumerate(row):
            h = idx.get(i)
            if h is None:
                continue
            d[h] = val
        # 欠落列を空文字で補完
        for h in header:
            if h not in d:
                d[h] = ""
        out.append(d)
    return out


def union_columns(h1: List[str], h2: List[str]) -> List[str]:
    """列のユニオン。IDを先頭に、残りはh1の順→h2で未出の列、の順。"""
    def norm(cols: List[str]) -> List[str]:
        return [c for c in cols if c and c.strip()]

    a = norm(h1)
    b = norm(h2)

    cols: List[str] = []
    # ID を先頭に
    if "ID" in a or "ID" in b:
        cols.append("ID")

    # まず new 側の列を順に
    for c in a:
        if c == "ID":
            continue
        if c not in cols:
            cols.append(c)

    # old 側でまだ出ていない列を追加
    for c in b:
        if c == "ID":
            continue
        if c not in cols:
            cols.append(c)

    return cols


def index_by_id(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """ID をキーにした dict に変換。ID が空行は無視。"""
    idx: Dict[str, Dict[str, str]] = {}
    for d in rows:
        key = d.get("ID", "").strip()
        if not key:
            continue
        idx[key] = d
    return idx


def ensure_columns(d: Dict[str, str], columns: List[str]) -> Dict[str, str]:
    """指定された列セットを持つ dict に整形（欠損列は ""）。"""
    return {c: d.get(c, "") for c in columns}


def is_number_str(s: str) -> bool:
    """数値なら True、空欄なら False、それ以外も False."""
    if s is None:
        return False
    t = str(s).strip()
    if t == "":
        return False
    try:
        float(t)
        return True
    except ValueError:
        return False


def merge_rows_cellwise(
    old_row: Dict[str, str],
    new_row: Dict[str, str],
    columns: List[str],
) -> Dict[str, str]:
    """
    1つのIDについて、旧行と新行をセル単位でマージする。

    要件:
    - old or new どちらか一方だけが数値 → その数値を残す
    - old と new 両方数値 → new を優先
    - old, new とも空欄 → 空欄のまま
    """
    merged: Dict[str, str] = {}

    for col in columns:
        if col == "ID":
            # ID は新→旧の順で埋める
            merged[col] = (new_row.get(col) or old_row.get(col) or "").strip()
            continue

        old_val = (old_row.get(col) or "").strip()
        new_val = (new_row.get(col) or "").strip()

        old_is_num = is_number_str(old_val)
        new_is_num = is_number_str(new_val)

        if old_is_num and new_is_num:
            # 両方数値 → 新
            merged[col] = new_val
        elif old_is_num and not new_is_num:
            # 旧だけ数値 → 旧
            merged[col] = old_val
        elif not old_is_num and new_is_num:
            # 新だけ数値 → 新
            merged[col] = new_val
        else:
            # 両方空欄 or 非数値（今回は空欄しか来ない前提） → 空欄
            merged[col] = ""

    return merged


def merge_csv(new_path: Path, old_path: Path, out_path: Path) -> None:
    # 読み込み
    new_header, new_data = read_csv_any_encoding(new_path)
    old_header, old_data = read_csv_any_encoding(old_path)

    new_dicts = to_dicts(new_header, new_data)
    old_dicts = to_dicts(old_header, old_data)

    # 列定義: new の並びを優先しつつ、old だけの列も後ろに足す
    columns = union_columns(new_header, old_header)

    # ID -> 行 に変換
    new_by_id = index_by_id(new_dicts)
    old_by_id = index_by_id(old_dicts)

    # 全IDの集合
    all_ids = sorted(set(old_by_id.keys()) | set(new_by_id.keys()))

    merged_by_id: Dict[str, Dict[str, str]] = {}

    for id_ in all_ids:
        old_row = old_by_id.get(id_)
        new_row = new_by_id.get(id_)

        if old_row is None and new_row is not None:
            # new にだけ存在 → new をそのまま
            merged_by_id[id_] = ensure_columns(new_row, columns)
        elif old_row is not None and new_row is None:
            # old にだけ存在 → old をそのまま
            merged_by_id[id_] = ensure_columns(old_row, columns)
        else:
            # 両方に存在 → セル単位でマージ
            merged_by_id[id_] = merge_rows_cellwise(
                ensure_columns(old_row, columns),
                ensure_columns(new_row, columns),
                columns,
            )

    # ID昇順で出力
    ordered_ids = sorted(merged_by_id.keys())
    out_rows: List[Dict[str, str]] = [merged_by_id[i] for i in ordered_ids]

    # 書き出し
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(out_rows)

    print(
        f"OK: merged {len(old_by_id)} (old IDs) + {len(new_by_id)} (new IDs) "
        f"-> {len(out_rows)} unique IDs → {out_path}"
    )


if __name__ == "__main__":
    if not new_csv_path.exists():
        print(f"Error: 新規CSVが見つかりません → {new_csv_path}")
    elif not old_csv_path.exists():
        print(f"Error: 既存CSVが見つかりません → {old_csv_path}")
    else:
        merge_csv(new_csv_path, old_csv_path, output_csv_path)
