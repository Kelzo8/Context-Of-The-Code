from setuptools import setup, find_packages

setup(
    name="metrics_sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'requests>=2.31.0',
        'python-dateutil>=2.8.2'
    ],
) 