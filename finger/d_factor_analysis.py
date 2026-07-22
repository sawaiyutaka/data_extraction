# ============================================================
# 8項目版女性らしさ尺度と5項目短縮版の比較・検証
#
# 原尺度：
# 35 + AD45 - AD44 - AD46 - AD47 - AD48 - AD49 - AD50 - AD51
#
# 短縮版候補：
# AD45, AD46, AD47, AD48, AD51
# ============================================================

# 初回のみ必要
# pip install pandas numpy scipy openpyxl factor_analyzer

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import (
    calculate_kmo,
    calculate_bartlett_sphericity
)

# ============================================================
# 1. 設定
# ============================================================

input_file = r"D:\ttc2d4d\sawai_260722.csv"
OUTPUT_PATH = r"D:\ttc2d4d\sawai_260722.csvfemininity_scale_validation.xlsx"

# 回答カテゴリーの最小値・最大値
# 例：1～4件法なら1, 4
ITEM_MIN = 1
ITEM_MAX = 4

# 性別変数
SEX_VAR = "TTC_sex"

# 原尺度の8項目
FULL_ITEMS = [
    "AD44", "AD45", "AD46", "AD47",
    "AD48", "AD49", "AD50", "AD51"
]

# 今回検討する5項目
SHORT_ITEMS = [
    "AD45", "AD46", "AD47", "AD48", "AD51"
]

# 5項目版から除外される3項目
EXCLUDED_ITEMS = [
    "AD45", "AD49", "AD50"
]

# 原尺度の得点計算で符号が異なる項目
PLUS_ITEMS = ["AD45"]

MINUS_ITEMS = [
    "AD44", "AD46", "AD47", "AD48",
    "AD49", "AD50", "AD51"
]

# 得点計算を許容する回答済み項目数
# 完全回答のみで計算する場合は、それぞれ項目数と同じにする
MIN_VALID_FULL = 8
MIN_VALID_SHORT = 5
MIN_VALID_EXCLUDED = 3

# ブートストラップ回数
N_BOOTSTRAP = 2000
RANDOM_SEED = 12345


# ============================================================
# 2. データ読み込み
# ============================================================

df = pd.read_csv(
    input_file,
    encoding="utf-8-sig"
)


missing_columns = [
    col for col in FULL_ITEMS + [SEX_VAR]
    if col not in df.columns
]

if missing_columns:
    print("以下の列がデータにありません：")
    print(missing_columns)
    raise KeyError("必要な列名を確認してください。")

# 項目を数値に変換
for col in FULL_ITEMS:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 回答範囲外の値を欠損にする
for col in FULL_ITEMS:
    invalid = (
        df[col].notna()
        & ~df[col].between(ITEM_MIN, ITEM_MAX)
    )

    if invalid.any():
        print(
            f"警告：{col}に回答範囲外の値が"
            f"{invalid.sum()}件あり、欠損値に置換しました。"
        )
        df.loc[invalid, col] = np.nan


# ============================================================
# 3. 得点方向をそろえる
# ============================================================

def reverse_score(series):
    """
    逆転得点を計算する。
    1～4件法なら、1→4、2→3、3→2、4→1。
    """
    return ITEM_MIN + ITEM_MAX - series


# 高得点ほど原尺度の得点が高くなるように方向を統一
aligned = pd.DataFrame(index=df.index)

for item in FULL_ITEMS:
    if item in MINUS_ITEMS:
        aligned[item] = reverse_score(df[item])
    else:
        aligned[item] = df[item]

aligned.columns = [f"{x}_aligned" for x in aligned.columns]

# 元データに追加
df = pd.concat([df, aligned], axis=1)

FULL_ALIGNED = [f"{x}_aligned" for x in FULL_ITEMS]
SHORT_ALIGNED = [f"{x}_aligned" for x in SHORT_ITEMS]
EXCLUDED_ALIGNED = [f"{x}_aligned" for x in EXCLUDED_ITEMS]


# ============================================================
# 4. 原尺度と短縮版の得点計算
# ============================================================

# 論文等で示されている原尺度の計算式
df["femininity_original_formula"] = (
    35
    + df["AD45"]
    - df["AD44"]
    - df["AD46"]
    - df["AD47"]
    - df["AD48"]
    - df["AD49"]
    - df["AD50"]
    - df["AD51"]
)

