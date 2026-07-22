import pandas as pd
import re

input_csv = r"D:/ttc5inbody/inbody270_data_第5期のみ_rawdata.csv"
output_csv = "inbody_EG0001_EG0911.csv"

# 削除されたID一覧
deleted_id_csv = "deleted_ids.csv"

# 3桁→4桁に修正したID一覧
corrected_id_csv = "corrected_ids.csv"

df = pd.read_csv(input_csv)

deleted_ids = []
corrected_ids = []


def extract_id(value):
    """
    <1234> や <FGxxxx> の中身を取り出す
    """
    if pd.isna(value):
        return None

    match = re.search(r"<([^<>]+)>", str(value))
    return match.group(1) if match else None


def normalize_numeric_id(inner_id):
    """
    3桁数字なら先頭に0を付与して4桁化
    """
    if re.fullmatch(r"\d{3}", inner_id):
        corrected = inner_id.zfill(4)
        corrected_ids.append({
            "before": inner_id,
            "after": corrected
        })
        return corrected

    return inner_id


def should_delete(value):
    inner_id = extract_id(value)

    if inner_id is None:
        deleted_ids.append(value)
        return True

    # 3桁数字なら4桁へ補正
    inner_id = normalize_numeric_id(inner_id)

    # <FGxxxx> は削除
    if re.fullmatch(r"FG\d{4}", inner_id):
        deleted_ids.append(value)
        return True

    # 4桁数字チェック
    if re.fullmatch(r"\d{4}", inner_id):
        num = int(inner_id)

        # 0001〜0911 以外は削除
        if not (1 <= num <= 911):
            deleted_ids.append(value)
            return True

        return False

    # 想定外形式は削除
    deleted_ids.append(value)
    return True


# 削除判定
delete_mask = df["1. ID"].apply(should_delete)

# 削除ID一覧出力
deleted_df = pd.DataFrame({
    "deleted_id": deleted_ids
})
deleted_df.to_csv(deleted_id_csv, index=False, encoding="utf-8-sig")

# 修正ID一覧出力
corrected_df = pd.DataFrame(corrected_ids)
corrected_df.to_csv(corrected_id_csv, index=False, encoding="utf-8-sig")

# 残す行
df_cleaned = df.loc[~delete_mask].copy()


def create_new_id(value):
    inner_id = extract_id(value)

    # 3桁なら4桁化
    inner_id = normalize_numeric_id(inner_id)

    return f"EG{inner_id}"


# 新しい ID 列を追加
df_cleaned["ID"] = df_cleaned["1. ID"].apply(create_new_id)

# 出力
df_cleaned.to_csv(output_csv, index=False, encoding="utf-8-sig")

print("処理完了")
print(f"出力ファイル: {output_csv}")
print(f"削除ID一覧: {deleted_id_csv}")
print(f"修正ID一覧: {corrected_id_csv}")
