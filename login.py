from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait 
from selenium.webdriver.common.by import By

CHROMEDRIVER_PATH = 'chromedriver'
CHROME_PROFILES_DIR = 'profiles'
LOGIN_URL = 'https://www.tiktok.com/login/phone-or-email/email'
RELOGIN_URL = 'https://www.tiktok.com/logout?lang=en&redirect_url=https%3A%2F%2Fwww.tiktok.com%2Flogin%2Fphone-or-email%2Femail'

def login(username, password):
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILES_DIR}")
    options.add_argument(f'--profile-directory={username}')
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=options)
    
    driver.get(RELOGIN_URL)

#     username_input = WebDriverWait(driver, 10).until(lambda x: x.find_element(By.NAME, 'username'))
#     password_input = WebDriverWait(driver, 10).until(lambda x: x.find_element(By.XPATH, '//input[@type="password"]'))

#     print(username_input)

#     username_input.send_keys(username)
#     password_input.send_keys(password)

# login_button = WebDriverWait(driver, 10).until(lambda x: x.find_element(By.XPATH, '//button[@data-e2e="login-button"]'))
# login_button.click()





    

    # is_disappeared = WebDriverWait(driver, 30, 1, (ElementNotVisibleException)).\ 

    #             until_not(lambda x: x.find_element(By.ID, "someId").is_displayed())
            


    import code
    code.interact(local=locals())

    import time
    time.sleep(20000)
    
    # return session_id

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="Tiktok account username", required=True)
    parser.add_argument("-p", "--password", help="Tiktok account password", required=True)
    args = parser.parse_args()

    login(username=args.username, password=args.password)


if __name__ == '__main__':
    main()
