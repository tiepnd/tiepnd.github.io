# Blog Phỏng vấn Backend

Web tĩnh trên GitHub Pages. Push lên `main` thì GitHub Actions đóng gói và đăng, sau vài phút web cập nhật. Mỗi sáng lúc 07:05 (giờ VN) workflow cũng chạy lại một lần để bài hẹn ngày tự lên.

## Cấu trúc
```
posts/                      bài viết — mỗi bài là MỘT trong hai dạng:
  <slug>.html                 một file HTML đầy đủ (CSS/JS nhúng sẵn)
  <slug>/index.html           kèm file js/css/ảnh cùng thư mục (đường dẫn tương đối)
site.json                   tên blog, giới thiệu, và từng bài: ngày đăng + link video
scripts/build.py            đóng gói posts/ + site.json → _site/ (trang chủ, 404, sitemap, robots)
.github/workflows/deploy.yml  push / mỗi sáng / bấm tay → build → đăng lên Pages
_site/                      kết quả đóng gói (không commit)
```

## Đăng bài mới
1. Thêm file `posts/<slug>.html`: dán nguyên file HTML vào. Slug thành link `…/<slug>`, chỉ dùng chữ thường không dấu, số và gạch ngang.
2. Thêm bài vào `site.json`:
   ```json
   "posts": {
     "<slug>": { "date": "2026-12-05", "youtube": "", "tiktok": "", "facebook": "" }
   }
   ```
   - `date` để trống = nháp. Ngày tương lai = hẹn ngày, sáng hôm đó bài tự lên. Hôm nay trở về trước = đăng ngay.
   - Không ghi `date` ở đây thì build lấy `<meta name="date" content="…">` trong bài.
3. Commit lên `main`:
   - Trên web GitHub: mở thư mục `posts` → **Add file → Create new file** (dán nội dung) hoặc **Upload files** (kéo file vào) → **Commit changes**. Sửa `site.json`: mở file → bút chì ✎ → sửa → **Commit changes**.
   - Trong Codespace: `git add -A && git commit -m "bài mới" && git push`.

Sau vài phút bài lên; xem tiến độ ở tab **Actions**.

Trang chủ lấy tiêu đề từ `<title>Tiêu đề · Nhóm</title>` (phần sau " · " thành nhãn nhỏ) và mô tả từ `<meta name="description">`.

## Gắn link video (sau khi đăng YouTube / TikTok / Facebook)
Điền vào `site.json` → `posts.<slug>.youtube` / `tiktok` / `facebook`, rồi commit.
- Bài làm bằng bộ bài học (có `<div class="phone" …>`): link YouTube thành video phát ngay trong bài; TikTok và Facebook thành dòng "Xem trên …"; trang chủ gắn nhãn "▶ có video".
- Bài HTML khác: tự dán khung YouTube vào bài:
  ```html
  <iframe src="https://www.youtube-nocookie.com/embed/XXXXXXXXXXX" width="315" height="560" style="border:0" title="Video" allowfullscreen></iframe>
  ```

## Xem thử trước khi đăng (Codespace hoặc máy có Python)
```bash
python3 scripts/build.py && python3 -m http.server -d _site 8000
```
Trong Codespace: khi được hỏi có mở cổng 8000 không, bấm Open in Browser. Không xem thử cũng được: commit xong thì xem thẳng trên web.

## Ghi chú
- Repo phải **public** thì Pages mới chạy trên gói GitHub Free.
- Repo public mà 60 ngày không có commit nào thì GitHub tắt lịch chạy mỗi sáng. Push một commit, hoặc bấm Run workflow, là chạy lại.
- Đổi tên file bài là đổi link, link cũ (trong mô tả video) sẽ hỏng.
- Muốn dùng tên miền riêng: Settings → Pages → Custom domain, rồi điền `url` trong `site.json`.
