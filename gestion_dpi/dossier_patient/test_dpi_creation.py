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
    """
    Log in as Médecin on the web application.
    
    This step involves opening the login page, entering email and password, 
    and clicking the login button. Afterward, the successful login is verified 
    by checking if the dashboard page is loaded.
    """
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

    """
    Navigate to the 'Créer DPI' page and wait for the button to appear.

    This step clicks on the "Créer DPI" link once it becomes visible.
    """
    # Step 2: Click "Créer DPI"
    create_dpi_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Créer DPI"))
    )
    create_dpi_button.click()

    """
    Fill out the form for creating a new DPI.
    
    This includes entering personal details such as NSS, email, password, name, 
    date of birth, address, phone number, insurance, and emergency contact.
    """
    # Step 3: Fill out the form
    driver.find_element(By.NAME, "nss").send_keys("12345627")
    driver.find_element(By.NAME, "email").send_keys("paa@gmail.com")
    driver.find_element(By.NAME, "password").send_keys("paa")
    driver.find_element(By.NAME, "nom").send_keys("Linaa")
    driver.find_element(By.NAME, "prenom").send_keys("Hamadachee")
    driver.find_element(By.NAME, "date_naissance").send_keys("02/01/2000")
    driver.find_element(By.NAME, "adresse").send_keys("123 Street")
    driver.find_element(By.NAME, "telephone").send_keys("0551234597")
    driver.find_element(By.NAME, "mutuelle").send_keys("Cnas")
    driver.find_element(By.NAME, "personne").send_keys("0567987654")

    # Submit the form
    driver.find_element(By.NAME, "submit").click()

    """
    Verify successful creation of DPI and redirection back to the dashboard.

    After submitting the form, the script waits for the page to reload and verifies
    that the user is redirected to the dashboard.
    """
    # Step 4: Verify success and redirection back to dashboard
    WebDriverWait(driver, 10).until(
        EC.url_contains("http://127.0.0.1:8000/dossier_patient/dashboard/")
    )
    print("DPI created successfully and redirected to dashboard.")

except Exception as e:
    """
    Catch and print any exception that occurs during the process.

    If an error occurs in any of the steps, the exception message is printed.
    """
    print(f"An error occurred: {e}")

finally:
    """
    Close the browser after the process is completed.

    Ensures the browser is properly closed regardless of success or failure.
    """
    driver.quit()