# 8項目すべてに回答していない場合は欠損
df.loc[
    df[FULL_ITEMS].notna().sum(axis=1) < MIN_VALID_FULL,
    "femininity_original_formula"
] = np.nan


def prorated_sum(data, items, minimum_valid):
    """
    欠損が許容される場合に、回答済み項目の平均×全項目数で
    比例配分した合計得点を計算する。
    """
    number_valid = data[items].notna().sum(axis=1)
    score = data[items].mean(axis=1) * len(items)
    score[number_valid < minimum_valid] = np.nan
    return score


# 方向をそろえた8項目合計
df["femininity_full_8item"] = prorated_sum(
    df, FULL_ALIGNED, MIN_VALID_FULL
)

# 方向をそろえた5項目合計
df["femininity_short_5item"] = prorated_sum(
    df, SHORT_ALIGNED, MIN_VALID_SHORT
)

# 5項目の平均得点
df["femininity_short_5item_mean"] = (
    df[SHORT_ALIGNED].mean(axis=1)
)

df.loc[
    df[SHORT_ALIGNED].notna().sum(axis=1) < MIN_VALID_SHORT,
    "femininity_short_5item_mean"
] = np.nan

# 除外された3項目の得点
df["femininity_excluded_3item"] = prorated_sum(
    df, EXCLUDED_ALIGNED, MIN_VALID_EXCLUDED
)

# 比較用の標準化得点
for col in [
    "femininity_full_8item",
    "femininity_short_5item",
    "femininity_excluded_3item"
]:
    mean = df[col].mean()
    sd = df[col].std(ddof=1)
    df[f"{col}_z"] = (df[col] - mean) / sd


# ============================================================
# 5. 項目ごとの記述統計
# ============================================================

def item_descriptive(data, items):
    results = []

    for item in items:
        x = data[item]
        valid = x.dropna()
        n_total = len(x)
        n_valid = valid.shape[0]
        n_missing = x.isna().sum()

        if n_valid > 0:
            floor_n = (valid == ITEM_MIN).sum()
            ceiling_n = (valid == ITEM_MAX).sum()

            row = {
                "Item": item,
                "N_total": n_total,
                "N_valid": n_valid,
                "N_missing": n_missing,
                "Missing_percent": n_missing / n_total * 100,
                "Mean": valid.mean(),
                "SD": valid.std(ddof=1),
                "Median": valid.median(),
                "Minimum": valid.min(),
                "Maximum": valid.max(),
                "Skewness": stats.skew(valid, bias=False),
                "Kurtosis": stats.kurtosis(valid, bias=False),
                "Floor_n": floor_n,
                "Floor_percent": floor_n / n_valid * 100,
                "Ceiling_n": ceiling_n,
                "Ceiling_percent": ceiling_n / n_valid * 100
            }
        else:
            row = {
                "Item": item,
                "N_total": n_total,
                "N_valid": 0,
                "N_missing": n_missing,
                "Missing_percent": 100,
                "Mean": np.nan,
                "SD": np.nan,
                "Median": np.nan,
                "Minimum": np.nan,
                "Maximum": np.nan,
                "Skewness": np.nan,
                "Kurtosis": np.nan,
                "Floor_n": np.nan,
                "Floor_percent": np.nan,
                "Ceiling_n": np.nan,
                "Ceiling_percent": np.nan
            }

        results.append(row)

    return pd.DataFrame(results)


item_statistics = item_descriptive(df, FULL_ITEMS)

# 回答カテゴリー別の人数
response_distribution = []

for item in FULL_ITEMS:
    counts = (
        df[item]
        .value_counts(dropna=False)
        .sort_index()
    )

    for category, count in counts.items():
        response_distribution.append({
            "Item": item,
            "Response": (
                "Missing" if pd.isna(category) else category
            ),
            "N": count,
            "Percent": count / len(df) * 100
        })

response_distribution = pd.DataFrame(response_distribution)


# ============================================================
# 6. Cronbachのα
# ============================================================

