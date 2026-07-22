import pandas as pd

# ============================================================
# ファイル設定
# ============================================================
input_file = r"D:\ttc2d4d\sawai_260721.csv"
output_file = r"D:\ttc2d4d\descriptive_statistics_by_TTC_sex.csv"

group_variable = "TTC_sex"

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

# ============================================================
# CSVデータの読み込み
# ============================================================
df = pd.read_csv(
    input_file,
    usecols=[group_variable] + variables
)

# 指標を数値型に変換
# 数値に変換できない値は欠損値（NaN）として扱う
df[variables] = df[variables].apply(
    pd.to_numeric,
    errors="coerce"
)

# ============================================================
# TTC_sex別に記述統計を計算
# ============================================================
results = []

for sex in [1, 2]:
    group_df = df[df[group_variable] == sex]
    total_n = len(group_df)

    for variable in variables:
        valid_n = group_df[variable].notna().sum()
        missing_n = group_df[variable].isna().sum()

        if total_n > 0:
            missing_percent = missing_n / total_n * 100
        else:
            missing_percent = float("nan")

        results.append({
            "TTC_sex": sex,
            "Variable": variable,
            "Total_N": total_n,
            "Valid_N": valid_n,
            "Mean": group_df[variable].mean(),
            "SD": group_df[variable].std(ddof=1),
            "Missing_N": missing_n,
            "Missing_percent": missing_percent
        })

result_df = pd.DataFrame(results)

# 小数点以下2桁に丸める
result_df["Mean"] = result_df["Mean"].round(2)
result_df["SD"] = result_df["SD"].round(2)
result_df["Missing_percent"] = result_df["Missing_percent"].round(1)

# ============================================================
# CSV出力
# ============================================================
result_df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)

print(f"記述統計を出力しました: {output_file}")
print(result_df)

# ============================================================
# TTC_sex = 1と2の平均値の比較：Welchのt検定
# ============================================================
from scipy.stats import ttest_ind
from statsmodels.stats.multitest import multipletests

test_results = []

for variable in variables:
    # 各群について、当該変数の欠損値を除外
    group1 = df.loc[df[group_variable] == 1, variable].dropna()
    group2 = df.loc[df[group_variable] == 2, variable].dropna()

    if len(group1) >= 2 and len(group2) >= 2:
        # 等分散を仮定しないWelchのt検定
        t_statistic, p_value = ttest_ind(
            group1,
            group2,
            equal_var=False
        )
    else:
        t_statistic = float("nan")
        p_value = float("nan")

    test_results.append({
        "Variable": variable,
        "TTC_sex_1_N": len(group1),
        "TTC_sex_1_Mean": group1.mean(),
        "TTC_sex_1_SD": group1.std(ddof=1),
        "TTC_sex_2_N": len(group2),
        "TTC_sex_2_Mean": group2.mean(),
        "TTC_sex_2_SD": group2.std(ddof=1),
        # 正の値：TTC_sex 1の平均が高い
        # 負の値：TTC_sex 2の平均が高い
        "Mean_difference_1_minus_2": group1.mean() - group2.mean(),
        "Welch_t": t_statistic,
        "P_value": p_value
    })

test_df = pd.DataFrame(test_results)

# ============================================================
# Benjamini–Hochberg法による多重比較補正
# ============================================================
valid_p = test_df["P_value"].notna()

test_df["P_value_FDR"] = float("nan")
test_df["Significant_raw_p_lt_0.05"] = False
test_df["Significant_FDR_p_lt_0.05"] = False

if valid_p.any():
    reject, adjusted_p, _, _ = multipletests(
        test_df.loc[valid_p, "P_value"],
        alpha=0.05,
        method="fdr_bh"
    )

    test_df.loc[valid_p, "P_value_FDR"] = adjusted_p
    test_df.loc[valid_p, "Significant_raw_p_lt_0.05"] = (
        test_df.loc[valid_p, "P_value"] < 0.05
    )
    test_df.loc[valid_p, "Significant_FDR_p_lt_0.05"] = reject

# 表示桁数を調整
summary_columns = [
    "TTC_sex_1_Mean",
    "TTC_sex_1_SD",
    "TTC_sex_2_Mean",
    "TTC_sex_2_SD",
    "Mean_difference_1_minus_2",
    "Welch_t"
]

test_df[summary_columns] = test_df[summary_columns].round(2)
test_df["P_value"] = test_df["P_value"].round(4)
test_df["P_value_FDR"] = test_df["P_value_FDR"].round(4)

# ============================================================
# 検定結果をCSV出力
# ============================================================
test_output_file = r"D:\ttc2d4d\comparison_between_TTC_sex_groups.csv"

test_df.to_csv(
    test_output_file,
    index=False,
    encoding="utf-8-sig"
)

print(f"群間比較の結果を出力しました: {test_output_file}")
print(test_df.to_string(index=False))
