import pandas as pd
import re

# ===== 設定 =====
input_csv = "raisho_sample_251022.csv"
output_csv = "output.csv"
deleted_id_csv = "deleted_ids.csv"

# ===== CSV読み込み =====
# ヘッダーがない前提
df = pd.read_csv(input_csv, header=None, dtype=str, encoding="cp932")

# 列名を付与
df.columns = ["来所型ID", "コホート本体ID"]

# 欠損対策
df["来所型ID"] = df["来所型ID"].fillna("")
df["コホート本体ID"] = df["コホート本体ID"].fillna("")

deleted_ids = []

# ===== 1. 「プレ」を含むサンプルナンバーを削除 =====
mask_pre = df["コホート本体ID"].str.contains("プレ", na=False)
deleted_ids.extend(df.loc[mask_pre, "来所型ID"].tolist())
df = df.loc[~mask_pre].copy()

# ===== 2. 来所型IDの数値部分を抽出 =====
def extract_id_number(raisho_id: str) -> int:
    """
    例: EG1234 -> 1234
    数字が取れない場合は非常に大きい値を返して削除対象になりやすくする
    """
    match = re.search(r"(\d+)", raisho_id)
    if match:
        return int(match.group(1))
    return 10**9

df["ID番号"] = df["来所型ID"].apply(extract_id_number)

# ===== 3. サンプルナンバー重複時、ID番号が大きい方を削除 =====
# 各サンプルナンバーごとに最小のID番号を残す
idx_to_keep = df.groupby("コホート本体ID")["ID番号"].idxmin()

# 残す行・削除する行を分ける
df_keep = df.loc[idx_to_keep].copy()
df_delete_dup = df.drop(idx_to_keep).copy()

deleted_ids.extend(df_delete_dup["来所型ID"].tolist())

# ===== 4. 不要列削除 =====
df_keep = df_keep.drop(columns=["ID番号"])

# ===== 5. 結果保存 =====
df_keep.to_csv(output_csv, index=False, header=False, encoding="utf-8-sig")

# 削除した来所型ID一覧を保存
deleted_ids_df = pd.DataFrame({"削除した来所型ID": deleted_ids})
deleted_ids_df.to_csv(deleted_id_csv, index=False, encoding="utf-8-sig")

# ===== 6. 表示 =====
print("処理完了")
print(f"残った件数: {len(df_keep)}")
print(f"削除件数: {len(deleted_ids)}")
print("削除した来所型ID:")
for rid in deleted_ids:
    print(rid)