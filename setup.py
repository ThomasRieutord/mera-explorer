import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mera_explorer",
    version="0.1",
    author="Thomas Rieutord",
    author_email="thomas.rieutord@met.ie",
    description="""The Met Eireann ReAnalysis explorer.
    Package to easily browse and manipulate the content of MERA (meant for internal use only).
    
    Last revision of the documentation: 16 Jan. 2024""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/ThomasRieutord/mera_explorer",
    packages=setuptools.find_packages(),
    classifiers=(
        "Environment :: Console"
        "Programming Language :: Python :: 3",
        "Operating System :: Linux",
        "Development Status :: Experimental",
    ),
)
