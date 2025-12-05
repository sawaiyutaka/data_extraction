#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
error_mode1_contains1.csv を読み込み、
✔ ひとつ以上エラーを含むID
✔ 全領域エラー（完全欠損）
✔ 右眼のみ全領域エラー
✔ 左眼のみ全領域エラー
の人数と割合を集計する
"""

import csv
from pathlib import Path

# ====== 設定：エラーCSVのパス ======
err_csv = Path(r"D:\ttc5oct\oct20251126\output20251125\vd_error_map_contains2or9.csv")

# ETDRS 9領域
R_COLS = [
    "R_Center", "R_Inner_Temporal", "R_Inner_Superior", "R_Inner_Nasal",
    "R_Inner_Inferior", "R_Outer_Temporal", "R_Outer_Superior",
    "R_Outer_Nasal", "R_Outer_Inferior"
]

L_COLS = [
    "L_Center", "L_Inner_Temporal", "L_Inner_Superior", "L_Inner_Nasal",
    "L_Inner_Inferior", "L_Outer_Temporal", "L_Outer_Superior",
    "L_Outer_Nasal", "L_Outer_Inferior"
]

ALL_COLS = R_COLS + L_COLS  # 18領域


def read_csv(path: Path):
    """CSVを読み込んで辞書のリストで返す"""
    data = []
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            with path.open("r", encoding=enc) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    clean = {k.strip(): (v.strip() if v else "") for k, v in row.items()}
                    data.append(clean)
            break
        except UnicodeDecodeError:
            data = []
            continue
    return data


def main():
    rows = read_csv(err_csv)
    if not rows:
        print("error CSV にデータがありません")
        return

    total_n = len(rows)

    ids_has_any_error = []        # ひとつ以上エラー
    ids_complete_missing = []     # 両眼とも完全欠損（全18領域 =1）
    ids_right_only_missing = []   # 右眼のみ完全欠損
    ids_left_only_missing = []    # 左眼のみ完全欠損

    for row in rows:
        id_ = row.get("ID", "")

        # 各部位の値を取得
        vals_all = [row.get(c, "") for c in ALL_COLS]
        vals_r = [row.get(c, "") for c in R_COLS]
        vals_l = [row.get(c, "") for c in L_COLS]

        # ひとつでも "1" がある？
        has_any_error = any(v == "1" for v in vals_all)

        # 右眼すべて =1 ?
        right_all_1 = all(v == "1" for v in vals_r)

        # 左眼すべて =1 ?
        left_all_1 = all(v == "1" for v in vals_l)

        # 全部 =1 (完全欠損)
        all_1 = right_all_1 and left_all_1

        # 振り分け
        if has_any_error:
            ids_has_any_error.append(id_)

        if all_1:
            ids_complete_missing.append(id_)
        else:
            # 右のみ完全欠損（左は完全ではない）
            if right_all_1 and not left_all_1:
                ids_right_only_missing.append(id_)

            # 左のみ完全欠損（右は完全ではない）
            if left_all_1 and not right_all_1:
                ids_left_only_missing.append(id_)

    # ===== 出力 =====

    print("========== 欠損の集計 ==========\n")
    print(f"総ID数: {total_n}\n")

    print("【1つ以上のエラー（1）を含む ID】")
    print(f"人数: {len(ids_has_any_error)} / {total_n}")
    print(f"割合: {len(ids_has_any_error)/total_n*100:.1f}%")
    print(f"IDリスト: {ids_has_any_error}\n")

    print("【両眼とも完全欠損（全18領域が1）】")
    print(f"人数: {len(ids_complete_missing)} / {total_n}")
    print(f"割合: {len(ids_complete_missing)/total_n*100:.1f}%")
    print(f"IDリスト: {ids_complete_missing}\n")

    print("【右眼のみ完全欠損（右9領域=1、左は完全ではない）】")
    print(f"人数: {len(ids_right_only_missing)} / {total_n}")
    print(f"割合: {len(ids_right_only_missing)/total_n*100:.1f}%")
    print(f"IDリスト: {ids_right_only_missing}\n")

    print("【左眼のみ完全欠損（左9領域=1、右は完全ではない）】")
    print(f"人数: {len(ids_left_only_missing)} / {total_n}")
    print(f"割合: {len(ids_left_only_missing)/total_n*100:.1f}%")
    print(f"IDリスト: {ids_left_only_missing}\n")


if __name__ == "__main__":
    main()
