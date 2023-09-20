from setuptools import setup

setup(name='py_datasource',
      version='0.1',
      description='Crawl data from many data sources',
      url='https://github.com/TsevenSG/py-datasource',
      author='Trung',
      author_email='trung@t7.sg',
      license='MIT',
      packages=['tradingview'],
      package_dir={'tradingview': 'src/tradingview'},
      install_requires=[
      ],
      zip_safe=False)
