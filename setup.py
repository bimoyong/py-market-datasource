from setuptools import setup, find_packages

setup(name='py_market_datasource',
      version='1.0.0',
      description='Interface with data from many data sources',
      url='https://github.com/bimoyong/py-market-datasource',
      author='Trung',
      author_email='trung@t7.sg',
      license='MIT',
      packages=find_packages(where='src'),
      package_dir={'': 'src'},
      # packages=[
      #     'data_providers',
      #     'models',
      # ],
      # package_dir={
      #     'data_providers': 'src/data_providers',
      #     'models': 'src/models',
      # },
      install_requires=[
          'dependency-injector==4.45.0',
          'pandas==2.2.3',
          'pydantic==2.10.6',
          'tenacity==9.0.0',
          'websocket-client==1.8.0',
      ],
      zip_safe=False)
