import pandas as pd
import numpy as np
from scipy.stats import ttest_ind
from statsmodels.stats.multitest import multipletests

# ============================================================
# ファイル設定
# ============================================================
input_file = r"D:\ttc2d4d\sawai_260722.csv"

descriptive_output_file = (
    r"D:\ttc2d4d\CPAQ_descriptive_statistics_by_TTC_sex.csv"
)

test_output_file = (
    r"D:\ttc2d4d\CPAQ_comparison_between_TTC_sex_groups.csv"
)

group_variable = "TTC_sex"

# 今回使用する5項目
item_variables = [
    "AD45",
    "AD46",
    "AD47",
    "AD48",
    "AD51"
]

# 作成する得点
score_variables = [
    "care_labor_total",
    "care_labor_ave"
]

# ============================================================
# CSVデータの読み込み
# ============================================================
df = pd.read_csv(
    input_file,
    usecols=[group_variable] + item_variables,
    encoding="utf-8-sig"
)

# TTC_sexと各項目を数値型に変換
# 数値に変換できない値はNaNにする
df[group_variable] = pd.to_numeric(
    df[group_variable],
    errors="coerce"
)

df[item_variables] = df[item_variables].apply(
    pd.to_numeric,
    errors="coerce"
)

# ============================================================
# 回答範囲の確認
# 1～4以外の値は欠損値として扱う
# ============================================================
for item in item_variables:
    df.loc[~df[item].isin([1, 2, 3, 4]), item] = np.nan

# ============================================================
# CPAQ feminineの一部の得点から「ケア労働志向性」の計算
# ============================================================
# 5項目すべてに回答があるか
complete_response = df[item_variables].notna().all(axis=1)

# あらかじめ欠損値で作成
df["care_labor_total"] = np.nan
df["care_labor_ave"] = np.nan

# 5項目すべてに回答がある人だけ得点を計算
df.loc[complete_response, "care_labor_total"] = (
    df.loc[complete_response, "AD45"]
    + (5 - df.loc[complete_response, "AD46"])
    + (5 - df.loc[complete_response, "AD47"])
    + (5 - df.loc[complete_response, "AD48"])
    + (5 - df.loc[complete_response, "AD51"])
)

# 平均得点
df.loc[complete_response, "care_labor_ave"] = (
    df.loc[complete_response, "care_labor_total"] / 5
)

# 得点範囲
# Total：5～20点
# Ave  ：1～4点

# TTC_sexが1または2のデータだけを解析
df = df[df[group_variable].isin([1, 2])].copy()

# ============================================================
# TTC_sex別の記述統計
# ============================================================
results = []

for sex in [1, 2]:
    group_df = df[df[group_variable] == sex]
    total_n = len(group_df)

    for variable in score_variables:
        valid_n = group_df[variable].notna().sum()
        missing_n = group_df[variable].isna().sum()

        missing_percent = (
            missing_n / total_n * 100
            if total_n > 0
            else np.nan
        )

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

# 表示桁数の調整
result_df["Mean"] = result_df["Mean"].round(2)
result_df["SD"] = result_df["SD"].round(2)
result_df["Missing_percent"] = (
    result_df["Missing_percent"].round(1)
)

# 記述統計をCSVに出力
result_df.to_csv(
    descriptive_output_file,
    index=False,
    encoding="utf-8-sig"
)

print(
    f"記述統計を出力しました: "
    f"{descriptive_output_file}"
)
print(result_df.to_string(index=False))

# ============================================================
# TTC_sex = 1と2の比較：Welchのt検定
# ============================================================
test_results = []

for variable in score_variables:

    group1 = df.loc[
        df[group_variable] == 1, variable
    ].dropna()

    group2 = df.loc[
        df[group_variable] == 2, variable
    ].dropna()

    # 両群に2人以上いて、データにばらつきがある場合
    if (
        len(group1) >= 2
        and len(group2) >= 2
        and pd.concat([group1, group2]).nunique() > 1
    ):
        t_statistic, p_value = ttest_ind(
            group1,
            group2,
            equal_var=False,
            nan_policy="omit"
        )
    else:
        t_statistic = np.nan
        p_value = np.nan

    test_results.append({
        "Variable": variable,
        "TTC_sex_1_N": len(group1),
        "TTC_sex_1_Mean": group1.mean(),
        "TTC_sex_1_SD": group1.std(ddof=1),
        "TTC_sex_2_N": len(group2),
        "TTC_sex_2_Mean": group2.mean(),
        "TTC_sex_2_SD": group2.std(ddof=1),
        "Mean_difference_1_minus_2": (
            group1.mean() - group2.mean()
        ),
        "Welch_t": t_statistic,
        "P_value": p_value
    })

test_df = pd.DataFrame(test_results)

# ============================================================
# Benjamini–Hochberg法による多重比較補正
# ============================================================
valid_p = test_df["P_value"].notna()

test_df["P_value_FDR"] = np.nan
test_df["Significant_raw_p_lt_0.05"] = False
test_df["Significant_FDR_p_lt_0.05"] = False

if valid_p.any():
    reject, adjusted_p, _, _ = multipletests(
        test_df.loc[valid_p, "P_value"],
        alpha=0.05,
        method="fdr_bh"
    )

    test_df.loc[valid_p, "P_value_FDR"] = adjusted_p

    test_df.loc[
        valid_p,
        "Significant_raw_p_lt_0.05"
    ] = test_df.loc[valid_p, "P_value"] < 0.05

    test_df.loc[
        valid_p,
        "Significant_FDR_p_lt_0.05"
    ] = reject

# ============================================================
# 表示桁数の調整
# ============================================================
descriptive_columns = [
    "TTC_sex_1_Mean",
    "TTC_sex_1_SD",
    "TTC_sex_2_Mean",
    "TTC_sex_2_SD",
    "Mean_difference_1_minus_2",
    "Welch_t"
]

test_df[descriptive_columns] = (
    test_df[descriptive_columns].round(2)
)

# CSVにはp値を丸めずに保存
test_df.to_csv(
    test_output_file,
    index=False,
    encoding="utf-8-sig"
)

# 画面表示のみ有効数字4桁
pd.set_option(
    "display.float_format",
    lambda x: f"{x:.4g}"
)

print(
    f"群間比較の結果を出力しました: "
    f"{test_output_file}"
)
print(test_df.to_string(index=False))
