# selenium_youtube



## Description

selenium implementation of youtube, which can upload/watch/like/comment/pin comment on videos

## Install

~~~~bash
pip install selenium_youtube
# or
pip3 install selenium_youtube
~~~~

## Usage

~~~~python
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
~~~~

## Dependencies

[beautifulsoup4](https://pypi.org/project/beautifulsoup4), [kcu](https://pypi.org/project/kcu), [kstopit](https://pypi.org/project/kstopit), [kyoutubescraper](https://pypi.org/project/kyoutubescraper), [noraise](https://pypi.org/project/noraise), [selenium](https://pypi.org/project/selenium), [selenium-browser](https://pypi.org/project/selenium-browser), [selenium-chrome](https://pypi.org/project/selenium-chrome), [selenium-firefox](https://pypi.org/project/selenium-firefox), [selenium-uploader-account](https://pypi.org/project/selenium-uploader-account)



## Credits

[Péntek Zsolt](https://github.com/Zselter07)