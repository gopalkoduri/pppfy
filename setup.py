from setuptools import setup, find_packages

setup(
    name="pppfy",
    version="1.0.0",
    description="A Python package to get prices based on Purchasing Power Parity (PPP)",
    author="Gopala Krishna Koduri",
    author_email="gopal@riyazapp.com",
    url="https://riyazapp.com",
    packages=find_packages(),
    package_data={
        "ppp": ["data/*.csv"],  # Include CSV files in the data directory within the ppp package
    },
    include_package_data=True,
    install_requires=[
        # List your package dependencies here
        # 'numpy', 'pandas', etc.
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