def cronbach_alpha(data):
    """
    完全回答者を用いてCronbachのαを計算する。
    """
    x = data.dropna()

    if len(x) < 3 or x.shape[1] < 2:
        return np.nan

    item_variances = x.var(axis=0, ddof=1)
    total_variance = x.sum(axis=1).var(ddof=1)
    number_items = x.shape[1]

    if total_variance == 0:
        return np.nan

    alpha = (
        number_items / (number_items - 1)
        * (1 - item_variances.sum() / total_variance)
    )

    return alpha


# ============================================================
# 7. McDonaldのω
# ============================================================

def mcdonald_omega(data):
    """
    1因子モデルに基づくMcDonaldのω totalの近似値。
    完全回答者を使用する。
    """
    x = data.dropna()

    if len(x) < 10 or x.shape[1] < 3:
        return np.nan

    fa = FactorAnalyzer(
        n_factors=1,
        rotation=None,
        method="minres"
    )
    fa.fit(x)

    loadings = fa.loadings_[:, 0]
    uniqueness = fa.get_uniquenesses()

    omega = (
        np.sum(loadings) ** 2
        / (
            np.sum(loadings) ** 2
            + np.sum(uniqueness)
        )
    )

    return omega


# ============================================================
# 8. 修正済み項目–合計相関と項目削除時α
# ============================================================

def item_analysis(data, items):
    complete = data[items].dropna()
    results = []

    for item in items:
        remaining_items = [x for x in items if x != item]
        remaining_total = complete[remaining_items].sum(axis=1)

        if len(complete) >= 3:
            correlation, p_value = stats.pearsonr(
                complete[item],
                remaining_total
            )
        else:
            correlation, p_value = np.nan, np.nan

        results.append({
            "Item": item.replace("_aligned", ""),
            "N_complete": len(complete),
            "Corrected_item_total_r": correlation,
            "Corrected_item_total_p": p_value,
            "Alpha_if_deleted": cronbach_alpha(
                complete[remaining_items]
            ),
            "Item_mean_aligned": complete[item].mean(),
            "Item_SD_aligned": complete[item].std(ddof=1)
        })

    return pd.DataFrame(results)


full_item_analysis = item_analysis(df, FULL_ALIGNED)
short_item_analysis = item_analysis(df, SHORT_ALIGNED)


# ============================================================
# 9. 信頼性の要約
# ============================================================

reliability_summary = pd.DataFrame([
    {
        "Scale": "Original 8-item scale",
        "Number_of_items": 8,
        "N_complete": df[FULL_ALIGNED].dropna().shape[0],
        "Cronbach_alpha": cronbach_alpha(df[FULL_ALIGNED]),
        "McDonald_omega": mcdonald_omega(df[FULL_ALIGNED]),
        "Mean_interitem_correlation":
            df[FULL_ALIGNED].corr().values[
                np.triu_indices(len(FULL_ALIGNED), k=1)
            ].mean()
    },
    {
        "Scale": "Proposed 5-item scale",
        "Number_of_items": 5,
        "N_complete": df[SHORT_ALIGNED].dropna().shape[0],
        "Cronbach_alpha": cronbach_alpha(df[SHORT_ALIGNED]),
        "McDonald_omega": mcdonald_omega(df[SHORT_ALIGNED]),
        "Mean_interitem_correlation":
            df[SHORT_ALIGNED].corr().values[
                np.triu_indices(len(SHORT_ALIGNED), k=1)
            ].mean()
    },
    {
        "Scale": "Excluded 3-item score",
        "Number_of_items": 3,
        "N_complete": df[EXCLUDED_ALIGNED].dropna().shape[0],
        "Cronbach_alpha": cronbach_alpha(df[EXCLUDED_ALIGNED]),
        "McDonald_omega": mcdonald_omega(df[EXCLUDED_ALIGNED]),
        "Mean_interitem_correlation":
            df[EXCLUDED_ALIGNED].corr().values[
                np.triu_indices(len(EXCLUDED_ALIGNED), k=1)
            ].mean()
    }
])


# ============================================================
# 10. 探索的因子分析
# ============================================================

