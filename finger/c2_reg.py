import pandas as pd
import numpy as np
import statsmodels.api as sm

# ============================================================
# ファイル設定
# ============================================================
input_file = r"D:\ttc2d4d\sawai_260722.csv"

analysis_data_output = (
    r"D:\ttc2d4d\care_labor_mental_health_analysis_data.csv"
)

linear_output = (
    r"D:\ttc2d4d\care_labor_SMFQ_linear_regression.csv"
)

logistic_output = (
    r"D:\ttc2d4d\care_labor_suicidality_logistic_regression.csv"
)

exposure = "care_labor_total"

# ケア労働志向性の計算に使用する項目
item_variables = [
    "AD45",
    "AD46",
    "AD47",
    "AD48",
    "AD51"
]

# ============================================================
# SMFQ項目の設定
# ============================================================
smfq_items = {
    "smfq_10": [
        "AD64", "AD65", "AD66", "AD67", "AD68",
        "AD69", "AD70", "AD71", "AD72", "AD73",
        "AD74", "AD77", "AD78"
    ],
    "smfq_12": [
        "BD59", "BD60", "BD61", "BD62", "BD63",
        "BD64", "BD65", "BD66", "BD67", "BD68",
        "BD69", "BD70", "BD71"
    ],
    "smfq_14": [
        "CD86", "CD87", "CD88", "CD89", "CD90",
        "CD91", "CD92", "CD93", "CD94", "CD95",
        "CD96", "CD97", "CD98"
    ],
    "smfq_16": [
        "DD95", "DD96", "DD97", "DD98", "DD99",
        "DD100", "DD101", "DD102", "DD103",
        "DD104", "DD105", "DD106", "DD107"
    ]
}

mental_health_source_variables = [
    "EC400",
    "EC401",
    "EC404"
]

all_smfq_items = [
    item
    for item_list in smfq_items.values()
    for item in item_list
]

use_columns = (
    item_variables
    + all_smfq_items
    + mental_health_source_variables
)

# ============================================================
# データの読み込み
# ============================================================
df = pd.read_csv(
    input_file,
    usecols=use_columns,
    encoding="utf-8-sig"
)

# 使用する変数を数値型に変換
# 数値に変換できない値はNaN
df[use_columns] = df[use_columns].apply(
    pd.to_numeric,
    errors="coerce"
)

# ============================================================
# CPAQ feminineの一部から「ケア労働志向性」を計算
# ============================================================

# 想定される回答範囲を1～4とする
# それ以外の値は欠損値として扱う
df[item_variables] = df[item_variables].where(
    df[item_variables].isin([1, 2, 3, 4]),
    np.nan
)

# 5項目すべてに回答しているか
complete_response = df[item_variables].notna().all(axis=1)

# あらかじめ欠損値で作成
df["care_labor_total"] = np.nan
df["care_labor_ave"] = np.nan

# 逆転項目
reverse_items = [
    "AD46",
    "AD47",
    "AD48",
    "AD51"
]

# 逆転項目は「5 - 回答値」で得点化
care_labor_scored = df[item_variables].copy()
care_labor_scored[reverse_items] = (
    5 - care_labor_scored[reverse_items]
)

# 5項目すべてに回答がある人だけ合計得点を計算
df.loc[complete_response, "care_labor_total"] = (
    care_labor_scored.loc[complete_response].sum(axis=1)
)

# 平均得点
df.loc[complete_response, "care_labor_ave"] = (
    df.loc[complete_response, "care_labor_total"] / 5
)

# 得点の確認
print("\nケア労働志向性得点の記述統計")
print(
    df[["care_labor_total", "care_labor_ave"]]
    .describe()
    .T
)

# ============================================================
# SMFQ得点を作成する関数
# ============================================================
def calculate_smfq(data, item_columns):
    """
    SMFQ得点を作成する。

    元の回答：
        1 = あてはまる
        2 = ときどきあてはまる
        3 = あてはまらない

    得点：
        3 - 元の回答
        1 → 2点
        2 → 1点
        3 → 0点

    欠損なし：
        13項目の得点を合計

    欠損が1項目：
        回答済み12項目の個人内平均で欠損項目を補完し、
        合計得点を四捨五入

    欠損が2項目以上：
        NaN
    """

    items = data[item_columns].copy()

    # 1、2、3以外の値は欠損として扱う
    items = items.where(items.isin([1, 2, 3]), np.nan)

    # 回答を0～2点に変換
    scored_items = 3 - items

    missing_count = scored_items.isna().sum(axis=1)
    observed_sum = scored_items.sum(axis=1, min_count=1)
    observed_count = scored_items.notna().sum(axis=1)

    score = pd.Series(
        np.nan,
        index=data.index,
        dtype="float64"
    )

    # 欠損がない場合
    complete = missing_count == 0

    score.loc[complete] = observed_sum.loc[complete]

    # 欠損が1項目だけの場合
    one_missing = missing_count == 1

    # 回答済み12項目の平均値で1項目を補完
    prorated_score = (
        observed_sum.loc[one_missing]
        + (
            observed_sum.loc[one_missing]
            / observed_count.loc[one_missing]
        )
    )

    # 0.5を切り上げる通常の四捨五入
    score.loc[one_missing] = np.floor(
        prorated_score + 0.5
    )

    # 欠損が2項目以上の場合はNaNのまま
    return score


