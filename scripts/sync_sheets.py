#!/usr/bin/env python3
"""
把四份 Google Sheet 匯出成 data/ 底下的 CSV 檔，供 index.html 直接讀取。
由 .github/workflows/sync-sheets.yml 排程執行，不需要手動跑（但也可以手動跑：
見本檔案最下面的「本機測試方式」）。

認證：使用服務帳號 hlddru-sheets-reader@hlddru.iam.gserviceaccount.com。
      這四份 Google Sheet 都必須先「共用」給這個服務帳號的 email，
      權限設為「檢視者」即可，不需要編輯權限。
      服務帳號的金鑰 JSON，整份內容存成 GitHub repo 的 secret：GOOGLE_SERVICE_ACCOUNT_KEY。
      詳細設定步驟見 SETUP.md。
"""
import csv
import io
import json
import os
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# spreadsheetId：Google Sheet 網址中 /d/ 和 /edit 之間那一段。
# sheetName：試算表內該分頁的名稱（使用者說「分頁內容均與檔名相同」，
#            所以這裡填的是 Google Sheet 分頁的名稱，不是輸出的 CSV 檔名）。
# outFile：匯出後寫入 data/ 底下的檔名。
SHEETS = [
    {
        'spreadsheetId': '1PfpINRZEZ8duVSQao7LeCkUqjcW4Ly6R9OyNod7N5dg',
        'sheetName': 'TWN-Lemmata',
        'outFile': 'TWN-Lemmata.csv',
    },
    {
        'spreadsheetId': '1_7ylGQXn49CDqxwd559N2d8iva6lJveqUNjr4UF728M',
        'sheetName': 'TWN_Senses',
        'outFile': 'TWN-Senses.csv',
    },
    {
        'spreadsheetId': '1PDIBQpzsK4L59DQXE4MduBUW0o2rOVXOqV_S8m8I_OE',
        'sheetName': 'TWN-Examples',
        'outFile': 'TWN-Examples.csv',
    },
    {
        'spreadsheetId': '1TkZF2NUeGGMMWel48AMZFZ2uCdjiACh3o3CC0vgvglU',
        'sheetName': 'HLD-Etymology',
        'outFile': 'HLD-Etymology.csv',
    },
]

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')


def get_credentials():
    raw = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY')
    if not raw:
        print('環境變數 GOOGLE_SERVICE_ACCOUNT_KEY 未設定，請確認 GitHub secret 是否已建立。', file=sys.stderr)
        sys.exit(1)
    info = json.loads(raw)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


def fetch_sheet_as_rows(service, spreadsheet_id, sheet_name):
    # 用 sheet_name!A:ZZ 抓整個分頁目前用到的範圍；不用寫死結束列數，
    # Sheets API 會自動只回傳實際有資料的部分。
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!A:ZZ",
        valueRenderOption='FORMATTED_VALUE',
    ).execute()
    return result.get('values', [])


def rows_to_csv_text(rows):
    if not rows:
        return ''
    width = max(len(r) for r in rows)
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator='\n')
    for row in rows:
        padded = row + [''] * (width - len(row))
        writer.writerow(padded)
    return buf.getvalue()


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    changed = []
    for cfg in SHEETS:
        print(f"抓取 {cfg['outFile']}（spreadsheet={cfg['spreadsheetId']}, sheet={cfg['sheetName']}）…")
        try:
            rows = fetch_sheet_as_rows(service, cfg['spreadsheetId'], cfg['sheetName'])
        except Exception as e:
            print(f"  ⚠ 抓取失敗：{e}", file=sys.stderr)
            continue
        csv_text = rows_to_csv_text(rows)
        out_path = os.path.join(DATA_DIR, cfg['outFile'])
        old_text = ''
        if os.path.exists(out_path):
            with open(out_path, encoding='utf-8') as f:
                old_text = f.read()
        if csv_text != old_text:
            with open(out_path, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_text)
            changed.append(cfg['outFile'])
            print(f"  → 已更新（{len(rows)} 列）")
        else:
            print(f"  → 內容無變化（{len(rows)} 列）")

    # 讓 workflow 判斷要不要 commit：有變動時把檔名列表寫進 GITHUB_OUTPUT
    gh_output = os.environ.get('GITHUB_OUTPUT')
    if gh_output:
        with open(gh_output, 'a') as f:
            f.write(f"changed={'1' if changed else ''}\n")
            f.write(f"changed_files={' '.join(changed)}\n")


if __name__ == '__main__':
    main()

# ── 本機測試方式 ──
# 1. pip install google-api-python-client google-auth
# 2. 把服務帳號金鑰 JSON 存成本機檔案，例如 sa-key.json
# 3. export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat sa-key.json)"
# 4. python3 scripts/sync_sheets.py
# 5. 檢查 data/*.csv 是否正確更新
