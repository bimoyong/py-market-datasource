from setuptools import setup

setup(name='py_datasource',
      version='1.0.5',
      description='Interface with data from many data sources',
      url='https://github.com/TsevenSG/py-datasource',
      author='Trung',
      author_email='trung@t7.sg',
      license='MIT',
      packages=[
          'data_providers',
          'tradingview',
      ],
      package_dir={
          'data_providers': 'src/data_providers',
          'tradingview': 'src/tradingview',
      },
      install_requires=[
          'dependency-injector==4.41.0',
          'pydantic==1.10.13',
          'websocket-client==1.6.3',
      ],
      zip_safe=False)
