import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='backuper',
    version='1.0.0b',
    packages=['backuper',],
    include_package_data=True,
    license='BSD License',  # example license
    description='Backuper tools',
    long_description=README,
    url='http://www.cygame.ru/',
    author='Ernado',
    author_email='ernado@ya.ru',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    #install_requires = [
    #    'PIL>=1.1.7',
    #    'Django>=1.4'
    #],
)