import sys
from setuptools import setup

if sys.version_info.major < 3:
    sys.exit('Sorry, this library only supports Python 3')

setup(
    name='easyzebra',
    packages=['easyzebra'],
    include_package_data=True,
    version='0.0.10',
    description='Zebra ZPL II Driver',
    author='Stephen Brown (Little Fish Solutions LTD)',
    author_email='opensource@littlefish.solutions',
    url='https://github.com/stevelittlefish/easyzebra',
    download_url='https://github.com/stevelittlefish/easyzebra/archive/v0.0.10.tar.gz',
    keywords=['easy', 'zebra', 'zpl'],
    license='Apache',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries'
    ],
    install_requires=[
        'requests>=2.10.0',
        'Unidecode>=0.4.19'
    ],
)

