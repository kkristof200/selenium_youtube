# selenium_youtube

![python_version](https://img.shields.io/static/v1?label=Python&message=3.5%20|%203.6%20|%203.7&color=blue) [![PyPI download month](https://img.shields.io/pypi/dm/selenium_youtube?logo=pypi&logoColor=white)](https://pypi.python.org/pypi/selenium_youtube/) [![PyPI version](https://img.shields.io/pypi/v/selenium_youtube?logo=pypi&logoColor=white)](https://pypi.python.org/pypi/selenium_youtube/)

## Install

````shell
pip install --upgrade selenium-youtube
# or
pip3 install --upgrade selenium-youtube
````

## Usage

````python
from selenium_youtube.youtube import Youtube

youtube = Youtube(
    'path_to_cookies_folder',
    'path_to_extensions_folder'
)

result = youtube.upload('path_to_video', 'title', 'description', ['tag1', 'tag2'])
````

## Dependencies

[beautifulsoup4](https://pypi.org/project/beautifulsoup4), [kcu](https://pypi.org/project/kcu), [kstopit](https://pypi.org/project/kstopit), [kyoutubescraper](https://pypi.org/project/kyoutubescraper), [noraise](https://pypi.org/project/noraise), [selenium](https://pypi.org/project/selenium), [selenium-firefox](https://pypi.org/project/selenium-firefox), [selenium-uploader-account](https://pypi.org/project/selenium-uploader-account)

## Credits

[Péntek Zsolt](https://github.com/Zselter07)