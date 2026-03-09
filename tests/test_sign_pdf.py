import unittest
import tempfile
import os
import subprocess
import sys
import shutil
import datetime
from reportlab.pdfgen import canvas
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12

class TestSignPDF(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Define paths
        self.pdf_path = os.path.join(self.test_dir, 'sample.pdf')
        self.cert_path = os.path.join(self.test_dir, 'dummy.p12')
        self.password = b'testpassword'
        
        # 1. Create a Sample PDF file
        self.create_sample_pdf(self.pdf_path)
        
        # 2. Create a Dummy Certificate (PKCS#12)
        self.create_dummy_certificate(self.cert_path, self.password)

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)

    def create_sample_pdf(self, path):
        c = canvas.Canvas(path)
        c.drawString(100, 750, "This is a sample PDF generated for testing purposes.")
        c.save()

    def create_dummy_certificate(self, cert_path, password):
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"Dummy Test Certificate"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
        ).not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        ).sign(private_key, hashes.SHA256())
        
        # Serialize to PKCS12 format
        p12 = pkcs12.serialize_key_and_certificates(
            b"test_cert",
            private_key,
            cert,
            None,
            serialization.BestAvailableEncryption(password)
        )
        
        with open(cert_path, "wb") as f:
            f.write(p12)

    def test_sign_and_watermark(self):
        # The main script should be in the directory above `tests`
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sign_pdf.py'))
        # Ensure the script exists
        self.assertTrue(os.path.exists(script_path), f"sign_pdf.py not found at {script_path}")
        
        # 3. Sign the PDF and apply the "testing" watermark
        cmd = [
            sys.executable, script_path, 
            self.pdf_path, 
            self.cert_path, 
            "-p", self.password.decode('utf-8'), 
            "-w", "testing"
        ]
        
        # Run the command using subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Verify that the script executed successfully
        self.assertEqual(result.returncode, 0, f"Script failed with output:\n{result.stderr}\n{result.stdout}")
        
        # Verify the output PDF was created
        name, ext = os.path.splitext(self.pdf_path)
        expected_output = f"{name}_signed{ext}"
        
        self.assertTrue(os.path.exists(expected_output), "Signed PDF was not created.")
        self.assertGreater(os.path.getsize(expected_output), 0, "Signed PDF is empty.")

if __name__ == '__main__':
    unittest.main()
