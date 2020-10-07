# --------------------------------------------------------------- Imports ---------------------------------------------------------------- #

# System
from typing import List, Dict, Optional, Tuple, Callable
import time, json

# Pip
from selenium_firefox.firefox import Firefox, By, Keys
from selenium.webdriver.common.action_chains import ActionChains
from ktimeout import timeout
from kcu import strings

from bs4 import BeautifulSoup as bs

# Local
from .visibility import Visibility
from .upload_status import UploadStatus

# ---------------------------------------------------------------------------------------------------------------------------------------- #



# --------------------------------------------------------------- Defines ---------------------------------------------------------------- #

YT_URL          = 'https://www.youtube.com'
YT_STUDIO_URL   = 'https://studio.youtube.com'
YT_UPLOAD_URL   = 'https://www.youtube.com/upload'
YT_LOGIN_URL    = 'https://accounts.google.com/signin/v2/identifier?service=youtube'
YT_STUDIO_VIDEO_URL = 'https://studio.youtube.com/video/{}/edit/basic'
YT_WATCH_VIDEO_URL = 'https://www.youtube.com/watch?v='

MAX_TITLE_CHAR_LEN          = 100
MAX_DESCRIPTION_CHAR_LEN    = 5000
MAX_TAGS_CHAR_LEN           = 500

LOGIN_INFO_COOKIE_NAME = 'LOGIN_INFO'

# ---------------------------------------------------------------------------------------------------------------------------------------- #



# ----------------------------------------------------------- class: Youtube ------------------------------------------------------------- #

