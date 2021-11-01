# ------------------------------------------------------------ Imports ----------------------------------------------------------- #

# System
from typing import List, Optional, Tuple, Callable, Union
import time
from sys import platform

# Pip
from selenium_uploader_account import SeleniumUploaderAccount
from selenium_browser import Browser
from noraise import noraise
from kcu import strings
from kstopit import signal_timeoutable
from kyoutubescraper import YoutubeScraper, ChannelAboutData

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from bs4 import BeautifulSoup as bs

# Local
from .enums.visibility import Visibility
from .enums.upload_status import UploadStatus
from .enums.analytics_period import AnalyticsPeriod
from .enums.analytics_tab import AnalyticsTab

# -------------------------------------------------------------------------------------------------------------------------------- #



# ------------------------------------------------------------ Defines ----------------------------------------------------------- #

YT_URL                  = 'https://www.youtube.com'
YT_STUDIO_URL           = 'https://studio.youtube.com'
YT_UPLOAD_URL           = 'https://www.youtube.com/upload'
YT_LOGIN_URL            = 'https://accounts.google.com/signin/v2/identifier?service=youtube'
YT_STUDIO_VIDEO_URL     = 'https://studio.youtube.com/video/{}/edit/basic'
YT_WATCH_VIDEO_URL      = 'https://www.youtube.com/watch?v={}'
YT_PROFILE_URL          = 'https://www.youtube.com/channel/{}'
YT_PROFILE_CONTENT_URL  = 'https://studio.youtube.com/channel/{}/videos'
YT_SEARCH_URL           = 'https://www.youtube.com/results?search_query={}'

MAX_TITLE_CHAR_LEN          = 100
MAX_DESCRIPTION_CHAR_LEN    = 5000
MAX_TAGS_CHAR_LEN           = 400
MAX_TAG_CHAR_LEN            = 30

LOGIN_INFO_COOKIE_NAME = 'LOGIN_INFO'

# -------------------------------------------------------------------------------------------------------------------------------- #



# -------------------------------------------------------- class: Youtube -------------------------------------------------------- #

