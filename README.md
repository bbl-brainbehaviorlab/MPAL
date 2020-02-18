# MPAL (Motion Pattern Analysis)
#### A Python Open Source Application for the Trajectory Analysis of Hand Motion

## What is MPAL?
MPAL is a Python open-source and interactive application designed for analyzing hand motion. This application takes 3D
coordinates retrieved from, for example, a motion tracking device, and visualizes the data frame-by-frame together with 
algorithm-generated labels that describe motion pattern. All folders and files under this repository are released under
the GNU-GPL v3.0 license (see LICENSE).

## Installing MPAL
1. Download the latest official release from <https://github.com/bbl-brainbehaviorlab/MPAL/archive/master.zip> and extract it.<br>
**OR**<br>
Clone the repository using `git clone https://github.com/bbl-brainbehaviorlab/MPAL.git`.

2. Install Python 3.7.

3. Install pip and setuptools.

4. On terminal, use `cd` to change directory to the extracted folder.<br>
(E.g., `cd <directory_path>/MPAL-master`)

5. Use `pip install .` or `pip3 install .` to install all dependencies.

## To use MPAL
1. On terminal, use `cd` to change directory to the MPAL subfolder within the main application folder.<br>
(E.g., `cd <directory_path>/MPAL-master/MPAL`)<br>
(You should see *\_\_init\_\_.py*, *app.py*, *analysis.py*, & *preprocessing.py* in this folder)

2. Enter `python3 app.py` to run the application.