class Youtube:

    # ------------------------------------------------------------- Init ------------------------------------------------------------- #

    def __init__(
        self,
        cookies_folder_path: Optional[str] = None,
        extensions_folder_path: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        screen_size: Optional[Tuple[int, int]] = None,
        full_screen: bool = False,
        disable_images: bool = False,
        user_agent: Optional[str] = None,
        login_prompt_callback: Optional[Callable[[str], None]] = None,
        headless: bool = False
    ):
        self.browser = Firefox(
            cookies_folder_path, extensions_folder_path, host=host, port=port, 
            screen_size=screen_size, user_agent=user_agent, 
            full_screen=full_screen, disable_images=disable_images,
            headless=headless
        )
        self.channel_id = None
        self.browser.get(YT_URL)
        self.__dismiss_alerts()

        try:
            self.__internal_channel_id = cookies_folder_path.strip('/').split('/')[-1]
        except:
            self.__internal_channel_id = cookies_folder_path or self.browser.cookies_folder_path

        try:
            logged_in = self.browser.login_via_cookies(YT_URL, LOGIN_INFO_COOKIE_NAME)

            if not logged_in and email and password:
                logged_in = self.login(email=email, password=password, login_prompt_callback=login_prompt_callback)

            if logged_in:
                time.sleep(0.5)
                self.browser.get(YT_URL)
                time.sleep(0.5)
                self.browser.save_cookies()
                time.sleep(0.5)
                self.channel_id = self.get_current_channel_id()
        except Exception as e:
            print(e)
            self.quit()

            raise


    # ------------------------------------------------------ Public properties ------------------------------------------------------- #

    @property
    def is_logged_in(self) -> bool:
        return self.browser.has_cookie(LOGIN_INFO_COOKIE_NAME)


    # -------------------------------------------------------- Public methods -------------------------------------------------------- #

    def login(
        self,
        email: Optional[str],
        password: Optional[str],
        login_prompt_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        org_url = self.browser.driver.current_url
        self.browser.get(YT_URL)
        time.sleep(0.5)

        logged_in = self.is_logged_in

        if not logged_in and email is not None and password is not None:
            logged_in = self.__login_auto(email, password)
        
        if not logged_in:
            print('Could not log you in automatically.')
            logged_in = self.__login_manual(login_prompt_callback=login_prompt_callback)

        if logged_in:
            time.sleep(0.5)
            self.browser.get(YT_URL)
            time.sleep(0.5)

            self.browser.save_cookies()

        time.sleep(0.5)
        self.browser.get(org_url)

        return logged_in

    def watch_video(
        self,
        video_id: str,
        percent_to_watch: float = -1, # 0-100 # -1 means all
        like: bool = False
    ) -> Tuple[bool, bool]: # watched, liked
        watched = False
        liked = False

        try:
            self.browser.get(YT_WATCH_VIDEO_URL+video_id)
            length_s = float(strings.between(self.browser.driver.page_source, 'detailpage\\\\u0026len=', '\\\\'))
            play_button = self.browser.find_by('button', class_='ytp-large-play-button ytp-button', timeout=0.5)

            if play_button and play_button.is_displayed():
                play_button.click()
                time.sleep(1)

            while True:
                ad = self.browser.find_by('div', class_='video-ads ytp-ad-module', timeout=0.5)

                if not ad or not ad.is_displayed():
                    break

                time.sleep(0.1)

            watched = True
            seconds_to_watch = percent_to_watch / 100 * length_s if percent_to_watch >= 0 else length_s

            if seconds_to_watch > 0:
                print('Goinng to watch', seconds_to_watch)
                time.sleep(seconds_to_watch)

            return watched, self.like(video_id) if like and self.is_logged_in else False
        except Exception as e:
            print(e)

            return watched, liked
    
    def like(self, video_id: str) -> bool:
        self.browser.get(YT_WATCH_VIDEO_URL+video_id)

        try:
            buttons_container = self.browser.find_by('div', id_='top-level-buttons', class_='style-scope ytd-menu-renderer', timeout=1.5)

            if buttons_container:
                button_container = self.browser.find_by('ytd-toggle-button-renderer', class_='style-scope ytd-menu-renderer force-icon-button style-text', timeout=0.5, in_element=buttons_container)

                if button_container:
                    button = self.browser.find_by('button', id_='button', timeout=0.5, in_element=button_container)

                    if button:
                        attr = button.get_attribute('aria-pressed')

                        if attr and attr == 'false':
                            button.click()

                        return True

            return False
        except Exception as e:
            print(e)

            return False

    def upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        made_for_kids: bool = False,
        visibility: Visibility = Visibility.PUBLIC,
        thumbnail_image_path: Optional[str] = None,
        _timeout: Optional[int] = 60*3, # 3 min
        extra_sleep_after_upload: Optional[int] = None,
        extra_sleep_before_publish: Optional[int] = None
    ) -> (bool, Optional[str]):

        if _timeout is not None:
            try:
                with timeout.timeout(_timeout):
                    return self.__upload(video_path, title, description, tags, made_for_kids=made_for_kids, visibility=visibility, thumbnail_image_path=thumbnail_image_path, extra_sleep_after_upload=extra_sleep_after_upload, extra_sleep_before_publish=extra_sleep_before_publish)
            except Exception as e:
                print('Upload', e)
                # self.browser.get(YT_URL)

                return False, None
        else:
            return self.__upload(video_path, title, description, tags, made_for_kids=made_for_kids, visibility=visibility, thumbnail_image_path=thumbnail_image_path, extra_sleep_after_upload=extra_sleep_after_upload, extra_sleep_before_publish=extra_sleep_before_publish)

    def get_current_channel_id(self) -> Optional[str]:
        self.browser.get(YT_URL)

        try:
            return json.loads(
                strings.between(
                    self.browser.driver.page_source, 'var ytInitialGuideData = ', '};'
                ) + '}'
            )['responseContext']['serviceTrackingParams'][2]['params'][0]['value']
        except Exception as e:
            print('get_current_channel_id', e)

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
                with timeout.timeout(_timeout):
                    return self.__comment_on_video(video_id, comment, pinned=pinned)
            except Exception as e:
                print('Comment', e)
                # self.browser.get(YT_URL)

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

    def add_endscreen(self, video_id: str, max_wait_seconds_for_processing: float = 0) -> bool:
        self.browser.get(YT_STUDIO_VIDEO_URL.format(video_id))

        try:
            start_time = time.time()

            while True:
                attrs = self.browser.get_attributes(self.browser.find_by('ytcp-text-dropdown-trigger', id_='endscreen-editor-link'))

                if not attrs or 'disabled' in attrs:
                    if time.time() - start_time < max_wait_seconds_for_processing:
                        time.sleep(1)

                        continue

                    return False
                else:
                    break

            self.browser.find_by('ytcp-text-dropdown-trigger', id_='endscreen-editor-link').click()
            time.sleep(0.5)
            self.browser.find_all_by('div', class_='card style-scope ytve-endscreen-template-picker')[0].click()
            time.sleep(0.5)
            self.browser.find_by('ytcp-button', id_='save-button').click()

            time.sleep(2)

            return self.browser.find_by('ytve-endscreen-editor-options-panel', class_='style-scope ytve-editor', timeout=0.5) is None
        except Exception as e:
            print(e)

            return False

    def quit(self):
        try:
            self.browser.driver.quit()
        except:
            pass


    # ------------------------------------------------------- Private methods -------------------------------------------------------- #

    def __upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        made_for_kids: bool = False,
        visibility: Visibility = Visibility.PUBLIC,
        thumbnail_image_path: Optional[str] = None,
        extra_sleep_after_upload: Optional[int] = None,
        extra_sleep_before_publish: Optional[int] = None
    ) -> (bool, Optional[str]):
        self.browser.get(YT_URL)
        time.sleep(1.5)

        try:
            self.browser.get(YT_UPLOAD_URL)
            time.sleep(1.5)
            self.browser.save_cookies()

            self.browser.find(By.XPATH, "//input[@type='file']").send_keys(video_path)
            print('Upload: uploaded video')

            if extra_sleep_after_upload is not None and extra_sleep_after_upload > 0:
                time.sleep(extra_sleep_after_upload)

            title_field = self.browser.find_by('div', id_='textbox')
            time.sleep(0.5)
            title_field.send_keys(Keys.BACK_SPACE)
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

            if thumbnail_image_path is not None:
                try:
                    self.browser.find(By.XPATH, "//input[@id='file-loader']").send_keys(thumbnail_image_path)
                    time.sleep(0.5)
                    print('Upload: added thumbnail')
                except Exception as e:
                    print('Upload: Thumbnail error: ', e)

            self.browser.find(By.XPATH, "/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-details/div/div/ytcp-button/div").click()
            print("Upload: clicked more options")

            tags_container = self.browser.find(By.XPATH, "/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-details/div/ytcp-uploads-advanced/ytcp-form-input-container/div[1]/div[2]/ytcp-free-text-chip-bar/ytcp-chip-bar/div")
            tags_field = self.browser.find(By.ID, 'text-input', tags_container)
            tags_field.send_keys(','.join(tags) + ',')
            print("Upload: added tags")

            kids_selection_name = 'MADE_FOR_KIDS' if made_for_kids else 'NOT_MADE_FOR_KIDS'
            kids_section = self.browser.find(By.NAME, kids_selection_name)
            self.browser.find(By.ID, 'radioLabel', kids_section).click()
            print('Upload: did set', kids_selection_name)
            
            self.browser.find(By.ID, 'next-button').click()
            print('Upload: clicked first next')

            self.browser.find(By.ID, 'next-button').click()
            print('Upload: clicked second next')

            visibility_main_button = self.browser.find(By.NAME, visibility.name)
            self.browser.find(By.ID, 'radioLabel', visibility_main_button).click()
            print('Upload: set to', visibility.name)

            try:
                video_url_container = self.browser.find(By.XPATH, "//span[@class='video-url-fadeable style-scope ytcp-video-info']", timeout=2.5)
                video_url_element = self.browser.find(By.XPATH, "//a[@class='style-scope ytcp-video-info']", element=video_url_container, timeout=2.5)
                video_id = video_url_element.get_attribute('href').split('/')[-1]
            except Exception as e:
                print(e)
                video_id = None

            i=0

            if extra_sleep_before_publish is not None and extra_sleep_before_publish > 0:
                time.sleep(extra_sleep_before_publish)

            while True:
                try:
                    upload_progress_element = self.browser.find_by(
                        'ytcp-video-upload-progress',
                        class_='style-scope ytcp-uploads-dialog',
                        timeout=0.2
                    )

                    upload_status = UploadStatus.get_status(self.browser, upload_progress_element)

                    if upload_status in [UploadStatus.PROCESSING_SD, UploadStatus.PROCESSED_SD_PROCESSING_HD, UploadStatus.PROCESSED_ALL]:
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

                    if i >= 20:
                        done_button = self.browser.find(By.ID, 'done-button')

                        if done_button.get_attribute('aria-disabled') == 'false':
                            done_button.click()

                            print('Upload: published')

                            time.sleep(3)
                            self.browser.get(YT_URL)

                            return True, video_id

                        raise

                time.sleep(1)
        except Exception as e:
            print(e)
                
            self.browser.get(YT_URL)

            return False, None

    # returns (commented_successfully, pinned_comment_successfully)
    def __comment_on_video(self, video_id: str, comment: str, pinned: bool = False) -> (bool, bool):
        self.load_video(video_id)
        time.sleep(1)
        self.browser.scroll(150)
        time.sleep(1)
        self.browser.scroll(100)
        time.sleep(1)
        self.browser.scroll(100)

        try:
            header = self.browser.find_by('div', id_='masthead-container', class_='style-scope ytd-app')
            comment_field = self.browser.find(By.XPATH, "//div[@id='placeholder-area']", timeout=5)

            self.browser.scroll_to_element(comment_field, header_element=header)
            time.sleep(0.5)

            print('comment: clicking comment_field')
            comment_field.click()
            print('comment: sending keys')
            self.browser.find(By.XPATH, "//div[@id='contenteditable-root']", timeout=0.5).send_keys(comment)
            print('comment: clicking post_comment')
            self.browser.find(By.XPATH, "//ytd-button-renderer[@id='submit-button' and @class='style-scope ytd-commentbox style-primary size-default']", timeout=0.5).click()

            if not pinned:
                return True, False

            try:
                dropdown_menu_xpath = "//yt-sort-filter-sub-menu-renderer[@class='style-scope ytd-comments-header-renderer']"
                dropdown_menu = self.browser.find(By.XPATH, dropdown_menu_xpath)
                self.browser.scroll_to_element(dropdown_menu, header_element=header)
                time.sleep(0.5)

                dropdown_trigger_xpath = "//paper-button[@id='label' and @class='dropdown-trigger style-scope yt-dropdown-menu']"

                print('comment: clicking dropdown_trigger (open)')
                self.browser.find(By.XPATH, dropdown_trigger_xpath, element=dropdown_menu, timeout=2.5).click()

                try:
                    dropdown_menu = self.browser.find(By.XPATH, dropdown_menu_xpath)
                    dropdown_elements = [elem for elem in self.browser.find_all(By.XPATH, "//a", element=dropdown_menu, timeout=2.5) if 'yt-dropdown-menu' in elem.get_attribute('class')]

                    last_dropdown_element = dropdown_elements[-1]

                    if last_dropdown_element.get_attribute('aria-selected') == 'false':
                        time.sleep(0.25)
                        print('comment: clicking last_dropdown_element')
                        last_dropdown_element.click()
                    else:
                        print('comment: clicking dropdown_trigger (close) (did not click last_dropdown_element (did not find it))')
                        self.browser.find(By.XPATH, dropdown_trigger_xpath, element=dropdown_menu, timeout=2.5).click()
                except Exception as e:
                    print(e)
                    print('comment: clicking dropdown_trigger (close) (did not click last_dropdown_element (error occured))')
                    self.browser.find(By.XPATH, dropdown_trigger_xpath, element=dropdown_menu, timeout=2.5).click()
            except Exception as e:
                print(e)

            # self.browser.scroll(100)
            time.sleep(2.5)

            for comment_thread in self.browser.find_all(By.XPATH, "//ytd-comment-thread-renderer[@class='style-scope ytd-item-section-renderer']"):
                pinned_element = self.browser.find(By.XPATH, "//yt-icon[@class='style-scope ytd-pinned-comment-badge-renderer']", element=comment_thread, timeout=0.5)
                pinned = pinned_element is not None and pinned_element.is_displayed()

                if pinned:
                    continue

                try:
                    # button_3_dots
                    button_3_dots = self.browser.find(By.XPATH, "//yt-icon-button[@id='button' and @class='dropdown-trigger style-scope ytd-menu-renderer']", element=comment_thread, timeout=2.5)

                    self.browser.scroll_to_element(button_3_dots, header_element=header)
                    time.sleep(0.5)
                    print('comment: clicking button_3_dots')
                    button_3_dots.click()

                    popup_renderer_3_dots = self.browser.find(By.XPATH, "//ytd-menu-popup-renderer[@class='style-scope ytd-popup-container']", timeout=2)

                    # dropdown menu item (first)
                    print('comment: clicking button_3_dots-dropdown_menu_item (to pin it)')
                    self.browser.find(By.XPATH, "//a[@class='yt-simple-endpoint style-scope ytd-menu-navigation-item-renderer']", element=popup_renderer_3_dots, timeout=2.5).click()

                    confirm_button_container = self.browser.find(By.XPATH, "//yt-button-renderer[@id='confirm-button' and @class='style-scope yt-confirm-dialog-renderer style-primary size-default']", timeout=5)

                    # confirm button
                    print('comment: clicking confirm_button')
                    self.browser.find(By.XPATH, "//a[@class='yt-simple-endpoint style-scope yt-button-renderer']", element=confirm_button_container, timeout=2.5).click()
                    time.sleep(2)

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

    def __login_auto(self, email: str, password: str) -> bool:
        self.browser.get(YT_LOGIN_URL)
        time.sleep(0.5)

        try:
            with timeout.timeout(30):
                email_field = self.browser.find_by('input', { 'id': 'identifierId', 'type': 'email' })
                email_field.click()
                self.browser.send_keys_delay_random(email_field, email)
                time.sleep(1)
                self.browser.find_by('div', {'jscontroller': 'VXdfxd', 'role': 'button'}).click()
                time.sleep(1)

                action = ActionChains(self.browser.driver)

                pass_container = self.browser.find_by('div', { 'id': 'password', 'jscontroller': 'pxq3x' })
                pass_field = self.browser.find_by('input', { 'type': 'password' }, in_element=pass_container)
                action.move_to_element(pass_field).perform()
                pass_field.click()
                self.browser.send_keys_delay_random(pass_field, password)
                time.sleep(1)
                self.browser.find_by('div', {'jscontroller': 'VXdfxd', 'role': 'button'}).click()
                time.sleep(1)
        except Exception as e:
            print('__login_auto', e)

        self.browser.get(YT_URL)
        time.sleep(0.5)

        return self.is_logged_in
    
    def __login_manual(self, login_prompt_callback: Optional[Callable[[str], None]] = None) -> bool:
        self.browser.get(YT_LOGIN_URL)
        time.sleep(0.5)

        try:
            if login_prompt_callback is not None:
                login_prompt_callback(self.__internal_channel_id + ' needs manual input to log in.')

            input('Log in then press return')
        except Exception as e:
            print('__login_manual', e)

        self.browser.get(YT_URL)
        time.sleep(0.5)

        return self.is_logged_in
    
    def __dismiss_alerts(self):
        dismiss_button_container = self.browser.find_by('div', id_='dismiss-button', timeout=1.5)
        
        if dismiss_button_container:
            dismiss_button = self.browser.find_by('paper-button', id_='button', timeout=0.5, in_element=dismiss_button_container)

            if dismiss_button:
                dismiss_button.click()
            
            iframe = self.browser.find_by('iframe', class_='style-scope ytd-consent-bump-lightbox', timeout=2.5)

            if iframe:
                self.browser.driver.switch_to.frame(iframe)

            agree_button = self.browser.find_by('div', id_='introAgreeButton', timeout=2.5)

            if agree_button:
                agree_button.click()
            
            if iframe:
                self.browser.driver.switch_to.default_content()
    
    def __video_url(self, video_id: str) -> str:
        return YT_URL + '/watch?v=' + video_id
    
    def __channel_videos_url(self, channel_id: str) -> str:
        return YT_URL + '/channel/' + channel_id + '/videos?view=0&sort=da&flow=grid'


# ---------------------------------------------------------------------------------------------------------------------------------------- #s