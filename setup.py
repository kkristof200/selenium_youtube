import setuptools, os

readme_path = 'README.md'

if os.path.exists(readme_path):
    with open(readme_path, 'r') as f:
        long_description = f.read()
else:
    long_description = 'selenium_youtube'

setuptools.setup(
    name='selenium_youtube',
    version='2.0.11',
    author="Kovács Kristóf-Attila & Péntek Zsolt",
    description='selenium_youtube',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/kkristof200/selenium_youtube",
    packages=setuptools.find_packages(),
    install_requires=[
        'beautifulsoup4>=4.10.0',
        'kcu>=0.0.71',
        'kstopit>=0.0.10',
        'kyoutubescraper>=0.0.2',
        'noraise>=0.0.16',
        'selenium>=4.0.0b4',
        'selenium-browser>=0.0.15',
        'selenium-chrome>=0.0.29',
        'selenium-firefox>=2.0.7',
        'selenium-uploader-account>=0.2.1'
    ],
    classifiers=[
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.4'
)