from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time

driver = webdriver.Chrome()

try:
    driver.get("https://stagesync-928b5ae8eae2.herokuapp.com/update-availability")

    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")

    username_input.send_keys("USERNAME")
    password_input.send_keys("PASSWORD")

    # Submit the CAS authentication login
    password_input.send_keys(Keys.RETURN)

    time.sleep(20)  # Give time for duo push and rendering

    # Find the input field and enter bad data
    input_field = driver.find_element(By.NAME, "wednesday_conflicts")
    input_field.send_keys("Not a valid time format")

    # Submit the form
    submit_btn = driver.find_element(By.ID, "saveBtn")
    submit_btn.click()

    # Wait and check for error message
    time.sleep(1)
    error_msg = driver.find_element(By.XPATH, "//*[@role='alert']")
    print(error_msg)


finally:
    driver.quit()
