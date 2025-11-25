import pandas as pd
from pathlib import Path


def load_df(path, sheet_name=0):
    path = Path(path)
    suffix = path.suffix.lower()

    # CSV
    if suffix == ".csv":
        try:
            df = pd.read_csv(path, encoding="utf-8", low_memory=False)
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="cp932", low_memory=False)
        return df
    else:
        # .xlsx など Excel を想定
        return pd.read_excel(path, sheet_name=sheet_name)


# 例: パスを指定（CSV/ExcelどちらでもOK）
master_df = load_df(r"C:\Users\sawai\PycharmProjects\ace_ple\sawai_ace_soc_3171_251110.csv")
subset_df = load_df(r"E:\ttc6sawai\ec_n2113_PIなし.xlsx")
# /Volumes/Pegasus32R8/TTC/2025thesis/before_impute.csv
# /Volumes/Pegasus32R8/TTC/2022base_OC_PLE/180511AB基本セット（CBCL・SDQ・SMFQ）_200720.csv
# /Volumes/Transcend/data4extraction/NewFolder/output/ookuma_20230905.csv
# /Volumes/Transcend/提供データbackup/20230905_03_大熊彩子_追加/ookuma_20230905.csv
# /Volumes/Transcend/data4extraction/NewFolder/output/sawai_v2_20241126.csv
# /Volumes/Transcend/提供データbackup/20241010_15_臼井香/usui_20241011.csv
# /Volumes/Transcend/提供データbackup/20240402_13_朝重菜々美/tomoshige_20240401.csv
# /Volumes/Transcend/data4extraction/NewFolder/output/takahashi_20231006.csv


# SAMPLENUMBER をインデックスに（既にインデックスなら無視されます）
if "SAMPLENUMBER" in master_df.columns:
    master_df = master_df.set_index("SAMPLENUMBER")
if "SAMPLENUMBER" in subset_df.columns:
    subset_df = subset_df.set_index("SAMPLENUMBER")

# 共通の列・インデックスを抽出
common_cols = master_df.columns.intersection(subset_df.columns)
common_idx = master_df.index.intersection(subset_df.index)

# 比較対象（形・並びを合わせておくのがコツ）
m = master_df.loc[common_idx, common_cols].sort_index().sort_index(axis=1)
s = subset_df.loc[common_idx, common_cols].sort_index().sort_index(axis=1)

# 差分を検出（同一は省略）。列名は 'master' と 'subset' に。
diff = m.compare(
    s,
    align_axis=0,
    keep_shape=False,
    keep_equal=False,
    result_names=("master", "subset"),
)

# 見やすさのためインデックスを列に戻す（必要なら）
diff = diff.reset_index()

print(diff)
diff.to_csv("diff_output.csv", index=False)
print("差分を diff_output.csv に出力しました。")
