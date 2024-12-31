from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Path to Chrome binary
chrome_binary_path = "/usr/bin/google-chrome"

# Setup Chrome options and binary location
chrome_options = Options()
chrome_options.binary_location = chrome_binary_path

# Setup Chrome service and driver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
try:
    # Step 1: Login as Médecin
    driver.get("http://127.0.0.1:8000/dossier_patient/login/")
    driver.find_element(By.NAME, "email").send_keys("ma@gmail.com")  # Replace with actual username
    driver.find_element(By.NAME, "password").send_keys("ma")  # Replace with actual password
    driver.find_element(By.NAME, "submit").click()

        # Verify successful login
    WebDriverWait(driver, 10).until(
        EC.url_contains("http://127.0.0.1:8000/dossier_patient/dashboard/")
    )
    print("Login successful. Dashboard loaded.")

    # Step 2: Click "Créer DPI"
    create_dpi_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Créer DPI"))
    )
    create_dpi_button.click()


    # Step 3: Fill out the form
    driver.find_element(By.NAME, "nss").send_keys("1234567")
    driver.find_element(By.NAME, "email").send_keys("pw@gmail.com")
    driver.find_element(By.NAME, "password").send_keys("pw")
    driver.find_element(By.NAME, "nom").send_keys("Lina")
    driver.find_element(By.NAME, "prenom").send_keys("Hamadache")
    driver.find_element(By.NAME, "date_naissance").send_keys("01/01/2000")
    driver.find_element(By.NAME, "adresse").send_keys("123 Street")
    driver.find_element(By.NAME, "telephone").send_keys("0551234567")
    driver.find_element(By.NAME, "mutuelle").send_keys("Cnas")
    driver.find_element(By.NAME, "personne").send_keys("0567887654")

    # Submit the form
    driver.find_element(By.NAME, "submit").click()

        # Step 4: Verify success and redirection back to dashboard
    WebDriverWait(driver, 10).until(
        EC.url_contains("http://127.0.0.1:8000/dossier_patient/dashboard/")
    )
    print("DPI created successfully and redirected to dashboard.")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the browser
    driver.quit()