def efa_one_factor(data, items, scale_name):
    x = data[items].dropna()

    if len(x) < 10:
        return (
            pd.DataFrame(),
            pd.DataFrame([{
                "Scale": scale_name,
                "N": len(x),
                "KMO": np.nan,
                "Bartlett_chi2": np.nan,
                "Bartlett_p": np.nan,
                "Variance_explained_percent": np.nan
            }])
        )

    kmo_all, kmo_model = calculate_kmo(x)
    bartlett_chi2, bartlett_p = (
        calculate_bartlett_sphericity(x)
    )

    fa = FactorAnalyzer(
        n_factors=1,
        rotation=None,
        method="minres"
    )
    fa.fit(x)

    loadings = pd.DataFrame({
        "Scale": scale_name,
        "Item": [i.replace("_aligned", "") for i in items],
        "Factor_loading": fa.loadings_[:, 0],
        "Communality": fa.get_communalities(),
        "Uniqueness": fa.get_uniquenesses()
    })

    variance = fa.get_factor_variance()

    fit_summary = pd.DataFrame([{
        "Scale": scale_name,
        "N": len(x),
        "KMO": kmo_model,
        "Bartlett_chi2": bartlett_chi2,
        "Bartlett_p": bartlett_p,
        "Variance_explained_percent": variance[1][0] * 100
    }])

    return loadings, fit_summary


full_loadings, full_efa_summary = efa_one_factor(
    df, FULL_ALIGNED, "Original 8-item scale"
)

short_loadings, short_efa_summary = efa_one_factor(
    df, SHORT_ALIGNED, "Proposed 5-item scale"
)

factor_loadings = pd.concat(
    [full_loadings, short_loadings],
    ignore_index=True
)

efa_summary = pd.concat(
    [full_efa_summary, short_efa_summary],
    ignore_index=True
)


# ============================================================
# 11. 平行分析
# ============================================================

def parallel_analysis(data, items, n_iter=1000, seed=12345):
    """
    実データの相関行列の固有値と、
    ランダムデータの95パーセンタイルを比較する。
    """
    x = data[items].dropna()

    if len(x) < 10:
        return pd.DataFrame()

    rng = np.random.default_rng(seed)

    actual_eigenvalues = np.linalg.eigvalsh(
        x.corr().values
    )[::-1]

    random_eigenvalues = np.zeros(
        (n_iter, len(items))
    )

    for i in range(n_iter):
        random_data = rng.normal(
            size=(len(x), len(items))
        )
        random_corr = np.corrcoef(
            random_data,
            rowvar=False
        )
        random_eigenvalues[i, :] = np.linalg.eigvalsh(
            random_corr
        )[::-1]

    random_95 = np.percentile(
        random_eigenvalues,
        95,
        axis=0
    )

    return pd.DataFrame({
        "Factor_number": np.arange(1, len(items) + 1),
        "Actual_eigenvalue": actual_eigenvalues,
        "Random_95th_percentile": random_95,
        "Retain_factor":
            actual_eigenvalues > random_95
    })


parallel_full = parallel_analysis(
    df, FULL_ALIGNED, seed=RANDOM_SEED
)
parallel_full["Scale"] = "Original 8-item scale"

parallel_short = parallel_analysis(
    df, SHORT_ALIGNED, seed=RANDOM_SEED
)
parallel_short["Scale"] = "Proposed 5-item scale"

parallel_results = pd.concat(
    [parallel_full, parallel_short],
    ignore_index=True
)


# ============================================================
# 12. 尺度得点間の相関
# ============================================================

def correlation_result(data, variable1, variable2):
    temp = data[[variable1, variable2]].dropna()

    if len(temp) < 3:
        return {
            "Variable_1": variable1,
            "Variable_2": variable2,
            "N": len(temp),
            "Pearson_r": np.nan,
            "Pearson_p": np.nan,
            "Spearman_rho": np.nan,
            "Spearman_p": np.nan
        }

    pearson_r, pearson_p = stats.pearsonr(
        temp[variable1], temp[variable2]
    )
    spearman_rho, spearman_p = stats.spearmanr(
        temp[variable1], temp[variable2]
    )

    return {
        "Variable_1": variable1,
        "Variable_2": variable2,
        "N": len(temp),
        "Pearson_r": pearson_r,
        "Pearson_p": pearson_p,
        "Spearman_rho": spearman_rho,
        "Spearman_p": spearman_p
    }


score_correlations = pd.DataFrame([
    correlation_result(
        df,
        "femininity_short_5item",
        "femininity_full_8item"
    ),
    correlation_result(
        df,
        "femininity_short_5item",
        "femininity_original_formula"
    ),
    correlation_result(
        df,
        "femininity_short_5item",
        "femininity_excluded_3item"
    )
])


