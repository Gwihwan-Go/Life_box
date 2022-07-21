from selenium import webdriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import yaml

def login(Id, password,driver):

    #input : Id and password of user, and driver which is webdriver object
    #output : None
    
    driver.implicitly_wait(4)
    Id_path = '//*[@id="i0116"]'
    Id_ok_path='//*[@id="idSIButton9"]'
    pwd_path = '//*[@id="i0118"]'
    
    driver.find_element(By.XPATH, Id_path).send_keys(Id)
    click_Id_ok_path = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,Id_ok_path)))
    click_Id_ok_path.click()
    driver.find_element(By.XPATH, pwd_path).send_keys(password) 
    time.sleep(1)
    click_to_login = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="idSIButton9"]')))
    click_to_login.click()
    click_to_dismiss = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="idSIButton9"]')))
    click_to_dismiss.click()



with open('config.yaml') as f:
    config = yaml.safe_load(f)
f.close()

option = webdriver.ChromeOptions()
option.add_argument('headless')
url="http://127.0.0.1:5000/login"

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=option)
print(f"accessing to the server={url}")
driver.get(url)
login(config['username'],config['password'],driver)

print(f"server access completed")