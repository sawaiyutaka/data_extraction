import pandas as pd

# CSV読み込み
df = pd.read_csv(r"D:\ttc5oct\noise20angio251222.csv")

# L_列とR_列を抽出
l_cols = [c for c in df.columns if c.startswith("L_")]
r_cols = [c for c in df.columns if c.startswith("R_")]

results = []

for _, row in df.iterrows():
    id_ = row["ID"]

    # L_列に 2 or 9 が1つでも含まれる
    if row[l_cols].isin([2, 9]).any():
        results.append(f"{id_}_L")

    # R_列に 2 or 9 が1つでも含まれる
    if row[r_cols].isin([2, 9]).any():
        results.append(f"{id_}_R")

# DataFrame化してCSV出力
out_df = pd.DataFrame(results, columns=["ID"])
out_df.to_csv(r"D:\ttc5oct\blurlist20angio.csv", index=False)