# ============================================================
# 13. ブートストラップ95%信頼区間
# ============================================================

def bootstrap_statistic(
    data,
    statistic_function,
    n_bootstrap=2000,
    seed=12345
):
    rng = np.random.default_rng(seed)
    estimates = []

    for _ in range(n_bootstrap):
        indices = rng.integers(
            0, len(data), len(data)
        )
        sample = data.iloc[indices]

        try:
            estimate = statistic_function(sample)
            if np.isfinite(estimate):
                estimates.append(estimate)
        except Exception:
            continue

    if len(estimates) == 0:
        return np.nan, np.nan, np.nan

    return (
        statistic_function(data),
        np.percentile(estimates, 2.5),
        np.percentile(estimates, 97.5)
    )


bootstrap_results = []

# αの信頼区間
for scale_name, items in [
    ("Original 8-item scale", FULL_ALIGNED),
    ("Proposed 5-item scale", SHORT_ALIGNED)
]:
    complete = df[items].dropna().reset_index(drop=True)

    estimate, lower, upper = bootstrap_statistic(
        complete,
        cronbach_alpha,
        n_bootstrap=N_BOOTSTRAP,
        seed=RANDOM_SEED
    )

    bootstrap_results.append({
        "Statistic": "Cronbach alpha",
        "Scale_or_comparison": scale_name,
        "Estimate": estimate,
        "CI_lower_95": lower,
        "CI_upper_95": upper,
        "N": len(complete)
    })

# 5項目版と8項目版の相関
correlation_data = df[
    [
        "femininity_short_5item",
        "femininity_full_8item"
    ]
].dropna().reset_index(drop=True)


def short_full_correlation(x):
    return stats.pearsonr(
        x["femininity_short_5item"],
        x["femininity_full_8item"]
    )[0]


estimate, lower, upper = bootstrap_statistic(
    correlation_data,
    short_full_correlation,
    n_bootstrap=N_BOOTSTRAP,
    seed=RANDOM_SEED
)

bootstrap_results.append({
    "Statistic": "Pearson correlation",
    "Scale_or_comparison": "5-item vs 8-item",
    "Estimate": estimate,
    "CI_lower_95": lower,
    "CI_upper_95": upper,
    "N": len(correlation_data)
})

# 5項目版と除外3項目の相関
excluded_correlation_data = df[
    [
        "femininity_short_5item",
        "femininity_excluded_3item"
    ]
].dropna().reset_index(drop=True)


def short_excluded_correlation(x):
    return stats.pearsonr(
        x["femininity_short_5item"],
        x["femininity_excluded_3item"]
    )[0]


estimate, lower, upper = bootstrap_statistic(
    excluded_correlation_data,
    short_excluded_correlation,
    n_bootstrap=N_BOOTSTRAP,
    seed=RANDOM_SEED
)

bootstrap_results.append({
    "Statistic": "Pearson correlation",
    "Scale_or_comparison": "5-item vs excluded 3-item",
    "Estimate": estimate,
    "CI_lower_95": lower,
    "CI_upper_95": upper,
    "N": len(excluded_correlation_data)
})

bootstrap_results = pd.DataFrame(bootstrap_results)


# ============================================================
# 14. 性別ごとの記述統計と信頼性
# ============================================================

sex_results = []

for sex_value, group in df.groupby(SEX_VAR):
    for scale_name, items, score in [
        (
            "Original 8-item scale",
            FULL_ALIGNED,
            "femininity_full_8item"
        ),
        (
            "Proposed 5-item scale",
            SHORT_ALIGNED,
            "femininity_short_5item"
        )
    ]:
        sex_results.append({
            SEX_VAR: sex_value,
            "Scale": scale_name,
            "N_score": group[score].notna().sum(),
            "Mean": group[score].mean(),
            "SD": group[score].std(ddof=1),
            "Minimum": group[score].min(),
            "Maximum": group[score].max(),
            "Cronbach_alpha":
                cronbach_alpha(group[items]),
            "McDonald_omega":
                mcdonald_omega(group[items])
        })

sex_results = pd.DataFrame(sex_results)


# ============================================================
# 15. 性別による5項目得点の比較
# ============================================================

