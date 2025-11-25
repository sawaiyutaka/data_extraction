#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETDRS集計CSV（新規: etdrs_aggregated.csv）と、同じ構造の既存CSVをIDでマージします。
重複IDがある場合は **新規CSV(=etdrs側)** を優先します。

PyCharmでそのまま実行可能:
1) 下の `new_csv_path` に etdrs_aggregated.csv のパス
2) 下の `old_csv_path` に 既存(別の人が作成)CSV のパス
3) `output_csv_path` に 出力先ファイル名
4) ▶実行
"""
from __future__ import annotations
import csv
from pathlib import Path
from typing import Dict, List, Tuple

# ==== 設定 ================================================================
new_csv_path = Path(r"./macular_all_layers_001_792.csv")   # 先ほど出力した新規CSV（優先）
old_csv_path = Path(r"./macular_all_layers_793_910.csv")     # 既存の同構造CSV（統合元）
output_csv_path = Path(r"./macular_all_layers_merged.csv")    # 出力ファイル
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
    idx = {i: h for i, h in enumerate(header)}
    out: List[Dict[str, str]] = []
    for row in data:
        d: Dict[str, str] = {}
        for i, val in enumerate(row):
            h = idx.get(i)
            if h is None:
                continue
            d[h] = val
        # 欠落列は空文字で補完
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

    # IDを先頭に固定
    cols: List[str] = []
    if "ID" in a or "ID" in b:
        cols.append("ID")
    # a優先で追加
    for c in a:
        if c == "ID":
            continue
        if c not in cols:
            cols.append(c)
    # bの未出列を後置
    for c in b:
        if c == "ID":
            continue
        if c not in cols:
            cols.append(c)
    return cols


def index_by_id(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    idx: Dict[str, Dict[str, str]] = {}
    for d in rows:
        key = d.get("ID", "").strip()
        if not key:
            # IDが空の行はスキップ
            continue
        idx[key] = d
    return idx


def ensure_columns(d: Dict[str, str], columns: List[str]) -> Dict[str, str]:
    return {c: d.get(c, "") for c in columns}


def merge_csv(new_path: Path, old_path: Path, out_path: Path) -> None:
    # 読み込み
    new_header, new_data = read_csv_any_encoding(new_path)
    old_header, old_data = read_csv_any_encoding(old_path)

    new_dicts = to_dicts(new_header, new_data)
    old_dicts = to_dicts(old_header, old_data)

    # 列定義: 新規の並びを優先しつつ、旧にしかない列も後ろに付ける
    columns = union_columns(new_header, old_header)

    # インデックス化
    new_by_id = index_by_id(new_dicts)
    old_by_id = index_by_id(old_dicts)

    # マージ: 旧→ベース、その上から新規で上書き（新規優先）
    merged_by_id = dict(old_by_id)
    merged_by_id.update(new_by_id)

    # 出力順: ID昇順（必要に応じて変更可）
    ordered_ids = sorted(merged_by_id.keys())
    out_rows: List[Dict[str, str]] = [ensure_columns(merged_by_id[i], columns) for i in ordered_ids]

    # 書き出し（UTF-8）
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"OK: merged {len(old_by_id)} (old) + {len(new_by_id)} (new) -> {len(out_rows)} rows → {out_path}")


if __name__ == "__main__":
    # 入力存在チェック
    if not new_csv_path.exists():
        print(f"Error: 新規CSVが見つかりません → {new_csv_path}")
    elif not old_csv_path.exists():
        print(f"Error: 既存CSVが見つかりません → {old_csv_path}")
    else:
        merge_csv(new_csv_path, old_csv_path, output_csv_path)