# ============================================================
# 年齢別SMFQ得点の作成
# ============================================================
for score_name, item_columns in smfq_items.items():
    df[score_name] = calculate_smfq(
        df,
        item_columns
    )

# 得点範囲外になっていないか確認
for score_name in smfq_items:
    invalid_score = (
        df[score_name].notna()
        & ~df[score_name].between(0, 26)
    )

    if invalid_score.any():
        print(
            f"警告：{score_name}に0～26点の"
            f"範囲外の値があります。"
        )

# ============================================================
# 20歳時点の希死念慮
# ============================================================
# EC400が1～3なら0、4なら1、それ以外はNaN
df["suicidal_ideation"] = np.select(
    [
        df["EC400"].isin([1, 2, 3]),
        df["EC400"].eq(4)
    ],
    [
        0,
        1
    ],
    default=np.nan
)

# ============================================================
# 20歳時点の自傷
# ============================================================
# EC401が1なら0、2～5なら1、それ以外はNaN
df["self_harm"] = np.select(
    [
        df["EC401"].eq(1),
        df["EC401"].isin([2, 3, 4, 5])
    ],
    [
        0,
        1
    ],
    default=np.nan
)

# ============================================================
# 20歳時点の自殺企図
# ============================================================
df["suicide_attempt"] = np.nan

# self_harmが0なら自殺企図も0
df.loc[
    df["self_harm"].eq(0),
    "suicide_attempt"
] = 0

# self_harmが1かつEC404が0なら0
df.loc[
    df["self_harm"].eq(1)
    & df["EC404"].eq(0),
    "suicide_attempt"
] = 0

# self_harmが1かつEC404が1なら1
df.loc[
    df["self_harm"].eq(1)
    & df["EC404"].eq(1),
    "suicide_attempt"
] = 1

# 以下の場合はNaNのまま
# ・self_harmがNaN
# ・self_harmが1でEC404がNaN
# ・self_harmが1でEC404が0/1以外

# ============================================================
# 作成した変数の簡単な確認
# ============================================================
created_outcomes = [
    "smfq_10",
    "smfq_12",
    "smfq_14",
    "smfq_16",
    "suicidal_ideation",
    "self_harm",
    "suicide_attempt"
]

print("\n作成した変数の記述統計")
print(
    df[[exposure] + created_outcomes]
    .describe()
    .T
)

print("\n二値アウトカムの人数")
for variable in [
    "suicidal_ideation",
    "self_harm",
    "suicide_attempt"
]:
    print(f"\n{variable}")
    print(
        df[variable]
        .value_counts(dropna=False)
        .sort_index()
    )

# 解析用データを保存
df[[exposure] + created_outcomes].to_csv(
    analysis_data_output,
    index=False,
    encoding="utf-8-sig"
)

# ============================================================
# 線形回帰
# care_labor_total → 年齢別SMFQ
# ============================================================
linear_outcomes = [
    "smfq_10",
    "smfq_12",
    "smfq_14",
    "smfq_16"
]

linear_results = []

for outcome in linear_outcomes:

    # モデルごとのlistwise deletion
    model_data = (
        df[[exposure, outcome]]
        .dropna()
        .copy()
    )

    if (
        len(model_data) >= 3
        and model_data[exposure].nunique() >= 2
        and model_data[outcome].nunique() >= 2
    ):
        X = sm.add_constant(
            model_data[[exposure]],
            has_constant="add"
        )

        y = model_data[outcome]

        model = sm.OLS(y, X).fit()

        conf_int = model.conf_int().loc[exposure]

        linear_results.append({
            "Outcome": outcome,
            "Exposure": exposure,
            "N": int(model.nobs),
            "Outcome_mean": y.mean(),
            "Outcome_SD": y.std(ddof=1),
            "Exposure_mean": model_data[exposure].mean(),
            "Exposure_SD": model_data[exposure].std(ddof=1),
            "Beta": model.params[exposure],
            "SE": model.bse[exposure],
            "CI_95_lower": conf_int.iloc[0],
            "CI_95_upper": conf_int.iloc[1],
            "P_value": model.pvalues[exposure],
            "R_squared": model.rsquared
        })

    else:
        linear_results.append({
            "Outcome": outcome,
            "Exposure": exposure,
            "N": len(model_data),
            "Outcome_mean": model_data[outcome].mean(),
            "Outcome_SD": model_data[outcome].std(ddof=1),
            "Exposure_mean": model_data[exposure].mean(),
            "Exposure_SD": model_data[exposure].std(ddof=1),
            "Beta": np.nan,
            "SE": np.nan,
            "CI_95_lower": np.nan,
            "CI_95_upper": np.nan,
            "P_value": np.nan,
            "R_squared": np.nan
        })

