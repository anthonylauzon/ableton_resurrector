from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

packages = find_packages(exclude=('tests', 'docs'))

setup(
    name='ableton_resurrector',
    version='0.0.1',
    description='Ableton Resurrector',
    long_description=readme,
    author='Anthony Lauzon',
    author_email='ant@systematic.systems',
    url='https://github.com/anthonylauzon/ableton_resurrector',
    license=license,
    packages=packages,
    install_requires=[
        'mdfind>=2018.11.20',
        'beautifulsoup4>=4.7.1'
    ],
    entry_points = {
        'console_scripts': [
            'ableton_resurrector=ableton_resurrector.ableton_resurrector:main'
        ]
    }
)
