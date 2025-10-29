import pandas as pd
from pathlib import Path  # ← 変更: パスはPathlibで安全に扱う
import difflib  # ← 変更: 近い候補の提示用
import re  # ← 変更: 英数字のバリデーション
import shlex  # ← 変更: 追加入力の柔軟な分割に使用
from typing import Optional

# ===== 設定 =====
# 入力：縦並びの項目名（英数字）を記載したテキスト
ITEMS_FILE = Path(r'input.txt')  # ← 変更: 項目名はここから読み込み（1行=1項目）
# CSV/Excelの置き場所
CSV_DIR = Path(r'E:\ttc6sawai')
CSV_GLOB = '*.csv'
XLS_DIR = Path(r'E:\ttc6sawai')
XLS_GLOB = '*.xls*'
# 結合のキー
INDEX_COL = 'SAMPLENUMBER'
# 出力
OUTPUT = Path(r'E:\data_extract\sawai_ace_251022.csv')


# ===== ヘルパ =====
def read_csv_file(path: Path, index_col: Optional[str] = None) -> pd.DataFrame:
    """CSVを読み込む。utf-8→cp932の順でフォールバック。すべて文字列として読む。"""
    try:
        df = pd.read_csv(path, encoding='utf-8', dtype=str, on_bad_lines='skip')  # ← 変更
    except Exception:
        df = pd.read_csv(path, encoding='cp932', dtype=str, on_bad_lines='skip')  # ← 変更
    if index_col and index_col in df.columns:
        df = df.set_index(index_col)  # ← 変更
    return df


def read_excel_file(path: Path, index_col: Optional[str] = None) -> pd.DataFrame:
    """Excelを読み込む。エンジン自動→openpyxl/xlrdの順でフォールバック。"""
    try:
        df = pd.read_excel(path, dtype=str)  # ← 変更
    except Exception:
        try:
            df = pd.read_excel(path, dtype=str, engine='openpyxl')
        except Exception:
            df = pd.read_excel(path, dtype=str, engine='xlrd')
    if index_col and index_col in df.columns:
        df = df.set_index(index_col)  # ← 変更
    return df


def normalize_items_from_text(path: Path) -> list[str]:
    """
    縦並びの項目名を読み込み、スペース区切り（横並び）のリストとして返す。
    - 余分な空白・タブ・カンマも区切りとして解釈（← ブラッシュアップ）
    - 英数字（と _）のみ許可。違反は自動除外＆警告表示（← ブラッシュアップ）
    """
    if not path.exists():
        raise FileNotFoundError(f'項目ファイルが見つかりません: {path}')
    with open(path, 'r', encoding='utf-8') as f:  # ← 変更: エンコーディング明示
        raw = f.read()

    # 改行・タブ・カンマ等をスペースに正規化
    normalized = re.sub(r'[,\t\r\n]+', ' ', raw).strip()  # ← 変更
    if not normalized:
        raise ValueError('項目ファイルが空です。項目名を1行ごとに記載してください。')

    # スペースで分割（英数字＋_のみ残す）
    candidates = normalized.split()
    valid = []
    dropped = []
    for it in candidates:
        if re.fullmatch(r'[A-Za-z0-9_]+', it):  # ← 変更: 英数字のみ想定
            valid.append(it)
        else:
            dropped.append(it)

    if dropped:
        print(f'[警告] 英数字以外を含むため除外: {dropped[:10]}{" ..." if len(dropped) > 10 else ""}')
    # 重複は順序を保って除去
    seen = set()
    deduped = [x for x in valid if not (x in seen or seen.add(x))]  # ← 変更
    return deduped


def maybe_extend_with_manual_input(items: list[str]) -> list[str]:
    """
    追加で手入力したい場合に対応（空Enterでスキップ）。
    手入力はスペース区切り or クオート対応（shlex）。
    もちろん英数字チェックも実施。
    """
    add = input('追加の項目名があれば入力（スペース区切り、空Enterでスキップ）: ').strip()
    if not add:
        return items
    tokens = shlex.split(add)
    extra = []
    for t in tokens:
        if re.fullmatch(r'[A-Za-z0-9_]+', t):
            extra.append(t)
        else:
            print(f'[警告] 英数字以外を含むため除外: {t}')
    merged = items + [x for x in extra if x not in items]  # ← 変更
    return merged


def select_columns_exact(df: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    """
    完全一致で列を抽出（英数字項目名前提）。
    見つからない項目は通知し、近い候補を提示。
    """
    existing = set(df.columns)
    found = [c for c in names if c in existing]
    missing = [c for c in names if c not in existing]

    if missing:
        # 近い候補を提示（各欠損名につき最大3候補）
        suggestions_map = {}
        for m in missing:
            suggestions = difflib.get_close_matches(m, df.columns, n=3, cutoff=0.6)
            if suggestions:
                suggestions_map[m] = suggestions
        print('[注意] 見つからなかった項目:', missing)
        if suggestions_map:
            print('[参考] 近い候補:')
            for k, v in suggestions_map.items():
                print(f'  {k} -> {v}')

    if not found:
        raise KeyError('指定された項目が1つも見つかりませんでした。')

    return df.loc[:, found]


def main():
    # 1) 項目名の読み込み（縦並び→横並び=リスト）
    items = normalize_items_from_text(ITEMS_FILE)  # ← 変更: テキスト→リスト
    print(f'項目（{len(items)}件）: {items[:15]}{" ..." if len(items) > 15 else ""}')

    # 2) 追加入力（任意）
    items = maybe_extend_with_manual_input(items)  # ← 変更: 追加入力サポート
    print(f'最終項目リスト（{len(items)}件）')

    # 3) ファイル収集
    csv_files = sorted(CSV_DIR.glob(CSV_GLOB))
    xls_files = sorted(XLS_DIR.glob(XLS_GLOB))
    if not csv_files and not xls_files:
        raise SystemExit('CSV/Excelファイルが見つかりません。パス/パターンを確認してください。')

    # 4) 読み込み
    dfs = []
    for p in csv_files:
        print(f'[CSV] 読み込み: {p}')
        dfs.append(read_csv_file(p, INDEX_COL))
    for p in xls_files:
        print(f'[XLS] 読み込み: {p}')
        dfs.append(read_excel_file(p, INDEX_COL))

    # 5) 結合（INDEX_COL基準で外部結合）
    df = pd.concat(dfs, axis=1, join='outer')
    # 重複列は先勝ちで落とす
    df = df.loc[:, ~df.columns.duplicated()]  # ← 変更
    print(f'結合後サイズ: {df.shape[0]}行 × {df.shape[1]}列')

    # 6) 列抽出（完全一致）
    result = select_columns_exact(df, items)
    print(f'抽出後サイズ: {result.shape[0]}行 × {result.shape[1]}列')

    # 7) 出力
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)  # ← 変更: 出力フォルダ自動作成
    result.to_csv(OUTPUT, encoding='utf-8', index=True)
    print(f'→ 出力: {OUTPUT}')


if __name__ == '__main__':
    main()
