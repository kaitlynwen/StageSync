from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

driver = webdriver.Chrome()

try:
    driver.get("https://stagesync-928b5ae8eae2.herokuapp.com/generate-schedule")

    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")

    username_input.send_keys("USERNAME")
    password_input.send_keys("PASSWORD")

    # Submit the CAS authentication login
    password_input.send_keys(Keys.RETURN)

    time.sleep(20)  # Give time for duo push and rendering

    # Check if known event actually got rendered
    events = driver.find_elements(By.CLASS_NAME, "fc-timegrid-col-events")
    found = any("Test | NS Warm Up" in event.text for event in events)

    assert found, "Expected event not found on calendar"

finally:
    driver.quit()
