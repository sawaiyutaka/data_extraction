import pandas as pd
import numpy as np
from scipy.stats import pearsonr, norm

# ============================================================
# ファイル設定
# ============================================================
input_file = r"D:\ttc2d4d\sawai_260721.csv"
output_file = r"D:\ttc2d4d\correlations_with_2D4D.csv"

variables = [
    "AE62D4DR",
    "AE62D4DL",
    "CA329",
    "CA330A",
    "CA330B",
    "CA330C",
    "CA330D",
    "CA330E",
    "CA330F",
    "CA330G",
    "CA330H",
    "CA330I",
    "CA330J",
    "CA330K",
    "CB118A",
    "CB118B",
    "CB118C",
    "CB118D",
    "CB118E",
    "CB118F",
    "CB118G",
    "CB118H",
    "CB118I",
    "CB118J",
    "CB118K",
    "CC86A",
    "CC86B",
    "CC86C",
    "CC86D",
    "CC86E",
    "CC86F",
    "CC86G",
    "CC86H",
    "CC86I",
    "CC86J",
    "CC86K",
    "CD45A",
    "CD45B",
    "CD45C",
    "CD45D",
    "CD45E",
    "CD45F",
    "CD45G",
    "CD45H",
    "CD45I",
    "CD45J",
    "CD45K",
    "CD48A",
    "CD48B",
    "CD48C",
    "CD48D",
    "CD48E",
    "CD48F",
    "CD48G",
    "CD48H",
    "CD48I",
    "CD48J",
    "CD48K"
]

# TTC_sexは読み込まない
df = pd.read_csv(
    input_file,
    usecols=variables,
    encoding="utf-8-sig"
)

# 数値に変換できない値を欠損値にする
df[variables] = df[variables].apply(
    pd.to_numeric,
    errors="coerce"
)

# ============================================================
# Pearson相関係数の95%信頼区間
# Fisherのz変換を使用
# ============================================================
def pearson_ci(r, n, confidence=0.95):
    """
    Pearsonの相関係数rについて、
    Fisherのz変換に基づく信頼区間を計算する。
    """
    if n <= 3 or np.isnan(r):
        return np.nan, np.nan

    # 完全相関の場合にatanhで無限大になるのを防ぐ
    if r >= 1:
        return 1.0, 1.0
    if r <= -1:
        return -1.0, -1.0

    z = np.arctanh(r)
    standard_error = 1 / np.sqrt(n - 3)
    z_critical = norm.ppf(1 - (1 - confidence) / 2)

    lower_z = z - z_critical * standard_error
    upper_z = z + z_critical * standard_error

    return np.tanh(lower_z), np.tanh(upper_z)


# ============================================================
# AE62D4DR・AE62D4DLと各指標の相関
# ============================================================
target_variables = [
    "AE62D4DR",
    "AE62D4DL"
]

# 2D:4D変数そのものは比較対象から除外
indicator_variables = [
    variable for variable in variables
    if variable not in target_variables
]

results = []

for target in target_variables:
    for indicator in indicator_variables:

        # この2変数のどちらにも欠損がない対象者のみ使用
        pair_df = df[[target, indicator]].dropna()
        n = len(pair_df)

        # 相関係数の計算には少なくとも3人必要
        # 両変数にばらつきがあることも確認
        if (
            n >= 3
            and pair_df[target].nunique() > 1
            and pair_df[indicator].nunique() > 1
        ):
            r, p_value = pearsonr(
                pair_df[target],
                pair_df[indicator]
            )

            ci_lower, ci_upper = pearson_ci(r, n)

        else:
            r = np.nan
            p_value = np.nan
            ci_lower = np.nan
            ci_upper = np.nan

        results.append({
            "2D4D_variable": target,
            "Indicator": indicator,
            "N_pairwise_complete": n,
            "Pearson_r": r,
            "CI_95_lower": ci_lower,
            "CI_95_upper": ci_upper,
            "P_value": p_value
        })

correlation_df = pd.DataFrame(results)

# ============================================================
# 表示桁数の調整
# ============================================================
correlation_df[
    ["Pearson_r", "CI_95_lower", "CI_95_upper"]
] = correlation_df[
    ["Pearson_r", "CI_95_lower", "CI_95_upper"]
].round(3)

correlation_df["P_value"] = correlation_df["P_value"].round(4)

# ============================================================
# CSV出力
# ============================================================
correlation_df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)

print(f"相関分析の結果を出力しました: {output_file}")
print(correlation_df.to_string(index=False))
