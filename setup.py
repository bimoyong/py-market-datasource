from setuptools import setup

setup(name='py_datasource',
      version='1.0.2',
      description='Interface with data from many data sources',
      url='https://github.com/TsevenSG/py-datasource',
      author='Trung',
      author_email='trung@t7.sg',
      license='MIT',
      packages=[
          'data_providers',
          'tradingview',
          'googlesheet',
      ],
      package_dir={
          'data_providers': 'src/data_providers',
          'googlesheet': 'src/googlesheet',
          'tradingview': 'src/tradingview',
      },
      install_requires=[
          'dependency-injector==4.41.0',
          'google-auth==2.17.3',
          'gspread-dataframe==3.3.1',
          'gspread==5.10.0',
          'pydantic==2.5.1',
          'websocket-client==1.6.3',
      ],
      zip_safe=False)
