from selenium import webdriver
from selenium.webdriver.chrome.service import Service


WEBDRIVERPATH = "U:\\InstalledApp\\Work\\AppData\\ChromeDriver-Win64\\chromedriver.exe"
PROFILEPATH = "U:\\DataStorage\\UIT\\Semesters\\Semester6\\DS200\\CourseProject\\SourceCode\\data_collector\\profile"


def set_up_driver():
    """Set up and return a Chrome WebDriver."""
    service = Service(executable_path=WEBDRIVERPATH)

    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=960,1080")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-data-dir={PROFILEPATH}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=service, options=options)

    return driver