class Youtube(SeleniumUploaderAccount):

    # --------------------------------------------------------- Init --------------------------------------------------------- #

    def __init__(
        self,

        # browser
        browser: Browser,

        # login
        prompt_user_input_login: bool = True,
        login_prompt_callback: Optional[Callable[[str], None]] = None,
        login_prompt_timeout_seconds: int = 60*5
    ):
        super().__init__(
            # browser
            browser=browser,

            # login
            prompt_user_input_login=prompt_user_input_login,
            login_prompt_callback=login_prompt_callback,
            login_prompt_timeout_seconds=login_prompt_timeout_seconds,
        )

        if not self.did_log_in_at_init:
            self.__dismiss_alerts()


    # ------------------------------------------------------- Overrides ------------------------------------------------------ #

    def _upload_function(self) -> Callable:
        return self.upload

    def _home_url(self) -> str:
        return YT_URL

    def _get_current_user_id(self) -> Optional[str]:
        return self.get_current_channel_id()

    def _profile_url_format(self) -> Optional[str]:
        return YT_PROFILE_URL

    def _login_via_cookies_needed_cookie_names(self) -> Union[str, List[str]]:
        return LOGIN_INFO_COOKIE_NAME


    # ---------------------------------------------------- Public methods ---------------------------------------------------- #

    def get_sub_and_video_count(self, channel_id: str) -> Optional[Tuple[int, int]]:
        return YoutubeScraper(user_agent=self.user_agent, proxy=self.proxy.string).get_sub_and_video_count(channel_id=channel_id)

    def get_channel_about_data(
        self,
        user_name: Optional[str] = None,
        channel_id: Optional[str] = None,
        channel_url_name: Optional[str] = None
    ) -> Optional[ChannelAboutData]:
        return YoutubeScraper(user_agent=self.user_agent, proxy=self.proxy.string).get_channel_about_data(
            user_name=user_name,
            channel_id=channel_id,
            channel_url_name=channel_url_name
        )

    def watch_video(
        self,
        video_id: str,
        percent_to_watch: float = -1, # 0-100 # -1 means all
        like: bool = False
    ) -> Tuple[bool, bool]: # watched, liked
        watched = False
        liked = False

        try:
            self.get(YT_WATCH_VIDEO_URL.format(video_id))
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
                self.print('Goinng to watch', seconds_to_watch)
                time.sleep(seconds_to_watch)

            return watched, self.like(video_id) if like and self.is_logged_in else False
        except Exception as e:
            self.print(e)

            return watched, liked

    def like(self, video_id: str) -> bool:
        if not self.is_logged_in:
            print('Error - \'upload\': Isn\'t logged in')

            return False

        self.get(YT_WATCH_VIDEO_URL.format(video_id))

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
            self.print(e)

            return False

    def upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        made_for_kids: bool = False,
        visibility: Visibility = Visibility.PUBLIC,
        thumbnail_image_path: Optional[str] = None,
        timeout: Optional[int] = 60*3, # 3 min
        extra_sleep_after_upload: Optional[int] = None,
        extra_sleep_before_publish: Optional[int] = None
    ) -> (bool, Optional[str]):
        if not self.is_logged_in:
            print('Error - \'upload\': Isn\'t logged in')

            return False, None

        res = self.__upload(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            made_for_kids=made_for_kids,
            visibility=visibility,
            thumbnail_image_path=thumbnail_image_path,
            extra_sleep_after_upload=extra_sleep_after_upload,
            extra_sleep_before_publish=extra_sleep_before_publish,
            timeout=timeout
        )

        if isinstance(res, Exception):
            self.print(res)

            return False, None

        return res

    def get_current_channel_id(self, _click_avatar: bool = False, _get_home_url: bool = False) -> Optional[str]:
        if not self.is_logged_in:
            print('Error - \'upload\': Isn\'t logged in')

            return None

        if _get_home_url:
            self.get(YT_URL)

        try:
            if _click_avatar:
                avatar_button = self.browser.find_by('button', id_='avatar-btn', timeout=0.5)

                if avatar_button:
                    avatar_button.click()

            href_containers = self.browser.find_all_by('a', class_='yt-simple-endpoint style-scope ytd-compact-link-renderer', timeout=0.5)

            if href_containers:
                for href_container in href_containers:
                    href = href_container.get_attribute('href')

                    if href and 'channel/' in href:
                        return strings.between(href, 'channel/', '?')
        except Exception as e:
            self.print(e)

        if not _click_avatar:
            return self.get_current_channel_id(_click_avatar=True, _get_home_url=_get_home_url)
        elif not _get_home_url:
            return self.get_current_channel_id(_click_avatar=False, _get_home_url=True)

        return None

    def load_video(self, video_id: str):
        self.get(self.__video_url(video_id))

    def comment_on_video(
        self,
        video_id: str,
        comment: str,
        pinned: bool = False,
        timeout: Optional[int] = 15
    ) -> (bool, bool):
        if not self.is_logged_in:
            print('Error - \'upload\': Isn\'t logged in')

            return False, False

        res = self.__comment_on_video(
            video_id=video_id,
            comment=comment,
            pinned=pinned,
            timeout=timeout
        )

        if isinstance(res, Exception):
            self.print(res)

            return False, False

        return res

    def get_channel_video_ids(
        self,
        channel_id: Optional[str] = None,
        ignored_titles: Optional[List[str]] = None
    ) -> List[str]:
        video_ids = []
        ignored_titles = ignored_titles or []
        channel_id = channel_id or self.current_user_id

        try:
            self.get(self.__channel_videos_url(channel_id))
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
            self.print(e)

        return video_ids

    def check_analytics(
        self,
        tab: AnalyticsTab = AnalyticsTab.OVERVIEW,
        period: AnalyticsPeriod = AnalyticsPeriod.LAST_28_DAYS
    ) -> bool:
        return self.__open_yt_studio(f'analytics/tab-{tab.value}/period-{period.value}')

    def check_channel_branding(self) -> bool:
        return self.__open_yt_studio('editing/images')

    def check_channel_basic_info(self) -> bool:
        return self.__open_yt_studio('editing/details')

    @noraise(default_return_value=(False, 0))
    def get_violations(self) -> Tuple[bool, int]: # has_warning, strikes
        self.get(YT_STUDIO_URL)
        violations_container = self.browser.find_by('div', class_='style-scope ytcd-strikes-item')

        if not violations_container:
            return False, 0

        violations_label = self.browser.find_by('div', class_='label style-scope ytcp-badge', in_element=violations_container)

        if not violations_label:
            return False, 0

        violation_text = violations_label.text.strip().lower()
        violation_text_number = 0

        try:
            violation_text_number = int(violation_text)
        except:
            pass

        return True, violation_text_number

    @noraise(default_return_value=False)
    def add_endscreen(self, video_id: str, max_wait_seconds_for_processing: float = 0) -> bool:
        self.get(YT_STUDIO_VIDEO_URL.format(video_id))
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

    @noraise(default_return_value=False)
    def remove_welcome_popup(
        self,
        offset: Tuple[int, int] = (20, 20)
    ) -> bool:
        timeout = 5

        self.get(YT_STUDIO_URL, force=True)
        self.__dismiss_welcome_popup(offset=offset, timeout=timeout)

        self.get(YT_UPLOAD_URL, force=True)

        return self.__dismiss_welcome_popup(offset=offset, timeout=timeout)

    @noraise(default_return_value=None)
    def setup_account_branding(
        self,
        profile_pic: Optional[str] = None,
        banner_image: Optional[str] = None,
        watermark: Optional[str] = None,
    ) -> None:
        self.check_channel_branding()

        if profile_pic:
            self._input_file(profile_pic, class_='ytcp-profile-image-upload')
            self.browser.move_to_element(element=self.browser.find_by('ytcp-button', id_='done-button', class_='ytcp-profile-image-editor'), click=True)

        if banner_image:
            self._input_file(banner_image, class_='ytcp-banner-upload')
            self.browser.move_to_element(element=self.browser.find_by('ytcp-button', id_='done-button', class_='ytcp-profile-image-editor'), click=True)

        if watermark:
            self._input_file(watermark, class_='ytcp-video-watermark-upload')
            self.browser.move_to_element(element=self.browser.find_by('ytcp-button', id_='done-button', class_='ytcp-profile-image-editor'), click=True)

        self.browser.move_to_element(element=self.browser.find_by('ytcp-button', id_='publish-button'), click=True)

    @noraise(default_return_value=None)
    def setup_account_details(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        self.check_channel_basic_info()

        if name:
            self.browser.find_by('ytcp-icon-button', id_='edit-button', class_='ytcp-channel-editing-channel-name', timeout=5).click()
            self.browser.set_textfield_text_remove_old(
                element=self.browser.find_by('input', id_='brand-name-input', timeout=5),
                text=name
            )

        if description:
            self.browser.set_textfield_text_remove_old(
                element=self.browser.find_by('div', id_='textbox', timeout=5) or self.browser.find_by(id_='textbox', timeout=5),
                text=description
            )

        self.browser.move_to_element(element=self.browser.find_by('ytcp-button', id_='publish-button'), click=True)


    # ---------------------------------------------------- Private methods --------------------------------------------------- #

    @noraise(default_return_value=False)
    def __open_yt_studio(
        self,
        sub_url: str
    ) -> bool:
        if not self.current_user_id:
            self.print('No channel ID found')

            return False

        _YT_STUDIO_URL = YT_STUDIO_URL.rstrip('/')
        sub_url = sub_url.lstrip('/')

        self.get(f'{_YT_STUDIO_URL}/channel/{self.current_user_id}/{sub_url}')

        return True

    def _input_file(
        self,
        file_path: str,
        class_: Optional[str] = None,
    ) -> None:
        # can throw
        self.browser.find_by('input', class_=class_, type='file').send_keys(file_path)

        self.browser.move_to_element(element=self.browser.find_by('ytcp-button', id_='publish-button'), click=True)

    @signal_timeoutable(name='Upload')
    def __upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        made_for_kids: bool = False,
        visibility: Visibility = Visibility.PUBLIC,
        thumbnail_image_path: Optional[str] = None,
        extra_sleep_after_upload: Optional[int] = None,
        extra_sleep_before_publish: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> (bool, Optional[str]):
        self.get(YT_URL)
        time.sleep(1.5)

        try:
            self.get(YT_UPLOAD_URL)
            time.sleep(1.5)
            self.save_cookies()

            self._input_file(video_path)
            self.print('Upload: uploaded video')

            if extra_sleep_after_upload is not None and extra_sleep_after_upload > 0:
                time.sleep(extra_sleep_after_upload)

            self.__dismiss_welcome_popup()

            self.browser.set_textfield_text_remove_old(
                element=self.browser.find_by('div', id_='textbox', timeout=5) or self.browser.find_by(id_='textbox', timeout=5),
                text=title[:MAX_TITLE_CHAR_LEN]
            )
            self.print('Upload: added title')

            description_container = self.browser.find_by('ytcp-mention-textbox', class_='description-textarea style-scope ytcp-uploads-basics') or self.browser.find_by('div', id='description-container')
            self.browser.set_textfield_text_remove_old(
                element=self.browser.find_by(id='textbox', in_element=description_container),
                text=description[:MAX_DESCRIPTION_CHAR_LEN]
            )
            self.print('Upload: added description')

            if thumbnail_image_path is not None:
                try:
                    self.browser.find(By.XPATH, "//input[@id='file-loader']").send_keys(thumbnail_image_path)
                    time.sleep(0.5)
                    self.print('Upload: added thumbnail')
                except Exception as e:
                    self.print('Upload: Thumbnail error: ', e)

            (self.browser.find_by('ytcp-button', class_='advanced-button style-scope ytcp-uploads-details') or self.browser.find_by('ytcp-button', {"id":"toggle-button", "class":"style-scope ytcp-video-metadata-editor", "role":"button"})).click()

            self.print("Upload: clicked more options")

            if tags:
                tags_container = self.browser.find_by('ytcp-form-input-container', id='tags-container') or self.browser.find(By.XPATH, "/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-details/div/ytcp-uploads-advanced/ytcp-form-input-container/div[1]/div[2]/ytcp-free-text-chip-bar/ytcp-chip-bar/div")
                tags_field = self.browser.find(By.ID, 'text-input', tags_container)
                tags_field.send_keys(','.join([t for t in tags if len(t) <= MAX_TAG_CHAR_LEN])[:MAX_TAGS_CHAR_LEN-1] + ',')
                self.print("Upload: added tags")

            kids_selection_name = 'VIDEO_MADE_FOR_KIDS_MFK' if made_for_kids else 'VIDEO_MADE_FOR_KIDS_NOT_MFK'
            kids_section = self.browser.find(By.NAME, kids_selection_name)
            self.browser.find(By.ID, 'radioLabel', kids_section).click()
            self.print('Upload: did set', kids_selection_name)

            self.browser.find(By.ID, 'next-button').click()
            self.print('Upload: clicked first next')

            self.browser.find(By.ID, 'next-button').click()
            self.print('Upload: clicked second next')

            visibility_tab = self.browser.find_by('button', {'test-id':'REVIEW', 'state':'active'})

            if not visibility_tab:
                third_next = self.browser.find_by('ytcp-button', id='next-button')
                third_next.click()
                self.print('Upload: clicked third next')

            visibility_main_button = self.browser.find(By.NAME, visibility.name)
            self.browser.find(By.ID, 'radioLabel', visibility_main_button).click()
            self.print('Upload: set to', visibility.name)

            time.sleep(1)
            got_it_popup = self.browser.find(By.ID, 'got-it-button')

            if got_it_popup:
                print('FOUND GOT IT POPUP')
                got_it_popup.click()
                print('CLICKED GOT IT POPUP')

            try:
                video_url_container = self.browser.find(By.XPATH, "//span[@class='video-url-fadeable style-scope ytcp-video-info']", timeout=2.5)
                video_url_element = self.browser.find(By.XPATH, "//a[@class='style-scope ytcp-video-info']", element=video_url_container, timeout=2.5)
                video_id = video_url_element.get_attribute('href').split('/')[-1]
            except Exception as e:
                self.print(e)
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

                            self.print('Upload: published')

                            time.sleep(7)
                            self.get(YT_URL)

                            return True, video_id
                except Exception as e:
                    self.print(e)
                    i += 1

                    if i >= 20:
                        done_button = self.browser.find(By.ID, 'done-button')

                        if done_button.get_attribute('aria-disabled') == 'false':
                            done_button.click()

                            self.print('Upload: published')

                            time.sleep(3)
                            self.get(YT_URL)

                            return True, video_id

                        raise

                time.sleep(1)
        except Exception as e:
            self.print(e)

            self.get(YT_URL)

            return False, None

    # returns (commented_successfully, pinned_comment_successfully)
    @signal_timeoutable(name='Comment')
    def __comment_on_video(
        self,
        video_id: str,
        comment: str,
        pinned: bool = False,
        timeout: Optional[int] = None
    ) -> (bool, bool):
        self.load_video(video_id)
        time.sleep(1)
        self.browser.scroll(150)
        time.sleep(1)
        self.browser.scroll(100)
        time.sleep(1)
        self.browser.scroll(100)

        try:
            # time.sleep(10000)
            header = self.browser.find_by('div', id_='masthead-container', class_='style-scope ytd-app')

            self.print('comment: looking for \'comment_placeholder_area\'')
            comment_placeholder_area = self.browser.find_by('div', id_='placeholder-area', timeout=5)

            self.print('comment: scrollinng to \'comment_placeholder_area\'')
            self.browser.scroll_to_element(comment_placeholder_area, header_element=header)
            time.sleep(0.5)

            self.print('comment: getting focus')
            try:
                self.browser.find_by('div', id_='simple-box', class_='style-scope ytd-comments-header-renderer',timeout=0.5).click()
                self.browser.find_by('ytd-comment-simplebox-renderer', class_='style-scope ytd-comments-header-renderer',timeout=0.5).click()
                # comment_placeholder_area.click()
                self.browser.find_by('div', id_='placeholder-area', timeout=0.5).click()
            except Exception as e:
                self.print(e)

            self.print('comment: sending keys')
            # self.browser.find_by('div', id_='contenteditable-root', timeout=0.5).click()
            self.browser.find_by('div', id_='contenteditable-root', timeout=0.5).send_keys(comment)

            self.print('comment: clicking post_comment')
            self.browser.find_by('ytd-button-renderer', id_='submit-button', class_='style-scope ytd-commentbox style-primary size-default',timeout=0.5).click()

            # self.browser.find(By.XPATH, "//ytd-button-renderer[@id='submit-button' and @class='style-scope ytd-commentbox style-primary size-default']", timeout=0.5).click()

            if not pinned:
                return True, False

            try:
                try:
                    dropdown_menu = self.browser.find_by('yt-sort-filter-sub-menu-renderer', class_='style-scope ytd-comments-header-renderer')
                    self.browser.scroll_to_element(dropdown_menu, header_element=header)
                    time.sleep(0.5)

                    self.print('comment: clicking dropdown_trigger (open)')
                    self.browser.find_by('paper-button', id_='label', class_='dropdown-trigger style-scope yt-dropdown-menu', in_element=dropdown_menu, timeout=2.5).click()

                    try:
                        dropdown_menu = self.browser.find_by('paper-button', id_='label', class_='dropdown-trigger style-scope yt-dropdown-menu', in_element=dropdown_menu, timeout=2.5)
                        dropdown_elements = [elem for elem in self.browser.find_all_by('a', in_element=dropdown_menu, timeout=2.5) if 'yt-dropdown-menu' in elem.get_attribute('class')]

                        last_dropdown_element = dropdown_elements[-1]

                        if last_dropdown_element.get_attribute('aria-selected') == 'false':
                            time.sleep(0.25)
                            self.print('comment: clicking last_dropdown_element')
                            last_dropdown_element.click()
                        else:
                            self.print('comment: clicking dropdown_trigger (close) (did not click last_dropdown_element (did not find it))')
                            self.browser.find_by('paper-button', id_='label', class_='dropdown-trigger style-scope yt-dropdown-menu', in_element=dropdown_menu, timeout=2.5).click()
                    except Exception as e:
                        self.print(e)
                        self.browser.find_by('paper-button', id_='label', class_='dropdown-trigger style-scope yt-dropdown-menu', in_element=dropdown_menu, timeout=2.5).click()
                except Exception as e:
                    self.print(e)

                # self.browser.scroll(100)
                time.sleep(2.5)

                for comment_thread in self.browser.find_all_by('ytd-comment-thread-renderer', class_='style-scope ytd-item-section-renderer'):
                    pinned_element = self.browser.find_by('yt-icon', class_='style-scope ytd-pinned-comment-badge-renderer', in_element=comment_thread, timeout=0.5)
                    pinned = pinned_element is not None and pinned_element.is_displayed()

                    if pinned:
                        continue

                    try:
                        # button_3_dots
                        button_3_dots = self.browser.find_by('yt-icon-button', id_='button', class_='dropdown-trigger style-scope ytd-menu-renderer', in_element=comment_thread, timeout=2.5)

                        self.browser.scroll_to_element(button_3_dots, header_element=header)
                        time.sleep(0.5)
                        self.print('comment: clicking button_3_dots')
                        button_3_dots.click()

                        popup_renderer_3_dots = self.browser.find_by('ytd-menu-popup-renderer', class_='ytd-menu-popup-renderer', timeout=2)
                        time.sleep(1.5)

                        try:
                            self.browser.driver.execute_script("arguments[0].scrollIntoView();", self.browser.find_by('a',class_='yt-simple-endpoint style-scope ytd-menu-navigation-item-renderer', in_element=popup_renderer_3_dots, timeout=2.5))

                            self.browser.find_by('a',class_='yt-simple-endpoint style-scope ytd-menu-navigation-item-renderer', in_element=popup_renderer_3_dots, timeout=2.5).click()
                        except:
                            try:
                                self.browser.find_by('ytd-menu-navigation-item-renderer',class_='style-scope ytd-menu-popup-renderer', in_element=popup_renderer_3_dots, timeout=2.5).click()
                            except Exception as e:
                                try:
                                    self.browser.find_by('paper-item',class_='style-scope ytd-menu-navigation-item-renderer', in_element=popup_renderer_3_dots, timeout=2.5).click()
                                except Exception as e:
                                    pass

                        # confirm button
                        confirm_button = self.browser.find_by('yt-button-renderer', id_='confirm-button', timeout=5)
                        self.print(f'comment: clicking confirm_button ({confirm_button})')
                        confirm_button.click()
                        time.sleep(2)

                        return True, True
                    except Exception as e:
                        self.print(e)

                        return True, False
            except Exception as e:
                self.print(e)

                return True, False

            # could not find new comment
            self.print('no_new_comments')
            return True, False
        except Exception as e:
            self.print('comment error:', e)

            return False, False

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

    @noraise(default_return_value=False)
    def __dismiss_welcome_popup(
        self,
        offset: Tuple[int, int] = (20, 20),
        timeout: Optional[int] = 2
    ) -> bool:
        return self.browser.move_to_element(
            element=self.browser.find_by('iron-overlay-backdrop', class_='opened', timeout=timeout),
            offset=offset,
            click=True
        )

    def __video_url(self, video_id: str) -> str:
        return YT_URL + '/watch?v=' + video_id

    def __channel_videos_url(self, channel_id: str) -> str:
        return YT_URL + '/channel/' + channel_id + '/videos?view=0&sort=da&flow=grid'


# -------------------------------------------------------------------------------------------------------------------------------- #