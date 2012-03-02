from setuptools import setup, find_packages

setup(
      name="DjangoPythonJobBoard",
      version="0.1",
      packages=find_packages(),
      install_requires=[
                        'BeautifulSoup>=3.2.1',
                        'Django>=1.3',
                        'requests>=0.10.6'
                        ],
 
      include_package_data = True,
      )





