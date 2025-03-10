from setuptools import setup, find_namespace_packages

setup(
    name="metrics_sdk",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_namespace_packages(include=["metrics_sdk", "metrics_sdk.*"]),
    install_requires=[
        'requests>=2.31.0',
        'python-dateutil>=2.8.2'
    ],
) 