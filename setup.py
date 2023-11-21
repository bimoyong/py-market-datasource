from setuptools import setup

setup(name='py_datasource',
      version='0.1',
      description='Interface with data from many data sources',
      url='https://github.com/TsevenSG/py-datasource',
      author='Trung',
      author_email='trung@t7.sg',
      license='MIT',
      packages=['tradingview', 'googlesheet'],
      package_dir={
          'tradingview': 'src/tradingview',
          'googlesheet': 'src/googlesheet',
          'data_providers': 'src/data_providers',
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
