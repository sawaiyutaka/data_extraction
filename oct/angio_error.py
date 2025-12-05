#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
エラーマップCSVを読み込み、
大きなカテゴリー（Superior / Inferior / Nasal / Temporal / Center）を
ETDRS 9セクタ形式に展開し、

(1) 「1 を含むものだけ 1（それ以外は空欄）」 → *_contains1.csv
(2) 「2 または 9 を含むものだけ 1（それ以外は空欄）」 → *_contains2or9.csv

として出力するスクリプト。

入力CSVの想定形式（カンマ区切り）:
ID, L-Superior, L-Inferior, L-Nasal, L-Temporal, L-Center,
    R-Superior, R-Inferior, R-Temporal, R-Nasal, R-Center

※ヘッダーや値の前後にスペースがあってもOK（stripして扱う）
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional

# ==== 設定ここから ======================================================

# 入力CSVのパス
input_csv = Path(r"D:\ttc5oct\oct20251126\noise20angio.csv")  # ←ここを書き換えてください

# 出力CSV（① 1を含むものだけ1）
output_csv_contains1 = Path(r"D:\ttc5oct\oct20251126\error_map_contains1.csv")

# 出力CSV（② 2または9を含むものだけ1）
output_csv_contains2or9 = Path(r"D:\ttc5oct\oct20251126\error_map_contains2or9.csv")

# ======================================================================

# 最終出力カラム（ETDRS 9セクタの形）
OUTPUT_COLUMNS = [
    "ID",
    "R_Center", "R_Inner_Temporal", "R_Inner_Superior", "R_Inner_Nasal", "R_Inner_Inferior",
    "R_Outer_Temporal", "R_Outer_Superior", "R_Outer_Nasal", "R_Outer_Inferior",
    "L_Center", "L_Inner_Temporal", "L_Inner_Superior", "L_Inner_Nasal", "L_Inner_Inferior",
    "L_Outer_Temporal", "L_Outer_Superior", "L_Outer_Nasal", "L_Outer_Inferior",
]


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    """
    カンマ区切りCSVを読み込み、
    ヘッダーと各セルの前後の空白を strip した Dict のリストを返す。
    """
    # 文字コード自動トライ
    last_err = None
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
            break
        except UnicodeDecodeError as e:
            last_err = e
            rows = []
    else:
        # すべて失敗したら置換モードで読む
        with path.open("rb") as f:
            text = f.read().decode("utf-8", errors="replace")
        rows = list(csv.reader(text.splitlines()))

    if not rows:
        return []

    # 1行目をヘッダーとして使用（stripして正規化）
    raw_header = rows[0]
    header = [h.strip() for h in raw_header]

    dict_rows: List[Dict[str, str]] = []
    for r in rows[1:]:
        # 列数が足りない場合に備えてパディング
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))
        # 各セルも strip
        d = {header[i]: (r[i].strip() if i < len(r) else "") for i in range(len(header))}
        dict_rows.append(d)

    return dict_rows


def expand_to_etdrs_cells(row: Dict[str, str]) -> Dict[str, Optional[str]]:
    """
    大きな部位（L_Superior など）を、
    ETDRS 9セクタの小さな部位に展開した「生データ」を作る。

    例:
      L_Superior -> L_Inner_Superior, L_Outer_Superior
      R_Temporal -> R_Inner_Temporal, R_Outer_Temporal
    """
    out: Dict[str, Optional[str]] = {c: None for c in OUTPUT_COLUMNS}

    # IDをコピー
    out["ID"] = row.get("ID", "").strip()

    # 左眼
    l_sup = row.get("L_Superior", "").strip()
    l_inf = row.get("L_Inferior", "").strip()
    l_nas = row.get("L_Nasal", "").strip()
    l_tmp = row.get("L_Temporal", "").strip()
    l_ctr = row.get("L_Center", "").strip()

    # 右眼
    r_sup = row.get("R_Superior", "").strip()
    r_inf = row.get("R_Inferior", "").strip()
    r_nas = row.get("R_Nasal", "").strip()
    r_tmp = row.get("R_Temporal", "").strip()
    r_ctr = row.get("R_Center", "").strip()

    # --- 左眼をETDRSに展開 ---
    # Center
    out["L_Center"] = l_ctr or None

    # Temporal
    out["L_Inner_Temporal"] = l_tmp or None
    out["L_Outer_Temporal"] = l_tmp or None

    # Superior
    out["L_Inner_Superior"] = l_sup or None
    out["L_Outer_Superior"] = l_sup or None

    # Nasal
    out["L_Inner_Nasal"] = l_nas or None
    out["L_Outer_Nasal"] = l_nas or None

    # Inferior
    out["L_Inner_Inferior"] = l_inf or None
    out["L_Outer_Inferior"] = l_inf or None

    # --- 右眼をETDRSに展開 ---
    # Center
    out["R_Center"] = r_ctr or None

    # Temporal
    out["R_Inner_Temporal"] = r_tmp or None
    out["R_Outer_Temporal"] = r_tmp or None

    # Superior
    out["R_Inner_Superior"] = r_sup or None
    out["R_Outer_Superior"] = r_sup or None

    # Nasal
    out["R_Inner_Nasal"] = r_nas or None
    out["R_Outer_Nasal"] = r_nas or None

    # Inferior
    out["R_Inner_Inferior"] = r_inf or None
    out["R_Outer_Inferior"] = r_inf or None

    return out


def contains1(value: Optional[str]) -> str:
    """
    「1 を含む（'1', '12', '19' など）ものだけ 1、それ以外は空欄」
    """
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    return "1" if "1" in s else ""


def contains2or9(value: Optional[str]) -> str:
    """
    「2 または 9 を含む（'2', '9', '12', '19', '29' など）ものだけ 1、それ以外は空欄」
    """
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    return "1" if ("2" in s or "9" in s) else ""


def main():
    if not input_csv.exists():
        print(f"Error: 入力CSVが見つかりません → {input_csv}")
        return

    raw_rows = read_csv_rows(input_csv)
    if not raw_rows:
        print("入力CSVにデータ行がありません。")
        return

    # ① 大きな部位 → ETDRS 9セクタに展開（生データ）
    expanded_rows: List[Dict[str, Optional[str]]] = [
        expand_to_etdrs_cells(r) for r in raw_rows
    ]

    # ② contains1 / contains2or9 を適用して2種類の結果を作る
    rows_contains1: List[Dict[str, str]] = []
    rows_contains2or9: List[Dict[str, str]] = []

    for ex in expanded_rows:
        row1: Dict[str, str] = {}
        row2: Dict[str, str] = {}
        for col in OUTPUT_COLUMNS:
            if col == "ID":
                row1["ID"] = ex.get("ID") or ""
                row2["ID"] = ex.get("ID") or ""
            else:
                row1[col] = contains1(ex.get(col))
                row2[col] = contains2or9(ex.get(col))
        rows_contains1.append(row1)
        rows_contains2or9.append(row2)

    # 出力フォルダ作成
    output_csv_contains1.parent.mkdir(parents=True, exist_ok=True)
    output_csv_contains2or9.parent.mkdir(parents=True, exist_ok=True)

    # _contains1 を書き出し
    with output_csv_contains1.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows_contains1)

    # _contains2or9 を書き出し
    with output_csv_contains2or9.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows_contains2or9)

    print(f"完了: {len(expanded_rows)} 件を処理しました")
    print(f"  ・1を含むものだけ1 → {output_csv_contains1}")
    print(f"  ・2または9を含むものだけ1 → {output_csv_contains2or9}")


if __name__ == "__main__":
    main()
