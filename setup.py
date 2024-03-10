from setuptools import setup, find_packages

setup(
    name="web3tg",
    version='0.0.1',
    author="timer",
    author_email="timerkhan2002@gmail.com",
    description='Private bot for interacting with socials and profiles from web3db',
    packages=find_packages(),
    url='https://github.com/timertimertimer/web3tg',
    install_requires=[
        'g4f', 'capmonstercloudclient', 'web3db',
        'aiogram', 'aiofiles', 'aioimaplib', 'tweepy-self', 'better_proxy', 'aiohttp_proxy',
        'python-dotenv', 'loguru'
    ],
    project_urls={
        "GitHub": "https://github.com/timertimertimer/web3tg",
        "Source": "https://github.com/timertimertimer/web3tg"
    },
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ]
)