linear_results_df = pd.DataFrame(linear_results)

linear_results_df.to_csv(
    linear_output,
    index=False,
    encoding="utf-8-sig"
)

# ============================================================
# ロジスティック回帰
# care_labor_total → 20歳時点の各二値アウトカム
# ============================================================
logistic_outcomes = [
    "suicidal_ideation",
    "self_harm",
    "suicide_attempt"
]

logistic_results = []

for outcome in logistic_outcomes:

    # モデルごとのlistwise deletion
    model_data = (
        df[[exposure, outcome]]
        .dropna()
        .copy()
    )

    event_n = int(
        model_data[outcome].eq(1).sum()
    )

    non_event_n = int(
        model_data[outcome].eq(0).sum()
    )

    # 回帰を実行できるか確認
    can_fit = (
        len(model_data) >= 3
        and model_data[exposure].nunique() >= 2
        and model_data[outcome].nunique() == 2
    )

    if can_fit:
        X = sm.add_constant(
            model_data[[exposure]],
            has_constant="add"
        )

        y = model_data[outcome].astype(int)

        try:
            model = sm.Logit(y, X).fit(disp=False)

            beta = model.params[exposure]
            conf_int = model.conf_int().loc[exposure]

            logistic_results.append({
                "Outcome": outcome,
                "Exposure": exposure,
                "N": int(model.nobs),
                "Event_N": event_n,
                "Non_event_N": non_event_n,
                "Event_percent": event_n / len(model_data) * 100,
                "Beta_log_odds": beta,
                "SE": model.bse[exposure],
                "OR": np.exp(beta),
                "OR_95CI_lower": np.exp(conf_int.iloc[0]),
                "OR_95CI_upper": np.exp(conf_int.iloc[1]),
                "P_value": model.pvalues[exposure],
                "Converged": model.mle_retvals["converged"]
            })

        except Exception as error:
            print(
                f"{outcome}のロジスティック回帰で"
                f"エラーが発生しました：{error}"
            )

            logistic_results.append({
                "Outcome": outcome,
                "Exposure": exposure,
                "N": len(model_data),
                "Event_N": event_n,
                "Non_event_N": non_event_n,
                "Event_percent": (
                    event_n / len(model_data) * 100
                    if len(model_data) > 0
                    else np.nan
                ),
                "Beta_log_odds": np.nan,
                "SE": np.nan,
                "OR": np.nan,
                "OR_95CI_lower": np.nan,
                "OR_95CI_upper": np.nan,
                "P_value": np.nan,
                "Converged": False
            })

    else:
        logistic_results.append({
            "Outcome": outcome,
            "Exposure": exposure,
            "N": len(model_data),
            "Event_N": event_n,
            "Non_event_N": non_event_n,
            "Event_percent": (
                event_n / len(model_data) * 100
                if len(model_data) > 0
                else np.nan
            ),
            "Beta_log_odds": np.nan,
            "SE": np.nan,
            "OR": np.nan,
            "OR_95CI_lower": np.nan,
            "OR_95CI_upper": np.nan,
            "P_value": np.nan,
            "Converged": False
        })

logistic_results_df = pd.DataFrame(logistic_results)

logistic_results_df.to_csv(
    logistic_output,
    index=False,
    encoding="utf-8-sig"
)

# ============================================================
# 結果の画面表示
# ============================================================
pd.set_option(
    "display.float_format",
    lambda x: f"{x:.4g}"
)

print("\n================================================")
print("線形回帰の結果")
print("================================================")
print(
    linear_results_df.to_string(index=False)
)

print("\n================================================")
print("ロジスティック回帰の結果")
print("================================================")
print(
    logistic_results_df.to_string(index=False)
)

print("\n出力が完了しました。")
print(f"解析用データ: {analysis_data_output}")
print(f"線形回帰: {linear_output}")
print(f"ロジスティック回帰: {logistic_output}")