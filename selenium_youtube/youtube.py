from typing import List, Dict, Optional
import time

from selenium_firefox.firefox import Firefox, By, Keys

YT_URL='https://www.youtube.com'
YT_STUDIO_URL='https://studio.youtube.com'
YT_UPLOAD_URL='https://www.youtube.com/upload'

MAX_TITLE_CHAR_LEN=100
MAX_DESCRIPTION_CHAR_LEN=5000
MAX_TAGS_CHAR_LEN=500

class Youtube:
    def __init__(
        self,
        cookies_folder_path: str,
        extensions_folder_path: str,
        host: Optional[str] = None,
        port: Optional[int] = None
    ):
        self.browser = Firefox(cookies_folder_path, extensions_folder_path, host=host, port=port)

        try:
            self.browser.get(YT_URL)
            time.sleep(1.5)

            if self.browser.has_cookies_for_current_website():
                self.browser.load_cookies()
                time.sleep(1.5)
                self.browser.driver.refresh()
            else:
                input('Log in then press enter')
                self.browser.get(YT_URL)
                time.sleep(1.5)
                self.browser.save_cookies()
        except Exception:
            self.quit()

            raise
    
    def upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str]
    ) -> bool:
        self.browser.driver.get(YT_URL)
        time.sleep(1.5)

        try:
            self.browser.get(YT_UPLOAD_URL)
            time.sleep(1.5)
            self.browser.save_cookies()

            self.browser.find(By.XPATH, "//input[@type='file']").send_keys(video_path) 
            print('Upload: uploaded video')

            title_field = self.browser.find(By.ID, 'textbox')
            title_field.click()
            time.sleep(0.5)
            title_field.clear()
            time.sleep(0.5)
            title_field.send_keys(title)
            print('Upload: added title')

            description_container = self.browser.find(By.XPATH, "/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-details/div/ytcp-uploads-basics/ytcp-mention-textbox[2]")
            description_field = self.browser.find(By.ID, "textbox", element=description_container)
            description_field.click()
            time.sleep(0.5)
            description_field.clear()
            time.sleep(0.5)
            description_field.send_keys(description)
            print('Upload: added desc')

            self.browser.find(By.XPATH, "/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-details/div/div/ytcp-button/div").click()
            print("clicked more options")

            tags_container = self.browser.find(By.XPATH, "/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-details/div/ytcp-uploads-advanced/ytcp-form-input-container/div[1]/div[2]/ytcp-free-text-chip-bar/ytcp-chip-bar/div")
            tags_field = self.browser.find(By.ID, "text-input", tags_container)
            tags_field.send_keys(','.join(tags) + ',')
            print("added tags")

            kids_section = self.browser.find(By.NAME, "NOT_MADE_FOR_KIDS")
            self.browser.find(By.ID, "radioLabel", kids_section).click()

            i=0

            while True:
                try:
                    status_text = self.browser.find(By.XPATH, '/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[2]/div/div[1]/ytcp-video-upload-progress/span').text.lower()

                    if 'process' in status_text:
                        break
                except Exception as e:
                    print(e)
                    
                    i += 1

                    if i >= 4:
                        raise
                
                time.sleep(0.25)
            
            self.browser.find(By.ID, 'next-button').click()
            print('Upload: clicked first next')

            self.browser.find(By.ID, 'next-button').click()
            print('Upload: clicked second next')

            public_main_button = self.browser.find(By.NAME, "PUBLIC")
            self.browser.find(By.ID, 'radioLabel', public_main_button).click()
            print('Upload: set to public')

            self.browser.find(By.ID, 'done-button').click()
            print('Upload: published')

            time.sleep(2.5)
            self.browser.get(YT_URL)

            return True
        except:
            self.browser.get(YT_URL)

            return False
    
    def check_analytics(self) -> None:
        self.browser.get(YT_STUDIO_URL)
    
    def quit(self):
        self.browser.driver.quit()