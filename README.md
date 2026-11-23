# Duel Editor AI — Windows Portable build

## Mục tiêu
Tạo bản Windows Portable bằng GitHub Actions. Máy người dùng không cần tự cài Python.

## Cách đưa dự án lên GitHub
1. Giải nén ZIP này trên máy tính.
2. Mở repository `https://github.com/dragongann132-cyber/DuelEditorAI`.
3. Chọn **Add file → Upload files**.
4. Tải lên `app.py`, `launcher.py`, `requirements.txt` và thư mục `.github/workflows/`.
   - Nếu giao diện không nhận thư mục `.github`, hãy tạo file mới trên GitHub với đường dẫn `.github/workflows/build-windows.yml`, rồi sao chép nội dung file cùng tên trong ZIP.
5. Commit changes vào nhánh `main`.

## Lấy bản EXE
1. Mở tab **Actions** của repository.
2. Chọn workflow **Build Duel Editor AI for Windows**.
3. Chờ workflow hoàn tất màu xanh.
4. Mở lần chạy mới nhất, kéo xuống **Artifacts** và tải `DuelEditorAI-Windows-Portable`.
5. Giải nén ZIP. Chạy `DuelEditorAI.exe` bên trong thư mục `DuelEditorAI`.

Đây là bản Portable dạng thư mục: cần giữ nguyên toàn bộ các tệp cạnh `DuelEditorAI.exe`, không chỉ chép riêng file EXE.

## Lưu ý lần chạy đầu
- Windows có thể hiện cảnh báo SmartScreen vì đây là ứng dụng tự biên dịch, chưa có chữ ký số.
- Lần đầu nhận diện giọng nói, faster-whisper tải mô hình từ Hugging Face; cần Internet và có thể mất thời gian.
- Nên dùng CPU và model `small` trước. GPU chưa được bật mặc định.
- Video, audio và kết quả dự án được lưu cục bộ trong `%USERPROFILE%\\DuelEditorAI\\projects`.
- Ứng dụng hiện chỉ tách âm thanh, nhận diện lời thoại, gắn cờ từ đệm và xuất JSON/SRT. Chưa tự động xóa từ đệm hay dựng video hoàn chỉnh.

## Nếu build lỗi
Mở tab Actions, chọn lần chạy bị lỗi, sao chép phần log màu đỏ hoặc chụp ảnh gửi lại để được hỗ trợ.
