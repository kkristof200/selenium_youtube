from typing import List, Dict, Optional
import time, json

from selenium_firefox.firefox import Firefox, By, Keys
from ktimeout import timeout

from bs4 import BeautifulSoup as bs

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
                self.browser.refresh()
            else:
                input('Log in then press enter')
                self.browser.get(YT_URL)
                time.sleep(1.5)
                self.browser.save_cookies()
            
            self.channel_id = self.get_current_channel_id()
        except Exception as e:
            print(e)
            self.quit()

            raise

    def upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        _timeout: Optional[int] = 60*3 # 3 min
    ) -> (bool, Optional[str]):
        if _timeout is not None:
            try:
                return timeout.run(
                    timeout.partial(self.__upload, video_path, title, description, tags),
                    _timeout
                )
            except Exception as e:
                print(e)
                self.browser.get(YT_URL)

                return False, None
        else:
            return self.__upload(video_path, title, description, tags)

    def get_current_channel_id(self) -> Optional[str]:
        try:
            return json.loads(
                strings.between(
                    self.browser.driver.page_source, 'var ytInitialGuideData = ', '};'
                ) + '}'
            )['responseContext']['serviceTrackingParams'][2]['params'][0]['value']
        except:
            return None

    def load_video(self, video_id: str):
        self.browser.get(self.__video_url(video_id))

    def comment_on_video(self, video_id: str, comment: str, pinned: bool = False) -> bool:
        self.load_video(video_id)

        try:
            self.browser.scroll(350)

            self.browser.find(By.XPATH, "//div[@id='placeholder-area']").click()
            self.browser.find(By.XPATH, "//div[@id='contenteditable-root']").send_keys(comment)
            self.browser.find(By.XPATH, "//ytd-button-renderer[@id='submit-button' and @class='style-scope ytd-commentbox style-primary size-default']").click()

            if not pinned:
                return True

            we = self.browser.find(By.CLASS_NAME, 'style-scope.ytd-comment-renderer')
            self.browser.find(By.CLASS_NAME, 'dropdown-trigger.style-scope.ytd-menu-renderer', element=we).click()

            we2 = self.browser.find(By.CLASS_NAME, 'style-scope.ytd-menu-popup-renderer')
            self.browser.find(By.CLASS_NAME, 'yt-simple-endpoint.style-scope.ytd-menu-navigation-item-renderer', element=we2).click()

            we3 = self.browser.find(By.XPATH, "//yt-confirm-dialog-renderer[@class='style-scope ytd-popup-container']")
            self.browser.find(By.XPATH, "//paper-button[@id='button' and @class='style-scope yt-button-renderer style-primary size-default']", element=we3).click()

            return True
        except Exception as e:
            print(e)

            return False
    
    def get_channel_video_ids(self, channel_id: Optional[str] = None) -> List[str]:
        video_ids = []

        channel_id = channel_id or self.channel_id

        try:
            self.browser.get(self.__channel_videos_url(channel_id))
            y = None
            new_y = self.browser.current_page_offset_y()

            while y != new_y:
                y = new_y
                self.browser.scroll(1500)
                time.sleep(2)
                new_y = self.browser.current_page_offset_y()
                print('new_y', new_y)

            soup = bs(self.browser.driver.page_source, 'lxml')
            elems = soup.find_all('a', {'id':'thumbnail', 'class':'yt-simple-endpoint inline-block style-scope ytd-thumbnail'})

            for elem in elems:
                if 'href' in elem.attrs and '/watch?v=' in elem['href']:
                    video_ids.append(elem['href'].strip('/watch?v='))
        except:
            pass

        return video_ids

    def check_analytics(self) -> bool:
        self.browser.get(YT_STUDIO_URL)

        try:
            self.browser.get(self.browser.find(By.XPATH, "//a[@id='menu-item-3']").get_attribute('href'))

            return True
        except Exception as e:
            print(e)

            return False

    def quit(self):
        self.browser.driver.quit()

    def __upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str]
    ) -> (bool, Optional[str]):
        self.browser.get(YT_URL)
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
            title_field.send_keys(Keys.COMMAND + 'a')
            time.sleep(0.5)
            title_field.send_keys(title[:MAX_TITLE_CHAR_LEN])
            print('Upload: added title')
            description_container = self.browser.find(By.XPATH, "/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-details/div/ytcp-uploads-basics/ytcp-mention-textbox[2]")
            description_field = self.browser.find(By.ID, "textbox", element=description_container)
            description_field.click()
            time.sleep(0.5)
            description_field.clear()
            time.sleep(0.5)
            description_field.send_keys(description[:MAX_DESCRIPTION_CHAR_LEN])

            print('Upload: added description')

            self.browser.find(By.XPATH, "/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-details/div/div/ytcp-button/div").click()
            print("Upload: clicked more options")

            tags_container = self.browser.find(By.XPATH, "/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-details/div/ytcp-uploads-advanced/ytcp-form-input-container/div[1]/div[2]/ytcp-free-text-chip-bar/ytcp-chip-bar/div")
            tags_field = self.browser.find(By.ID, "text-input", tags_container)
            tags_field.send_keys(','.join(tags) + ',')
            print("Upload: added tags")

            kids_section = self.browser.find(By.NAME, "NOT_MADE_FOR_KIDS")
            self.browser.find(By.ID, "radioLabel", kids_section).click()
            print("Upload: did set NOT_MADE_FOR_KIDS")
            
            self.browser.find(By.ID, 'next-button').click()
            print('Upload: clicked first next')

            self.browser.find(By.ID, 'next-button').click()
            print('Upload: clicked second next')

            public_main_button = self.browser.find(By.NAME, "PUBLIC")
            self.browser.find(By.ID, 'radioLabel', public_main_button).click()
            print('Upload: set to public')

            try:
                video_url_container = self.browser.find(By.XPATH, "//span[@class='video-url-fadeable style-scope ytcp-video-info']", timeout=2.5)
                video_url_element = self.browser.find(By.XPATH, "//a[@class='style-scope ytcp-video-info']", element=video_url_container, timeout=2.5)
                video_id = video_url_element.get_attribute('href').split('/')[-1]
            except:
                video_id = None

            i=0

            while True:
                try:
                    done_button = self.browser.find(By.ID, 'done-button')

                    if done_button.get_attribute('aria-disabled') == 'false':
                        done_button.click()

                        print('Upload: published')

                        time.sleep(3)
                        self.browser.get(YT_URL)

                        return True, video_id
                except Exception as e:
                    print(e)

                    i += 1

                    if i >= 10:
                        raise

                time.sleep(1)
        except Exception as e:
            print(e)
            self.browser.get(YT_URL)

            return False, None
    
    def __video_url(self, video_id: str) -> str:
        return YT_URL + '/watch?v=' + video_id
    
    def __channel_videos_url(self, channel_id: str) -> str:
        return YT_URL + '/channel/' + channel_id + '/videos?view=0&sort=dd&flow=grid'