from setuptools import setup, find_packages
import os

version = '0.2.4'

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
except IOError:
    README = ''

setup(name='tgext.debugbar',
      version=version,
      description="Provides debug toolbar for TurboGears2",
      long_description=README,
      classifiers=[
        "Environment :: Web Environment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: TurboGears"
        ],
      keywords='turbogears2.widgets',
      author='Alessandro Molina',
      author_email='alessandro.molina@axant.it',
      url='https://pypi.python.org/pypi/tgext.debugbar',
      license='MIT',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['tgext'],
      include_package_data=True,
      package_data = {'': ['*.html', '*.js', '*.css', '*.png', '*.gif']},
      zip_safe=False,
      install_requires=[
        "TurboGears2 >= 2.2.0",
        "Pygments",
        "Genshi"
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
