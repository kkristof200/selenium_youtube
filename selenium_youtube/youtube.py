from typing import List, Dict, Optional, NoReturn
import time

from selenium_firefox.firefox import Firefox, By, Keys

YT_URL='https://www.youtube.com'
YT_STUDIO_URL='https://studio.youtube.com'
YT_UPLOAD_URL='https://www.youtube.com/upload'

MAX_TITLE_CHAR_LEN=100
MAX_DESCRIPTION_CHAR_LEN=5000
MAX_TAGS_CHAR_LEN=500

def upload(
    user_id: str,
    video_path: str,
    title: str,
    description: str,
    tags: List[str],
    host: Optional[str] = None,
    port: Optional[int] = None
):
    browser = Firefox(user_id, host=host, port=port)

    browser.driver.get(YT_URL)
    time.sleep(1.5)
    browser.load_cookies()
    time.sleep(1.5)
    browser.driver.refresh()
    time.sleep(2)

    print('Upload: refreshed page and logged in')
    browser.driver.get(YT_UPLOAD_URL)
    time.sleep(1.5)
    browser.save_cookies()

    browser.find(By.XPATH, "//input[@type='file']").send_keys(video_path) 
    print('Upload: uploaded video')

    title_field = browser.find(By.ID, 'textbox')
    title_field.click()
    time.sleep(0.5)
    title_field.clear()
    time.sleep(0.5)
    title_field.send_keys(title)
    print('Upload: added title')

    description_container = browser.find(By.XPATH, "/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-details/div/ytcp-uploads-basics/ytcp-mention-textbox[2]")
    description_field = browser.find(By.ID, "textbox", element=description_container)
    description_field.click()
    time.sleep(0.5)
    description_field.clear()
    time.sleep(0.5)
    description_field.send_keys(description)
    print('Upload: added desc')

    browser.find(By.XPATH, "/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-details/div/div/ytcp-button/div").click()
    print("clicked more options")

    tags_container = browser.find(By.XPATH, "/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-details/div/ytcp-uploads-advanced/ytcp-form-input-container/div[1]/div[2]/ytcp-free-text-chip-bar/ytcp-chip-bar/div")
    tags_field = browser.find(By.ID, "text-input", tags_container)
    tags_field.send_keys(','.join(tags) + ',')
    print("added tags")

    kids_section = browser.find(By.NAME, "NOT_MADE_FOR_KIDS")
    browser.find(By.ID, "radioLabel", kids_section).click()

    i=0

    while True:
        try:
            status_text = browser.find(By.XPATH, '/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[2]/div/div[1]/ytcp-video-upload-progress/span').text.lower()

            if 'process' in status_text:
                break
        except Exception as e:
            print(e)
            
            i += 1

            if i >= 4:
                raise
        
        time.sleep(0.25)
    
    browser.find(By.ID, 'next-button').click()
    print('Upload: clicked first next')

    browser.find(By.ID, 'next-button').click()
    print('Upload: clicked second next')

    public_main_button = browser.find(By.NAME, "PUBLIC")
    browser.find(By.ID, 'radioLabel', public_main_button).click()
    print('Upload: set to public')

    browser.find(By.ID, 'done-button').click()
    print('Upload: published')

    time.sleep(5)
    browser.driver.quit()

def login(
    id: str,
    host: str,
    port: int
) -> NoReturn:
    browser = Firefox(id, host=host, port=port)
    browser.driver.get(YT_URL)
    input('log in and enter: ')
    browser.driver.get(YT_URL)
    time.sleep(1)
    browser.save_cookies()
    time.sleep(2)
    browser.driver.quit()

def check_on_channel(
    id: str,
    host: str,
    port: int
) -> NoReturn:
    browser = Firefox(id, host=host, port=port)
    browser.driver.get(YT_URL)
    browser.load_cookies()
    browser.driver.get(YT_STUDIO_URL)