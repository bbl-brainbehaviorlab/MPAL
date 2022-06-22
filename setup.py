import setuptools

setuptools.setup(
    name="MPAL",
    version="1.0.0",
    url="https://github.com/bbl-brainbehaviorlab/MPAL",
    packages=setuptools.find_packages(),
    description="Motion Pattern Analysis (MPAL): A Python Open Source Application for the Trajectory Analysis of Hand Motion",
    long_description=open("README.md").read(),
    install_requires=[
        "numpy == 1.22.0",
        "scipy == 1.3.1",
        "pandas == 0.25.1",
        "matplotlib == 3.0.3",
        "PyQt5 == 5.13.0",
    ],
    python_requires='>=3.7',
)
