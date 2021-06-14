from selenium_youtube import Youtube

# pip install selenium_firefox
from selenium_firefox import Firefox
firefox = Firefox()

# pip install selenium_chrome
from selenium_chrome import Chrome
chrome = Chrome()

youtube = Youtube(
    browser=chrome # or firefox
)

upload_result = youtube.upload('path_to_video', 'title', 'description', ['tag1', 'tag2'])