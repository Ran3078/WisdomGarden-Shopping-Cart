# 虛擬購物車結算

依促銷折扣與優惠券，計算購物車最終應付金額。

## 功能

- 依結算日套用品類折扣
- 有效期內滿額優惠券（每次結算最多一張）
- 先算品類折扣，再套用優惠券
- 結果四捨五入至小數點 2 位

## 產品目錄

| 品類 | 商品 |
|------|------|
| 電子 | ipad、iphone、顯示器、筆記型電腦、鍵盤 |
| 食品 | 麵包、餅乾、蛋糕、牛肉、魚、蔬菜 |
| 日用品 | 餐巾紙、收納箱、咖啡杯、雨傘 |
| 酒類 | 啤酒、白酒、伏特加 |

## 環境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 使用方式

```powershell
# 互動輸入（貼上後輸入結算日期與優惠券即可）
python shopping_cart.py

# 或從檔案讀取
python shopping_cart.py input.txt
```

### 輸入格式

```
日期|折扣|品類          # 促銷，可多行；沒有則空行
                         # 空行分隔
數量*商品:單價           # 商品，可多行
                         # 空行分隔
結算日期
到期日 門檻 折抵金額     # 優惠券；沒有則空行
```

### 範例

輸入 Case A 後輸出：

```
3083.60
```

## 測試

```powershell
python test_shopping_cart.py
```

或：

```powershell
pytest test_shopping_cart.py -v
```

## CI

Push / Pull Request 時，GitHub Actions 會在 Python 3.11～3.13 自動執行測試。
