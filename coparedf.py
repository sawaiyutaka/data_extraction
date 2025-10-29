import datacompy
import pandas as pd

# 読み込み
master = pd.read_csv(r"C:\Users\sawai\PycharmProjects\ace_ple\sawai_ace_3171_251022.csv")
master = master.set_index("SAMPLENUMBER")
subset = pd.read_csv(r"C:\Users\sawai\PycharmProjects\ace_ple\sawai_ace_3171_251022.csv")
subset = subset.set_index("SAMPLENUMBER")

# master.index.name == subset.index.name == "SAMPLENUMBER"

# 1) 行は SAMPLENUMBER の共通集合だけに限定
common_idx = master.index.intersection(subset.index)
master_aligned = master.loc[common_idx].copy()
subset_aligned = subset.loc[common_idx].copy()

# 2) 列は subset にある列のうち master にもある列だけに限定
common_cols = subset_aligned.columns.intersection(master_aligned.columns)
master_use = master_aligned[common_cols].copy()
subset_use = subset_aligned[common_cols].copy()

# 3) datacompy で比較するため、SAMPLENUMBER を列に戻す（join_columnsで使うため）
master_use = master_use.reset_index()  # SAMPLENUMBER が列になる
subset_use = subset_use.reset_index()

# 4) 比較（数値誤差を許さない完全一致。必要なら abs_tol / rel_tol を調整）
compare = datacompy.Compare(
    master_use,
    subset_use,
    join_columns="SAMPLENUMBER",  # キーは SAMPLENUMBER
    abs_tol=0,
    rel_tol=0,
    df1_name="master",
    df2_name="subset"
)

# 5) 判定（True ならズレなし）
print("完全一致？ ->", compare.matches())

# 6) 詳細レポート（どの行・列にズレがあるか等をテキストで確認）
print(compare.report())
