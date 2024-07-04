from setuptools import setup

setup(name='py_datasource',
      version='1.0.8',
      description='Interface with data from many data sources',
      url='https://github.com/TsevenSG/py-datasource',
      author='Trung',
      author_email='trung@t7.sg',
      license='MIT',
      packages=[
          'data_providers',
          'model': 'src/model',
          'tradingview',
      ],
      package_dir={
          'data_providers': 'src/data_providers',
          'model': 'src/model',
          'tradingview': 'src/tradingview',
      },
      install_requires=[
          'dependency-injector==4.41.0',
          'pandas==2.1.1',
          'pydantic==2.6.4',
          'websocket-client==1.6.3',
      ],
      zip_safe=False)
