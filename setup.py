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
      },
      install_requires=[
          'google-auth==2.22.0',
          'gspread-dataframe==3.3.1'
          'gspread==5.10.0',
      ],
      zip_safe=False)
