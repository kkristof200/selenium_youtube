# selenium_youtube

![PyPI - package version](https://img.shields.io/pypi/v/selenium_youtube?logo=pypi&style=flat-square)
![PyPI - license](https://img.shields.io/pypi/l/selenium_youtube?label=package%20license&style=flat-square)
![PyPI - python version](https://img.shields.io/pypi/pyversions/selenium_youtube?logo=pypi&style=flat-square)
![PyPI - downloads](https://img.shields.io/pypi/dm/selenium_youtube?logo=pypi&style=flat-square)

![GitHub - last commit](https://img.shields.io/github/last-commit/kkristof200/selenium_youtube?style=flat-square)
![GitHub - commit activity](https://img.shields.io/github/commit-activity/m/kkristof200/selenium_youtube?style=flat-square)

![GitHub - code size in bytes](https://img.shields.io/github/languages/code-size/kkristof200/selenium_youtube?style=flat-square)
![GitHub - repo size](https://img.shields.io/github/repo-size/kkristof200/selenium_youtube?style=flat-square)
![GitHub - lines of code](https://img.shields.io/tokei/lines/github/kkristof200/selenium_youtube?style=flat-square)

![GitHub - license](https://img.shields.io/github/license/kkristof200/selenium_youtube?label=repo%20license&style=flat-square)

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