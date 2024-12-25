from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import img2pdf

# Kullanıcı giriş bilgileri
DASHBOARD_URL = "https://example-dashboard.com"
EMAIL_ADDRESS = "kullanici@example.com"
PASSWORD = "sifre123"
SENDER_EMAIL = "gonderici@example.com"
SENDER_PASSWORD = "smtp_sifre"
RECEIVER_EMAIL = "alici@example.com"

# Sabit Ayarlar
EXPECTED_DASHBOARD_URL = DASHBOARD_URL
DASHBOARD_TITLE_SELECTOR = "div[uitestid='gwt-debug-inlineEditLabelViewText'][title='Monitoring Overview']"
SCREENSHOT_PATH = "dashboard_screenshot.png"
ERROR_SCREENSHOT_PATH = "final_dashboard.png"
PDF_PATH = "dashboard_screenshot.pdf"

# Chrome Seçenekleri
chrome_options = Options()
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_experimental_option("prefs", {
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

# PNG'yi PDF'ye dönüştürme fonksiyonu
def convert_png_to_pdf(png_path, pdf_path):
    try:
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(png_path))
        print(f"PNG dosyası PDF'ye dönüştürüldü: {pdf_path}")
    except Exception as e:
        print(f"PNG'den PDF'ye dönüştürme sırasında hata: {e}")

# E-posta gönderme fonksiyonu
def send_email(sender_email, sender_password, receiver_email, file_path):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Dynatrace Dashboard Raporu"
    body = "Merhaba,\n\nEkte Dashboardun PDF formatında ekran görüntüsünü bulabilirsiniz.\n\nİyi çalışmalar."
    msg.attach(MIMEText(body, 'plain'))

    with open(file_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={Path(file_path).name}")
        msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("E-posta başarıyla gönderildi.")
    except Exception as e:
        print(f"E-posta gönderme başarısız oldu: {e}")

# Tarayıcıyı başlat
try:
    print("Tarayıcı başlatılıyor...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.maximize_window()
except Exception as e:
    print(f"Tarayıcı başlatılırken hata oluştu: {e}")
    exit()

try:
    # Dashboard URL'sine git
    print("Dashboard URL'sine gidiliyor...")
    driver.get(DASHBOARD_URL)

    # Giriş ekranı kontrolü
    print("Giriş ekranı yükleniyor...")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "email")))

    # E-posta girme
    print("E-posta adresi giriliyor...")
    email_input = driver.find_element(By.NAME, "email")
    email_input.send_keys(EMAIL_ADDRESS)
    email_input.send_keys(Keys.RETURN)

    # Şifre ekranı kontrolü
    print("Şifre ekranı yükleniyor...")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-id='password_login']")))

    # Şifre girme
    print("Şifre giriliyor...")
    password_input = driver.find_element(By.CSS_SELECTOR, "[data-id='password_login']")
    password_input.send_keys(PASSWORD)

    # Giriş butonuna tıklama
    print("Giriş butonuna tıklanıyor...")
    sign_in_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'strato-button-label') and text()='Sign in']"))
    )
    sign_in_button.click()

    # URL kontrolü
    print("Dashboard URL'si kontrol ediliyor...")
    WebDriverWait(driver, 40).until(lambda d: d.current_url == EXPECTED_DASHBOARD_URL)

    # Dashboard başlığı kontrolü
    print("Dashboard başlığı kontrol ediliyor...")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, DASHBOARD_TITLE_SELECTOR))
    )

    # Sayfanın ekran görüntüsü alınıyor
    print("Sayfanın ekran görüntüsü alınıyor...")
    driver.save_screenshot(SCREENSHOT_PATH)
    print(f"Ekran görüntüsü kaydedildi: {SCREENSHOT_PATH}")

    # PNG'yi PDF'ye dönüştür
    convert_png_to_pdf(SCREENSHOT_PATH, PDF_PATH)
    file_to_send = PDF_PATH

except Exception as e:
    print(f"Hata: {e}")
    driver.save_screenshot(ERROR_SCREENSHOT_PATH)
    print(f"Hata durumunda ekran görüntüsü alındı: {ERROR_SCREENSHOT_PATH}")
    # PNG'den PDF'ye dönüştür
    convert_png_to_pdf(ERROR_SCREENSHOT_PATH, PDF_PATH)
    file_to_send = PDF_PATH

finally:
    # E-posta gönderimi
    print("E-posta gönderiliyor...")
    send_email(SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL, file_to_send)

    driver.quit()
    print("Tarayıcı kapatıldı.")
