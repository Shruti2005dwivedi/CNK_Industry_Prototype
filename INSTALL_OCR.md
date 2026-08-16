# 📄 Installing OCR Support for Scanned PDFs

This guide will help you enable OCR (Optical Character Recognition) to process scanned/image PDFs.

## 🔍 What is OCR?

OCR allows the system to extract text from scanned documents and images. Without it, only text-based PDFs will work.

---

## 🪟 **Windows Installation (EASY METHOD)**

### Method 1: Using Chocolatey (Recommended)

1. **Install Chocolatey** (if not already installed):
   - Open PowerShell as Administrator
   - Run:
     ```powershell
     Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
     ```

2. **Install Tesseract**:
   ```powershell
   choco install tesseract
   ```

3. **Restart your terminal/command prompt**

### Method 2: Manual Installation

1. **Download Tesseract**:
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Download: `tesseract-ocr-w64-setup-5.3.3.20231005.exe` (or latest version)

2. **Install**:
   - Run the installer
   - **IMPORTANT**: During installation, note the installation path (usually `C:\Program Files\Tesseract-OCR`)
   - Make sure to check "Add to PATH" option

3. **Add to PATH manually** (if not added during installation):
   - Right-click "This PC" → Properties → Advanced System Settings
   - Click "Environment Variables"
   - Under "System variables", find "Path" and click Edit
   - Click "New" and add: `C:\Program Files\Tesseract-OCR`
   - Click OK on all windows

4. **Verify Installation**:
   Open Command Prompt and run:
   ```cmd
   tesseract --version
   ```
   You should see version information.

---

## 🔄 After Installation

1. **Restart the server**:
   - Stop the current server (Ctrl+C in the terminal running uvicorn)
   - Start again:
     ```bash
     uvicorn app.main:app --reload --port 8000
     ```

2. **Test OCR**:
   - Upload a scanned PDF
   - The system will automatically use OCR to extract text!

---

## ✅ Verification

Run this in Python to check if OCR is working:

```python
import pytesseract
print(pytesseract.get_tesseract_version())
```

If you see a version number, OCR is ready! 🎉

---

## 🆘 Troubleshooting

### "tesseract is not found" error:

1. **Check if installed**:
   ```cmd
   tesseract --version
   ```

2. **Check PATH**:
   ```cmd
   echo %PATH%
   ```
   Should include Tesseract directory.

3. **Restart everything**:
   - Close all terminals
   - Close VS Code / your editor
   - Reopen and try again

### Still not working?

Set Tesseract path manually in the code:
- Open `app/ingestion.py`
- Add at the top:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

---

## 📚 Supported Languages

By default, Tesseract supports English. To add more languages:

```bash
# Install additional language packs during Tesseract installation
# Or download from: https://github.com/tesseract-ocr/tessdata
```

---

## 🎯 After Setup

Your system will now support:
- ✅ Text-based PDFs (already working)
- ✅ Scanned/Image PDFs (with OCR)
- ✅ Mixed PDFs (some pages text, some scanned)

Upload any PDF and the system will automatically detect and process it! 🚀
