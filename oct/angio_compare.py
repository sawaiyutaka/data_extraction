#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vd_aggregated.csv と error_mode1_contains1.csv を突き合わせて、
各部位ごとに「エラーあり(1) / エラーなし(空欄)」で
VD の平均値と標準偏差、Welchの t 検定 (t, p) を計算し CSV 出力。
さらに右眼・左眼ごとにグラフ（棒グラフ＋エラーバー）を作成します。

入力:
  vd_aggregated.csv
    ID, R_Center, R_Inner_Temporal, ..., L-Outer_Inferior
  error_mode1_contains1.csv
    ID, R_Center, R_Inner_Temporal, ..., L-Outer_Inferior  (1 or 空欄)

出力:
  vd_stats_by_error.csv
    Region,
    N_error1, Mean_error1, SD_error1,
    N_error0, Mean_error0, SD_error0,
    t_error1_vs_error0, p_error1_vs_error0

  グラフ:
    vd_R_by_error.png
    vd_L_by_error.png
"""

import csv
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# ==== 設定ここから ======================================================

vd_csv = Path(r"D:\ttc5oct\oct20251126\output20251125\vd_aggregated_merged.csv")          # ←パスを合わせてください
err_csv = Path(r"D:\ttc5oct\oct20251126\output20251125\vd_error_map_contains2or9.csv")    # ←パスを合わせてください
out_csv = Path(r"D:\ttc5oct\oct20251126\output20251125\vd_stats_by_error.csv")

# グラフ出力先（画像ファイルはこのフォルダに保存）
plot_dir = out_csv.parent

# ======================================================================

# VD / エラーともに共通のカラム（ETDRS 9セクタ）
COLUMNS = [
    "R_Center", "R_Inner_Temporal", "R_Inner_Superior", "R_Inner_Nasal", "R_Inner_Inferior",
    "R_Outer_Temporal", "R_Outer_Superior", "R_Outer_Nasal", "R_Outer_Inferior",
    "L_Center", "L_Inner_Temporal", "L_Inner_Superior", "L_Inner_Nasal", "L_Inner_Inferior",
    "L_Outer_Temporal", "L_Outer_Superior", "L_Outer_Nasal", "L_Outer_Inferior",
]


def safe_float(s: str) -> Optional[float]:
    """空文字などを None にし、数字だけ float に変換"""
    if s is None:
        return None
    t = str(s).strip().replace(",", "")
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def read_csv_as_dict_by_id(path: Path) -> Dict[str, Dict[str, str]]:
    """1つのCSVを読み込み、IDをキーにした辞書にする（全セル strip 付き）"""
    data: Dict[str, Dict[str, str]] = {}
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    clean_row = {k.strip(): (v.strip() if v is not None else "") for k, v in row.items()}
                    id_ = clean_row.get("ID", "")
                    if id_:
                        data[id_] = clean_row
            break
        except UnicodeDecodeError:
            data = {}
            continue
    return data


def calc_mean_sd(values: List[float]) -> Tuple[Optional[float], Optional[float]]:
    """
    平均と標準偏差（不偏標準偏差, n-1で割る）を計算。
    要素数0 → (None, None)
    要素数1 → (mean, None)
    """
    n = len(values)
    if n == 0:
        return None, None
    mean = sum(values) / n
    if n == 1:
        return mean, None
    var = sum((x - mean) ** 2 for x in values) / (n - 1)
    sd = math.sqrt(var)
    return mean, sd


def welch_t_test(group1: List[float], group2: List[float]) -> Tuple[Optional[float], Optional[float]]:
    """
    Welch の t検定を実行する。
    group1: エラーあり
    group2: エラーなし
    どちらかの n < 2 の場合は (None, None)
    """
    if len(group1) < 2 or len(group2) < 2:
        return None, None
    # SciPy で Welch's t-test
    t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False, nan_policy="omit")
    return float(t_stat), float(p_val)


def make_barplot_for_side(
    side: str,
    stats_numeric: Dict[str, Dict[str, Optional[float]]],
    outfile: Path,
):
    """
    片眼分（RまたはL）の部位ごとの平均値＋エラーバー(SD)を棒グラフにする。

    side: 'R' or 'L'
    stats_numeric: {region_name: {"mean1":..., "sd1":..., "mean0":..., "sd0":...}, ...}
    """
    # 対象となる部位
    regions = [c for c in COLUMNS if c.startswith(side + "-")]
    if not regions:
        return

    # x軸用のラベル（"R_Center" → "Center"）
    labels = [r.split("-", 1)[1] for r in regions]

    means0 = [stats_numeric[r]["mean0"] for r in regions]
    sd0    = [stats_numeric[r]["sd0"]   for r in regions]
    means1 = [stats_numeric[r]["mean1"] for r in regions]
    sd1    = [stats_numeric[r]["sd1"]   for r in regions]

    # None を NaN にして matplotlib が扱えるようにする
    means0 = np.array([np.nan if m is None else m for m in means0], dtype=float)
    sd0    = np.array([0.0 if (s is None or np.isnan(s)) else s for s in sd0], dtype=float)
    means1 = np.array([np.nan if m is None else m for m in means1], dtype=float)
    sd1    = np.array([0.0 if (s is None or np.isnan(s)) else s for s in sd1], dtype=float)

    x = np.arange(len(regions))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width / 2, means0, width, yerr=sd0, label="Error=0", capsize=4)
    ax.bar(x + width / 2, means1, width, yerr=sd1, label="Error=1", capsize=4)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("VD")
    ax.set_title(f"{side} eye: VD by error (mean ± SD)")
    ax.legend()
    fig.tight_layout()

    outfile.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outfile, dpi=300)
    plt.close(fig)


def main():
    if not vd_csv.exists():
        print(f"Error: VD CSV が見つかりません → {vd_csv}")
        return
    if not err_csv.exists():
        print(f"Error: エラーCSVが見つかりません → {err_csv}")
        return

    # CSV読み込み（ID -> row の形）
    vd_data = read_csv_as_dict_by_id(vd_csv)
    err_data = read_csv_as_dict_by_id(err_csv)

    if not vd_data:
        print("vd_aggregated.csv にデータがありません。")
        return
    if not err_data:
        print("error_mode1_contains1.csv にデータがありません。")
        return

    # 共通IDのみ対象にする
    common_ids = sorted(set(vd_data.keys()) & set(err_data.keys()))
    if not common_ids:
        print("共通する ID がありません。")
        return

    print(f"共通ID数: {len(common_ids)}")

    stats_rows = []
    # グラフ用に数値を保持する辞書
    stats_numeric: Dict[str, Dict[str, Optional[float]]] = {}

    for col in COLUMNS:
        values_err1: List[float] = []
        values_err0: List[float] = []

        for id_ in common_ids:
            vd_row = vd_data[id_]
            err_row = err_data[id_]

            vd_val = safe_float(vd_row.get(col, ""))
            if vd_val is None:
                continue

            err_flag = (err_row.get(col, "") == "1")
            if err_flag:
                values_err1.append(vd_val)
            else:
                values_err0.append(vd_val)

        # 平均・SD
        mean1, sd1 = calc_mean_sd(values_err1)
        mean0, sd0 = calc_mean_sd(values_err0)

        # Welchのt検定
        t_stat, p_val = welch_t_test(values_err1, values_err0)

        stats_numeric[col] = {
            "mean1": mean1,
            "sd1": sd1,
            "mean0": mean0,
            "sd0": sd0,
        }

        row = {
            "Region": col,
            "N_error1": len(values_err1),
            "Mean_error1": f"{mean1:.3f}" if mean1 is not None else "",
            "SD_error1": f"{sd1:.3f}" if sd1 is not None else "",
            "N_error0": len(values_err0),
            "Mean_error0": f"{mean0:.3f}" if mean0 is not None else "",
            "SD_error0": f"{sd0:.3f}" if sd0 is not None else "",
            "t_error1_vs_error0": f"{t_stat:.3f}" if t_stat is not None else "",
            "p_error1_vs_error0": f"{p_val:.4g}" if p_val is not None else "",
        }
        stats_rows.append(row)

    # 出力ディレクトリ作成
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    # CSVに書き出し
    fieldnames = [
        "Region",
        "N_error1", "Mean_error1", "SD_error1",
        "N_error0", "Mean_error0", "SD_error0",
        "t_error1_vs_error0", "p_error1_vs_error0",
    ]

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stats_rows)

    print(f"統計CSVを書き出しました → {out_csv}")

    # グラフ作成（右眼・左眼）
    make_barplot_for_side(
        side="R",
        stats_numeric=stats_numeric,
        outfile=plot_dir / "vd_R_by_error.png",
    )
    make_barplot_for_side(
        side="L",
        stats_numeric=stats_numeric,
        outfile=plot_dir / "vd_L_by_error.png",
    )

    print(f"グラフを書き出しました → {plot_dir / 'vd_R_by_error.png'}")
    print(f"グラフを書き出しました → {plot_dir / 'vd_L_by_error.png'}")


if __name__ == "__main__":
    main()
