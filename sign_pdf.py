import argparse
import sys
import os
import tempfile

try:
    from pyhanko.sign import signers
    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
except ImportError:
    print("Error: pyhanko is not installed.", file=sys.stderr)
    print("Please install it using: pip install pyHanko", file=sys.stderr)
    sys.exit(1)

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import Color
    from pypdf import PdfReader, PdfWriter
    WATERMARK_SUPPORTED = True
except ImportError:
    WATERMARK_SUPPORTED = False

def create_watermark(watermark_text, output_pdf_path):
    c = canvas.Canvas(output_pdf_path)
    c.setFont("Helvetica", 14)
    c.setFillColor(Color(0.5, 0.5, 0.5, alpha=0.3)) # Grey with transparency

    # Rotate 45 degrees
    c.rotate(45)
    
    # Draw repeated watermark across a wide coordinate range to cover the page
    start_x = -1000
    end_x = 1500
    start_y = -1000
    end_y = 1500
    
    # Adjust spacing between repeats dynamically based on text length
    text_width = c.stringWidth(watermark_text, "Helvetica", 14)
    step_x = int(text_width + 50)  # text width plus 50px padding
    step_y = 250
    
    for x in range(start_x, end_x, step_x):
        for y in range(start_y, end_y, step_y):
            c.drawString(x, y, watermark_text)
    
    c.save()

def add_watermark_to_pdf(input_pdf_path, output_pdf_path, watermark_text):
    if not WATERMARK_SUPPORTED:
        print("Error: reportlab and pypdf are required for watermarking.", file=sys.stderr)
        print("Install them using: pip install reportlab pypdf", file=sys.stderr)
        sys.exit(1)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_wm:
        wm_path = tmp_wm.name
        
    try:
        create_watermark(watermark_text, wm_path)
        
        reader = PdfReader(input_pdf_path)
        writer = PdfWriter()
        wm_reader = PdfReader(wm_path)
        wm_page = wm_reader.pages[0]

        for page in reader.pages:
            # Merge the watermark onto the page
            page.merge_page(wm_page)
            writer.add_page(page)

        with open(output_pdf_path, "wb") as f:
            writer.write(f)
    finally:
        if os.path.exists(wm_path):
            os.remove(wm_path)

def sign_pdf(input_path, cert_path, password, watermark_text=None):
    """
    Signs a PDF file using a PKCS#12 certificate (.p12 or .pfx).
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)
        
    name, ext = os.path.splitext(input_path)
    output_path = f"{name}_signed{ext}"
        
    if not os.path.exists(cert_path):
        print(f"Error: Certificate file '{cert_path}' not found.", file=sys.stderr)
        sys.exit(1)
        
    file_to_sign = input_path
    temp_watermarked_file = None
    
    if watermark_text:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            temp_watermarked_file = tmp.name
        try:
            print(f"Adding watermark: '{watermark_text}'...")
            add_watermark_to_pdf(input_path, temp_watermarked_file, watermark_text)
            file_to_sign = temp_watermarked_file
        except Exception as e:
            print(f"Error adding watermark: {e}", file=sys.stderr)
            if temp_watermarked_file and os.path.exists(temp_watermarked_file):
                os.remove(temp_watermarked_file)
            sys.exit(1)

    try:
        # Load the PKCS12 certificate
        password_bytes = password.encode('utf-8') if password else b''
        signer = signers.SimpleSigner.load_pkcs12(cert_path, passphrase=password_bytes)
    except Exception as e:
        print(f"Error loading certificate (is the password correct?): {e}", file=sys.stderr)
        if temp_watermarked_file and os.path.exists(temp_watermarked_file):
            os.remove(temp_watermarked_file)
        sys.exit(1)
        
    try:
        with open(file_to_sign, 'rb') as doc:
            # Incremental writer is required for signing to avoid invalidating 
            # the document structure or any prior signatures.
            w = IncrementalPdfFileWriter(doc)
            
            with open(output_path, 'wb') as out_file:
                signers.sign_pdf(
                    w,
                    signers.PdfSignatureMetadata(field_name='Signature1'),
                    signer=signer,
                    output=out_file
                )
        print(f"Success: Signed PDF saved to '{output_path}'")
    except Exception as e:
        print(f"Error during PDF signing: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up temporary watermarked file if we created one
        if temp_watermarked_file and os.path.exists(temp_watermarked_file):
            os.remove(temp_watermarked_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Sign a PDF document digitally using a PKCS#12 certificate (.p12 or .pfx).",
        epilog="""
Requirements:
  pip install pyHanko reportlab pypdf

Example usage:
  python sign_pdf.py document.pdf mycert.p12 -p my_cert_password
  python sign_pdf.py document.pdf mycert.p12 -p my_cert_password -w "CONFIDENTIAL"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("input_pdf", help="Path to the input PDF file to be signed")
    parser.add_argument("cert", help="Path to the PKCS#12 certificate file (.p12/.pfx)")
    parser.add_argument("-p", "--password", default="", help="Password for the PKCS#12 certificate (if any)")
    parser.add_argument("-w", "--watermark", default="", help="Text to use as a diagonal watermark")
    
    args = parser.parse_args()
    
    sign_pdf(args.input_pdf, args.cert, args.password, args.watermark)
