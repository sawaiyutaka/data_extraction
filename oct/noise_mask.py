#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統合済みETDRS CSVに、ノイズ記録CSVを適用して該当領域を欠損値（空欄）に置き換えるスクリプト。

前提:
- 統合CSV(例: merged_etdrs.csv) は列に ID, R-*, L-* を持つ（Center / Inner_*, Outer_* を含む）
- ノイズCSVは下記列を持つ:
  ID, L-Superior, L-Inferior, L-Nasal, L-Temporal, L-Center,
      R-Superior, R-Inferior, R-Temporal, R-Nasal, R-Center
- ノイズCSVで "1" または 全角 "１" が入っている領域を欠損にします（"0" や空欄は無視）。
- Inferior/Superior/Nasal/Temporal にノイズがある場合、Inner_* と Outer_* の両方を欠損にします。
  例: L-Inferior=1 → L-Inner_Inferior と L-Outer_Inferior の両方を空欄に。

PyCharmでの使い方:
1) 下のパス設定を編集
2) ▶ 実行
"""
from __future__ import annotations
import csv
from pathlib import Path
from typing import Dict, List, Tuple

# ===== パス設定 ============================================================
merged_csv_path = Path(r"./macular_all_layers_merged.csv")      # ノイズ適用対象（先ほど統合したCSV）
noise_csv_path  = Path(r"./oct20noise.csv")       # ノイズ記録CSV
output_csv_path = Path(r"./5wave_macular_all_layers.csv")  # 出力先
# ==========================================================================

ENCODINGS = ("utf-8-sig", "cp932", "utf-8")

NOISE_COLUMNS = [
    "ID",
    "L-Superior","L-Inferior","L-Nasal","L-Temporal","L-Center",
    "R-Superior","R-Inferior","R-Temporal","R-Nasal","R-Center",
]

# ノイズ → 欠損にする対象列のマッピング
# Center は Center のみ、他の4象限は Inner_*, Outer_* の両方
TARGETS = {}
for eye in ("L", "R"):
    for quad in ("Superior", "Inferior", "Nasal", "Temporal"):
        TARGETS[f"{eye}-{quad}"] = [f"{eye}-Inner_{quad}", f"{eye}-Outer_{quad}"]
    TARGETS[f"{eye}-Center"] = [f"{eye}-Center"]


def read_csv_any(path: Path) -> Tuple[List[str], List[List[str]]]:
    for enc in ENCODINGS:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                rows = list(csv.reader(f))
                if not rows:
                    return [], []
                return rows[0], rows[1:]
        except UnicodeDecodeError:
            continue
    with path.open("rb") as f:
        text = f.read().decode("utf-8", errors="replace")
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        return [], []
    return rows[0], rows[1:]


def to_dicts(header: List[str], data: List[List[str]]) -> List[Dict[str, str]]:
    idx = {i: h for i, h in enumerate(header)}
    out: List[Dict[str, str]] = []
    for row in data:
        d: Dict[str, str] = {idx[i]: (row[i] if i < len(row) else "") for i in idx}
        out.append(d)
    return out


def index_by_id(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {r.get("ID", "").strip(): r for r in rows if r.get("ID", "").strip()}


def is_noise(val: str) -> bool:
    v = (val or "").strip()
    return v == "1" or v == "１"  # 全角にも対応


def apply_noise_mask(merged_rows: List[Dict[str, str]], noise_rows: List[Dict[str, str]]) -> int:
    by_id = index_by_id(merged_rows)
    masked_cells = 0
    for n in noise_rows:
        pid = (n.get("ID", "") or "").strip()
        if not pid:
            continue
        if pid not in by_id:
            # ノイズ側にだけ存在するIDはスキップ（必要なら新規作成も可）
            continue
        tgt_row = by_id[pid]
        # 各ノイズ列をチェック
        for key, targets in TARGETS.items():
            if key in n and is_noise(n[key]):
                for col in targets:
                    if col in tgt_row and tgt_row[col] != "":
                        tgt_row[col] = ""  # 欠損（空欄）
                        masked_cells += 1
    return masked_cells


def ensure_all_columns(rows: List[Dict[str, str]], header: List[str]) -> List[str]:
    """出力ヘッダ: 既存ヘッダの順を尊重。欠落列は末尾に追加。"""
    # 既存ヘッダをベース
    cols = [c for c in header if c]
    # 行の中にあってヘッダにない列があれば追加
    for r in rows:
        for k in r.keys():
            if k and k not in cols:
                cols.append(k)
    return cols


def main():
    if not merged_csv_path.exists():
        print(f"Error: 統合CSVが見つかりません → {merged_csv_path}")
        return
    if not noise_csv_path.exists():
        print(f"Error: ノイズCSVが見つかりません → {noise_csv_path}")
        return

    m_header, m_data = read_csv_any(merged_csv_path)
    n_header, n_data = read_csv_any(noise_csv_path)

    merged_dicts = to_dicts(m_header, m_data)
    noise_dicts = to_dicts(n_header, n_data)

    masked = apply_noise_mask(merged_dicts, noise_dicts)

    out_header = ensure_all_columns(merged_dicts, m_header)

    # 書き出し
    with output_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_header)
        writer.writeheader()
        for r in merged_dicts:
            writer.writerow({c: r.get(c, "") for c in out_header})

    print(f"OK: masked {masked} cells → {output_csv_path}")


if __name__ == "__main__":
    main()
