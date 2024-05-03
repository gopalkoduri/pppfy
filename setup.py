from setuptools import setup, find_packages

setup(
    name="pppfy",
    version="2024.05.03",
    description="A Python package to get prices based on Purchasing Power Parity (PPP)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",  # Ensure you include a README.md in your package
    author="Gopala Krishna Koduri",
    author_email="gopal@riyazapp.com",
    url="https://github.com/musicmuni/pppfy",  # Company URL
    project_urls={  # Additional URLs
        "Source Code": "https://github.com/musicmuni/pppfy",
        "Issue Tracker": "https://github.com/musicmuni/pppfy/issues",
        "Connect w/ Author": "https://linkedin.com/in/gopalkoduri",
        "Riyaz - Learn to sing": "https://riyazapp.com",
    },
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
