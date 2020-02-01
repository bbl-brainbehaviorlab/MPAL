# MPAL (Motion Pattern Analysis)
#### A Python Open Source Application for the Trajectory Analysis of Hand Motion

## What is MPAL?
MPAL is a Python open-source and interactive application designed for analyzing hand motion. This application takes 3D
coordinates retrieved from, for example, a motion tracking device, and visualizes the data frame-by-frame together with 
algorithm-generated labels that describe motion pattern. All folders and files under this repository are released under
the GNU-GPL v3.0 license (see LICENSE).

## Installation Guide
1. Download the repository and extract it.
2. Open terminal.
3. Install Python 3.7.
3. Install `pip` and `setuptools`.
4. Use `cd` to change directory to the extracted folder.
(E.g., `cd <directory_path>/MPAL-master`)
5. Use `pip install .` or `pip3 install .` to install all dependencies.

## Run MPAL
1. Open terminal.
2. Use `cd` to change directory to the MPAL subfolder within the main application folder.
(E.g., `cd <directory_path>/MPAL-master/MPAL`) (You should see *\_\_init\_\_.py*, *app.py*, *analysis.py*, & *preprocessing.py* in this folder)
3. Enter `python3 app.py` to run the application.
