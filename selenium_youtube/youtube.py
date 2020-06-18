from typing import List, Dict, Optional
import time, json

from selenium_firefox.firefox import Firefox, By, Keys
from ktimeout import timeout
from kcu import strings

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
        port: Optional[int] = None,
        disable_images: bool = False
    ):
        self.browser = Firefox(cookies_folder_path, extensions_folder_path, host=host, port=port, disable_images=disable_images)

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
        self.browser.get(YT_URL)

        try:
            return json.loads(
                strings.between(
                    self.browser.driver.page_source, 'var ytInitialGuideData = ', '};'
                ) + '}'
            )['responseContext']['serviceTrackingParams'][2]['params'][0]['value']
        except Exception as e:
            print(e)

            return None

    def load_video(self, video_id: str):
        self.browser.get(self.__video_url(video_id))

    def comment_on_video(
        self,
        video_id: str,
        comment: str,
        pinned: bool = False,
        _timeout: Optional[int] = 15
    ) -> (bool, bool):
        if _timeout is not None:
            try:
                return timeout.run(
                    timeout.partial(self.__comment_on_video, video_id, comment, pinned=pinned),
                    _timeout
                )
            except Exception as e:
                print(e)
                self.browser.get(YT_URL)

                return False, False
        else:
            return self.__comment_on_video(video_id, comment, pinned=pinned)

    def get_channel_video_ids(
        self,
        channel_id: Optional[str] = None,
        ignored_titles: Optional[List[str]] = None
    ) -> List[str]:
        video_ids = []
        ignored_titles = ignored_titles or []

        channel_id = channel_id or self.channel_id

        try:
            self.browser.get(self.__channel_videos_url(channel_id))
            last_page_source = self.browser.driver.page_source

            while True:
                self.browser.scroll(1500)

                i=0
                max_i = 100
                sleep_time = 0.1
                should_break = True

                while i < max_i:
                    i += 1
                    time.sleep(sleep_time)

                    if len(last_page_source) != len(self.browser.driver.page_source):
                        last_page_source = self.browser.driver.page_source
                        should_break = False

                        break

                if should_break:
                    break

            soup = bs(self.browser.driver.page_source, 'lxml')
            elems = soup.find_all('a', {'id':'video-title', 'class':'yt-simple-endpoint style-scope ytd-grid-video-renderer'})

            for elem in elems:
                if 'title' in elem.attrs:
                    should_continue = False
                    title = elem['title'].strip().lower()

                    for ignored_title in ignored_titles:
                        if ignored_title.strip().lower() == title:
                            should_continue = True

                            break

                    if should_continue:
                        continue

                if 'href' in elem.attrs and '/watch?v=' in elem['href']:
                    vid_id = strings.between(elem['href'], '?v=', '&')

                    if vid_id is not None and vid_id not in video_ids:
                        video_ids.append(vid_id)
        except Exception as e:
            print(e)

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
            except Exception as e:
                print(e)
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

    # returns (commented_successfully, pinned_comment_successfully)
    def __comment_on_video(self, video_id: str, comment: str, pinned: bool = False) -> (bool, bool):
        self.load_video(video_id)

        try:
            comments_threads_xpath = "//ytd-comment-thread-renderer[@class='style-scope ytd-item-section-renderer']"
            self.browser.scroll(350)

            self.browser.find(By.XPATH, "//div[@id='placeholder-area']", timeout=5).click()
            self.browser.find(By.XPATH, "//div[@id='contenteditable-root']", timeout=0.5).send_keys(comment)
            self.browser.find(By.XPATH, "//ytd-button-renderer[@id='submit-button' and @class='style-scope ytd-commentbox style-primary size-default']", timeout=0.5).click()

            if not pinned:
                return True, False

            try:
                dropdown_menu_xpath = "//yt-sort-filter-sub-menu-renderer[@class='style-scope ytd-comments-header-renderer']"
                dropdown_menu = self.browser.find(By.XPATH, dropdown_menu_xpath)

                self.browser.find(By.XPATH, "//paper-button[@id='label' and @class='dropdown-trigger style-scope yt-dropdown-menu']", element=dropdown_menu, timeout=2.5).click()

                try:
                    dropdown_menu = self.browser.find(By.XPATH, dropdown_menu_xpath)
                    dropdown_elements = [elem for elem in self.browser.find_all(By.XPATH, "//a", element=dropdown_menu, timeout=2.5) if 'yt-dropdown-menu' in elem.get_attribute('class')]

                    last_dropdown_element = dropdown_elements[-1]

                    if last_dropdown_element.get_attribute('aria-selected') == 'false':
                        time.sleep(0.25)
                        last_dropdown_element.click()
                    else:
                        self.browser.find(By.XPATH, "//paper-button[@id='label' and @class='dropdown-trigger style-scope yt-dropdown-menu']", element=dropdown_menu, timeout=2.5).click()
                except Exception as e:
                    print(e)
                    self.browser.find(By.XPATH, "//paper-button[@id='label' and @class='dropdown-trigger style-scope yt-dropdown-menu']", element=dropdown_menu, timeout=2.5).click()
            except Exception as e:
                print(e)

            # self.browser.scroll(100)
            time.sleep(2.5)

            for comment_thread in self.browser.find_all(By.XPATH, comments_threads_xpath):
                pinned_element = self.browser.find(By.XPATH, "//yt-icon[@class='style-scope ytd-pinned-comment-badge-renderer']", element=comment_thread, timeout=0.5)
                pinned = pinned_element is not None and pinned_element.is_displayed()

                if pinned:
                    continue

                try:
                    from selenium.webdriver.common.action_chains import ActionChains

                    # button_3_dots
                    button_3_dots = self.browser.find(By.XPATH, "//yt-icon-button[@id='button' and @class='dropdown-trigger style-scope ytd-menu-renderer']", element=comment_thread, timeout=2.5)
                    # time.sleep(2.5)
                    # ActionChains(self.browser.driver).move_to_element(button_3_dots).perform()
                    # time.sleep(2.5)
                    self.browser.scroll_to_element(button_3_dots)
                    time.sleep(0.5)
                    self.browser.scroll(-150)
                    time.sleep(0.5)
                    button_3_dots.click()

                    popup_renderer_3_dots = self.browser.find(By.XPATH, "//ytd-menu-popup-renderer[@class='style-scope ytd-popup-container']", timeout=2)

                    # dropdown menu item (first)
                    self.browser.find(By.XPATH, "//a[@class='yt-simple-endpoint style-scope ytd-menu-navigation-item-renderer']", element=popup_renderer_3_dots, timeout=2.5).click()

                    confirm_button_container = self.browser.find(By.XPATH, "//yt-button-renderer[@id='confirm-button' and @class='style-scope yt-confirm-dialog-renderer style-primary size-default']", timeout=5)

                    # confirm button
                    self.browser.find(By.XPATH, "//a[@class='yt-simple-endpoint style-scope yt-button-renderer']", element=confirm_button_container, timeout=2.5).click()

                    return True, True
                except Exception as e:
                    print(e)

                    return True, False

            # could not find new comment
            print('no_new_comments')
            return True, False
        except Exception as e:
            print(e)

            return False, False

    def __video_url(self, video_id: str) -> str:
        return YT_URL + '/watch?v=' + video_id
    
    def __channel_videos_url(self, channel_id: str) -> str:
        return YT_URL + '/channel/' + channel_id + '/videos?view=0&sort=da&flow=grid'