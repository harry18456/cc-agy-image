# agy-image

讓 Claude Code 用**本機 `agy` CLI**(Antigravity / Gemini「Nano Banana」)直接生圖、改圖 —— 全程本地、**免 API key**。
需要透明背景時,再用本地 `rembg` 做語意去背,產出**真正帶 alpha** 的 PNG(agy 本身只會畫假棋盤格 / 白底)。

裝好後用自然語言叫圖就會觸發,不必記指令:

- 「幫我畫一張直式活動海報,標題寫『立即啟用』…」
- 「畫個 app icon,扁平風格」
- 「把這張圖去背,存成透明 PNG」
- 「照這張吉祥物的樣子,做一張春節賀圖」(參考圖)

特色:

- **文字海報一次到位**:標題、內文、按鈕文字直接生成在圖裡,中文 OK(已驗證含密集文字排版)
- **`--ref` 參考圖**:成品忠實重現既有吉祥物 / 產品 / logo 的造型
- **`--transparent` 真去背**:rembg(u2net)語意分割,不需要乾淨純色底

> ⚠️ **僅支援 Windows**。headless 驅動 agy 需要 ConPTY(pywinpty);一般 subprocess pipe 會直接 hang。

## 需求

- Windows + Python 3
- 已安裝並登入過 `agy` CLI(Google Antigravity),且 `agy` 在 PATH 上
- Claude Code

## 安裝

```
/plugin marketplace add harry18456/cc
/plugin install agy-image@harry18456
```

重開 Claude Code 生效。

### 本機立即使用(免 push、免 marketplace)

把 skill 目錄以 junction 連進 skills 目錄,下個 session 就會載入:

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\agy-image" -Target "<這個 repo 的路徑>\skills\agy-image"
```

## 第一次使用注意

- 第一次執行會自動 `pip install pywinpty pillow`(裝進執行 script 的那個 Python)。
- 第一次用**去背**會自動安裝 `rembg + onnxruntime`,並下載約 **176MB** 的 u2net 模型到 `~/.u2net/` —— 第一張透明圖會等比較久。
- 生成一張圖通常 1~3 分鐘(agy 本身的速度),輸出約 1024px 等級的 PNG;要精確尺寸請事後自行 resize。

## 運作方式

`skills/agy-image/scripts/agy_image.py` 一支 script 包辦全部:

1. 用 ConPTY(pywinpty)驅動 `agy` —— agy 的 print 模式需要真 console。
2. headless 配方:`--add-dir <輸出目錄> --sandbox`,並指示 agy 一次直接生成存檔、不列計畫、不等確認。
3. agy 常把檔案存進 `~/.gemini/antigravity*/brain|scratch` 而不是指定路徑,script 會找出本次真正的成品(排除縮圖與中間產物)複製到 `--out`。
4. `--transparent` 再過一次本地 rembg,輸出真 alpha PNG。

已知行為:agy 結尾幾乎必印 `Error: timed out waiting for response`,**成功時也會印** —— 一切以 script 最後的 `OK / FAILED` 判定為準。

## 安全性

- prompt 一律走暫存檔傳遞,不做 shell 內插(inject-safe)。
- agy 以 `--sandbox` 執行。
- 每次呼叫仍會經過 Claude Code 的 Bash 權限確認;建議**不要**把 `agy` 或這支 script 加進 auto-approve allowlist,讓每次生成都是有意識的動作。

## 本地開發 / 測試

不必先推上 GitHub,直接載入這個資料夾:

```
claude --plugin-dir <這個 repo 的路徑>
```

## License

MIT
