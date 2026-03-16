import sys
import os
import datetime
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12

class SignPdfApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sign PDF")
        self.resize(800, 500)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Left Panel (Tabs)
        self.tabs = QTabWidget()
        self.sign_tab = QWidget()
        self.create_cert_tab = QWidget()
        
        self.tabs.addTab(self.sign_tab, "SIGN")
        self.tabs.addTab(self.create_cert_tab, "CREATE CERT")
        
        self.setup_sign_tab()
        self.setup_create_cert_tab()
        
        main_layout.addWidget(self.tabs, stretch=1)
        
        # Right Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.pdf_path_label = QLabel("No PDF selected!")
        self.pdf_path_label.setWordWrap(True)
        self.btn_select_pdf = QPushButton("SELECT PDF TO SIGN")
        self.btn_select_pdf.setMinimumHeight(200)
        self.btn_select_pdf.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.btn_select_pdf.clicked.connect(self.select_pdf)
        
        self.watermark_input = QLineEdit()
        self.watermark_input.setPlaceholderText("WATERMARK TEXT")
        self.watermark_input.setMinimumHeight(40)
        self.watermark_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_sign_mark = QPushButton("SIGN / MARK")
        self.btn_sign_mark.setMinimumHeight(40)
        self.btn_sign_mark.clicked.connect(self.sign_and_mark)
        
        right_layout.addWidget(self.pdf_path_label)
        right_layout.addWidget(self.btn_select_pdf)
        right_layout.addWidget(self.watermark_input)
        right_layout.addStretch()
        right_layout.addWidget(self.btn_sign_mark)
        
        
        main_layout.addWidget(right_panel, stretch=1)
        
        # Applying stylesheet to loosely match testing wireframe feel
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: monospace;
            }
            QPushButton {
                background-color: #3b3b3b;
                border: 1px solid #ffffff;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #ffffff;
                padding: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #ffffff;
            }
            QTabBar::tab {
                background: #3b3b3b;
                border: 1px solid #ffffff;
                padding: 10px;
            }
            QTabBar::tab:selected {
                background: #555555;
            }
            QGroupBox {
                border: 1px solid #ffffff;
                margin-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 5px 5px;
            }
        """)

    def setup_sign_tab(self):
        layout = QVBoxLayout(self.sign_tab)
        
        group = QGroupBox("CERTIFICATE SELECTOR")
        group_layout = QVBoxLayout()
        group_layout.addSpacing(10)
        
        self.cert_path_label = QLabel("No certificate selected!")
        self.cert_path_label.setWordWrap(True)
        self.btn_select_cert = QPushButton("CERT FILE SELECTOR")
        self.btn_select_cert.clicked.connect(self.select_cert)
        
        self.cert_password_input = QLineEdit()
        self.cert_password_input.setPlaceholderText("CERTIFICATE PASSWORD")
        self.cert_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        
        group_layout.addWidget(self.cert_path_label)
        group_layout.addWidget(self.btn_select_cert)
        group_layout.addWidget(self.cert_password_input)
        group.setLayout(group_layout)
        
        #instruction = QLabel("IF TAB SELECTED IS\n\nSIGN ELSE\n\nFORM TO CREATE CERT")
        #instruction.setWordWrap(True)
        #instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(group)
        #layout.addWidget(instruction)
        layout.addStretch()

    def setup_create_cert_tab(self):
        layout = QVBoxLayout(self.create_cert_tab)
        
        self.cn_input = QLineEdit()
        self.cn_input.setPlaceholderText("CN: Common Name (e.g., John Doe)")
        
        self.o_input = QLineEdit()
        self.o_input.setPlaceholderText("O: Organization (e.g., Acme Corp)")
        
        self.c_input = QLineEdit()
        self.c_input.setPlaceholderText("C: Country (e.g., US)")
        
        self.e_input = QLineEdit()
        self.e_input.setPlaceholderText("E: Email Address (e.g., john@example.com)")
        
        self.create_password_input = QLineEdit()
        self.create_password_input.setPlaceholderText("Certificate Password")
        self.create_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.btn_choose_save_loc = QPushButton("Choose Save Location")
        self.btn_choose_save_loc.clicked.connect(self.choose_save_location)
        self.save_loc_label = QLabel("Save Location: Not selected")
        self.save_loc_label.setWordWrap(True)
        
        self.btn_create_cert = QPushButton("CREATE CERTIFICATE")
        self.btn_create_cert.clicked.connect(self.create_certificate)
        
        layout.addWidget(self.cn_input)
        layout.addWidget(self.o_input)
        layout.addWidget(self.c_input)
        layout.addWidget(self.e_input)
        layout.addWidget(self.create_password_input)
        layout.addSpacing(10)
        layout.addStretch()
        layout.addWidget(self.btn_choose_save_loc)
        layout.addWidget(self.save_loc_label)
        layout.addSpacing(10)
        layout.addWidget(self.btn_create_cert)
        

    def select_pdf(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.pdf_path = file
            self.pdf_path_label.setText(f"Selected: {os.path.basename(file)}")
            self.btn_select_pdf.setText(f"Selected:\n{os.path.basename(file)}")

    def select_cert(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Certificate", "", "Certificate Files (*.p12 *.pfx)")
        if file:
            self.cert_path = file
            self.cert_path_label.setText(f"Selected: {os.path.basename(file)}")

    def choose_save_location(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save Certificate As", "", "PKCS12 File (*.p12)")
        if file:
            if not file.endswith('.p12'):
                file += '.p12'
            self.save_cert_path = file
            self.save_loc_label.setText(f"Save Location: {file}")

    def create_certificate(self):
        if not hasattr(self, 'save_cert_path') or not self.save_cert_path:
            QMessageBox.warning(self, "Error", "Please select a save location.")
            return
            
        cn = self.cn_input.text()
        if not cn:
            QMessageBox.warning(self, "Error", "Common Name (CN) is required.")
            return
            
        password = self.create_password_input.text()
        if not password:
            QMessageBox.warning(self, "Error", "Password is required for the certificate.")
            return

        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            attributes = [x509.NameAttribute(NameOID.COMMON_NAME, cn)]
            
            if self.o_input.text():
                attributes.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.o_input.text()))
            if self.c_input.text():
                attributes.append(x509.NameAttribute(NameOID.COUNTRY_NAME, self.c_input.text()))
            if self.e_input.text():
                attributes.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, self.e_input.text()))
                
            subject = issuer = x509.Name(attributes)
            
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
                datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
            ).add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=True
            ).add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=True,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False
                ), critical=True
            ).sign(private_key, hashes.SHA256())
            
            p12 = pkcs12.serialize_key_and_certificates(
                b"certificate",
                private_key,
                cert,
                None,
                serialization.BestAvailableEncryption(password.encode('utf-8'))
            )
            
            with open(self.save_cert_path, "wb") as f:
                f.write(p12)
                
            QMessageBox.information(self, "Success", f"Certificate successfully created at:\n{self.save_cert_path}")
            
            # Switch to SIGN tab and auto-select this file
            self.tabs.setCurrentIndex(0)
            self.cert_path = self.save_cert_path
            self.cert_path_label.setText(f"Selected: {os.path.basename(self.save_cert_path)}")
            # For convenience, pre-fill the password if we just created it
            self.cert_password_input.setText(password)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create certificate:\n{str(e)}")

    def sign_and_mark(self):
        if not hasattr(self, 'pdf_path') or not self.pdf_path:
            QMessageBox.warning(self, "Error", "Please select a PDF file in the right panel.")
            return
            
        if self.tabs.currentIndex() != 0:
            QMessageBox.warning(self, "Information", "Please ensure the SIGN tab is selected, a certificate is provided, and click SIGN & MARK again.")
            self.tabs.setCurrentIndex(0)
            return

        if not hasattr(self, 'cert_path') or not self.cert_path:
            QMessageBox.warning(self, "Error", "Please select a Certificate file in the SIGN tab.")
            return
            
        password = self.cert_password_input.text()
        watermark = self.watermark_input.text()
        
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sign_pdf.py')
        
        if not os.path.exists(script_path):
            QMessageBox.critical(self, "Error", f"Could not find sign_pdf.py at {script_path}")
            return
            
        cmd = [
            sys.executable,
            script_path,
            self.pdf_path,
            self.cert_path,
            "-p", password
        ]
        
        if watermark:
            cmd.extend(["-w", watermark])
            
        try:
            # We use subprocess.run to execute it synchronously
            self.btn_sign_mark.setText("SIGNING...")
            self.btn_sign_mark.setEnabled(False)
            QApplication.processEvents()
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            self.btn_sign_mark.setText("SIGN & MARK")
            self.btn_sign_mark.setEnabled(True)
            
            if result.returncode == 0:
                name, ext = os.path.splitext(self.pdf_path)
                out_path = f"{name}_signed{ext}"
                QMessageBox.information(self, "Success", f"Successfully signed and marked!\nSaved to: {out_path}")
            else:
                QMessageBox.critical(self, "Error", f"Script failed:\n{result.stderr}\n{result.stdout}")
        except Exception as e:
            self.btn_sign_mark.setText("SIGN & MARK")
            self.btn_sign_mark.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Failed to run script:\n{str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SignPdfApp()
    window.show()
    sys.exit(app.exec())
