# PDF Signer

A python script to digitally sign PDF documents using a PKCS#12 certificate (.p12 or .pfx).

## Setup
1. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
```
2. Activate the virtual environment:
- **Windows:**
```powershell
.\venv\Scripts\Activate.ps1
```
- **Linux/macOS:**
```bash
source venv/bin/activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Creating a Test Certificate
If you do not have a digital certificate, you can generate a free, self-signed certificate for testing purposes.

### Option A: Windows (PowerShell)
Run these commands in PowerShell to create and export a certificate:

The format `-Subject "CN=John Doe, O=Acme Corp, C=US, E=john@example.com"` allows you to specify:
*   `CN`: Common Name (e.g., John Doe)
*   `O`: Organization (e.g., Acme Corp)
*   `C`: Country (e.g., US)
*   `E`: Email Address (e.g., john@example.com)

```powershell
$cert = New-SelfSignedCertificate -Subject "CN=John Doe, O=Acme Corp, C=US, E=john@example.com" -CertStoreLocation "Cert:\CurrentUser\My" -KeyExportPolicy Exportable -KeySpec Signature -KeyAlgorithm RSA -KeyLength 4096 -NotAfter (Get-Date).AddDays(365)
$pwd = ConvertTo-SecureString -String 'password' -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath 'mycert.p12' -Password $pwd
```
*(This will generate a `mycert.p12` file with the password `password` in your current directory.)*

### Option B: Linux / macOS (OpenSSL)
If you have OpenSSL installed, you can generate a certificate using these commands (it will prompt you to enter the CN, O, C, etc., or you can pass them inline):
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=John Doe/O=Acme Corp/C=US/emailAddress=john@example.com"
openssl pkcs12 -export -out mycert.p12 -inkey key.pem -in cert.pem -passout pass:password
```

## Usage
Run the script providing the input PDF, certificate path, and password. The application will output a signed version with a `_signed` suffix.

```bash
python sign_pdf.py document.pdf mycert.p12 -p password
```
This automatically takes the input file (`document.pdf`) and produces a signed copy named `document_signed.pdf` in the same directory.

### Adding a Watermark
You can optionally add a diagonal watermark text to the signed PDF using the `-w` or `--watermark` argument:
```bash
python sign_pdf.py document.pdf mycert.p12 -p password -w "CONFIDENTIAL"
```