sex_values = sorted(df[SEX_VAR].dropna().unique())

if len(sex_values) == 2:
    group1 = df.loc[
        df[SEX_VAR] == sex_values[0],
        "femininity_short_5item"
    ].dropna()

    group2 = df.loc[
        df[SEX_VAR] == sex_values[1],
        "femininity_short_5item"
    ].dropna()

    welch = stats.ttest_ind(
        group1,
        group2,
        equal_var=False
    )

    pooled_sd = np.sqrt(
        (
            (len(group1) - 1) * group1.var(ddof=1)
            + (len(group2) - 1) * group2.var(ddof=1)
        )
        / (len(group1) + len(group2) - 2)
    )

    cohens_d = (
        (group2.mean() - group1.mean()) / pooled_sd
        if pooled_sd > 0 else np.nan
    )

    sex_comparison = pd.DataFrame([{
        "Group_1": sex_values[0],
        "Group_2": sex_values[1],
        "N_group_1": len(group1),
        "N_group_2": len(group2),
        "Mean_group_1": group1.mean(),
        "Mean_group_2": group2.mean(),
        "Mean_difference_group2_minus_group1":
            group2.mean() - group1.mean(),
        "Welch_t": welch.statistic,
        "Welch_p": welch.pvalue,
        "Cohens_d": cohens_d
    }])
else:
    sex_comparison = pd.DataFrame({
        "Message": [
            f"{SEX_VAR}が2群ではないため比較を実施しませんでした。"
        ]
    })


# ============================================================
# 16. 得点の記述統計
# ============================================================

score_variables = [
    "femininity_original_formula",
    "femininity_full_8item",
    "femininity_short_5item",
    "femininity_short_5item_mean",
    "femininity_excluded_3item"
]

score_descriptive = (
    df[score_variables]
    .describe()
    .T
    .reset_index()
    .rename(columns={"index": "Score"})
)


# ============================================================
# 17. Excelに出力
# ============================================================

with pd.ExcelWriter(
    OUTPUT_PATH,
    engine="openpyxl"
) as writer:

    item_statistics.to_excel(
        writer,
        sheet_name="Item_descriptives",
        index=False
    )

    response_distribution.to_excel(
        writer,
        sheet_name="Response_distribution",
        index=False
    )

    df[FULL_ITEMS].corr(method="pearson").to_excel(
        writer,
        sheet_name="Item_correlations"
    )

    df[FULL_ITEMS].corr(method="spearman").to_excel(
        writer,
        sheet_name="Item_corr_Spearman"
    )

    full_item_analysis.to_excel(
        writer,
        sheet_name="Full_item_analysis",
        index=False
    )

    short_item_analysis.to_excel(
        writer,
        sheet_name="Short_item_analysis",
        index=False
    )

    reliability_summary.to_excel(
        writer,
        sheet_name="Reliability",
        index=False
    )

    efa_summary.to_excel(
        writer,
        sheet_name="EFA_summary",
        index=False
    )

    factor_loadings.to_excel(
        writer,
        sheet_name="Factor_loadings",
        index=False
    )

    parallel_results.to_excel(
        writer,
        sheet_name="Parallel_analysis",
        index=False
    )

    score_descriptive.to_excel(
        writer,
        sheet_name="Score_descriptives",
        index=False
    )

    score_correlations.to_excel(
        writer,
        sheet_name="Score_correlations",
        index=False
    )

    bootstrap_results.to_excel(
        writer,
        sheet_name="Bootstrap_CI",
        index=False
    )

    sex_results.to_excel(
        writer,
        sheet_name="Results_by_sex",
        index=False
    )

    sex_comparison.to_excel(
        writer,
        sheet_name="Sex_comparison",
        index=False
    )

    output_columns = (
        FULL_ITEMS
        + [SEX_VAR]
        + FULL_ALIGNED
        + score_variables
        + [
            "femininity_full_8item_z",
            "femininity_short_5item_z",
            "femininity_excluded_3item_z"
        ]
    )

    df[output_columns].to_excel(
        writer,
        sheet_name="Scored_data",
        index=False
    )

print("解析が完了しました。")
print(f"出力ファイル：{OUTPUT_PATH}")
print()
print(reliability_summary)
print()
print(score_correlations)
