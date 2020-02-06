#!/usr/bin/env python3

import math
from collections import Counter
import re
import numpy as np
from numpy.linalg import norm
import pandas as pd

from preprocessing import *

'''
--------------------------------------------------------------
Main analysis class

The analysis logic is inspired by the following article:
Schrum, P., Rintoul, M.D., & Newton, B.D. (2018). Curvature Based Analysis to Identify and Categorize Trajectory Segments.

This class serves as the main class for analyzing motion trajectory, with plot object created

Usage:  Pass the file path and turning thresholds when initializing the Analysis class 
        (e.g., analysis = Analysis(file, thresholds))
                
        Goal:
        To create a hash string that describes the trajectory
        
        The labelling of the trajectory is separated into three levels:
            Level 1:
            With a sliding window (window_size=2, hop_size=1) (i, i+1), this script determines the heading direction of the two
            points and assign a label for each dimension, this results in 3 rows of labels. The three rows state the X 
            dimension, Y dimension, and Z dimension movements respectively. The X dimension is either Left=L, Right=R,
            or NoChange=-; the Y dimension is either Forward=F, Backward=B, or NoChange=-; the Z dimension is either Up=U, Down=D,
            or NoChange=-. 
            
            Level 2:
            After acquiring three rows of n-1 level-1 labels, this script groups consecutive sets of label. In other words, 
            if all three rows are the same in consecutive frames, they are grouped into one set.
            
            Level 3:
            When a level-2 node is grouped from more than a threshold of level-1 nodes, it is considered to be a "main 
            direction", otherwise it is considered to be a "change in direction". They will be labelled as uppercase and
            lowercase letters respectively. Furthermore, consecutive changes in direction will also be grouped.

Parameters:  X global angle, Y global angle, Z global angle, relative angle, arc length, radius, curvature vector(3)
--------------------------------------------------------------
'''


#######################
# Main analysis class #
#######################
class Analysis:

    def __init__(self, file, col_x, col_y, col_z, x_threshold, y_threshold, z_threshold, main_direction_threshold,
                 invert_x=False, invert_y=False, invert_z=False,
                 header=None, smooth=False, interpolate=False, interdist=0.5):
        # Set object attributes
        self.x_threshold = x_threshold
        self.y_threshold = 90 - y_threshold
        self.z_threshold = 90 - z_threshold
        self.main_direction_threshold = main_direction_threshold
        self.invert_x = invert_x
        self.invert_y = invert_y
        self.invert_z = invert_z

        # Update header
        if header is not None: header -= 1

        # Read .csv file and assign to variables
        dataset = pd.read_csv(file, header=header, engine="python")
        x = dataset.iloc[:, col_x-1].values
        y = dataset.iloc[:, col_y-1].values
        z = dataset.iloc[:, col_z-1].values
        self.original_corr = np.asarray([x, y, z]).T

        # Preprocessing
        self._preprocessing(x, y, z, smooth, interpolate, interdist)

        # Get level-1 hash
        self._lvl1hash()

        # Get level-2 hash
        self._lvl2hash()

        # Get level-3 hash
        self._lvl3hash()

        # Get post-interpolated to pre-interpolated conversion of data points
        self._get_prepost_idx()

        # Create plot object
        self.plot = Plot(self.x, self.y, self.z, self.lvl2hashframe, self.lvl3hashframe)

    # Preprocessing
    def _preprocessing(self, x, y, z, smooth, interpolate, interdist):
        self.X, self.pre_post_idx = preprocess(x, y, z, smooth=smooth, interpolate=interpolate, interdist=interdist)
        self.x = self.X[:, 0]
        self.y = self.X[:, 1]
        self.z = self.X[:, 2]

    # Get level-1 hash string and parameters of each node
    def _lvl1hash(self):
        # Initialize variables
        self.lvl1hash = [''] * 3
        self.parameters = np.empty((len(self.x), 9), dtype=object)

        # Loop through point duplets
        for i in range(len(self.x) - 1):
            # Compute directional vector
            direction_vector = [self.x[i+1] - self.x[i], self.y[i+1] - self.y[i], self.z[i+1] - self.z[i]]

            # Compute angular change in x/y and z
            angle1 = math.degrees(math.atan2(direction_vector[1], direction_vector[0]))
            angle2 = math.degrees(math.atan2(direction_vector[2], math.sqrt(direction_vector[0]**2 + direction_vector[1]**2)))

            # Determine left/right
            if abs(angle1) <= self.x_threshold:
                self.lvl1hash[0] += 'R' if self.invert_x else 'L'
            elif abs(angle1) >= 180 - self.x_threshold:
                self.lvl1hash[0] += 'L' if self.invert_x else 'R'
            else:
                self.lvl1hash[0] += '-'
            self.parameters[i, 0] = angle1

            # Determine forward/backward
            if self.y_threshold < angle1 < 180 - self.y_threshold:
                self.lvl1hash[1] += 'F' if self.invert_y else 'B'
            elif -(180 - self.y_threshold) < angle1 < -self.y_threshold:
                self.lvl1hash[1] += 'B' if self.invert_y else 'F'
            else:
                self.lvl1hash[1] += '-'
            self.parameters[i, 1] = angle1

            # Determine up/down
            if angle2 >= self.z_threshold:
                self.lvl1hash[2] += 'D' if self.invert_z else 'U'
            elif angle2 <= -self.z_threshold:
                self.lvl1hash[2] += 'U' if self.invert_z else 'D'
            else:
                self.lvl1hash[2] += '-'
            self.parameters[i, 2] = angle2

        # '/' padding
        self.lvl1hash[0] += '/'
        self.lvl1hash[1] += '/'
        self.lvl1hash[2] += '/'

        # Compute parameters
        for i in range(1, len(self.x) - 1):
            self.parameters[i, 3] = self.__find_angle(self.X[i-1], self.X[i], self.X[i+1])

        L, R, k = self.__curvature()
        self.parameters[:, 4] = L
        self.parameters[:, 5] = R
        self.parameters[:, 6:] = k

    # Get level-2 hash strings and hash frame
    def _lvl2hash(self):
        # Initialize variables
        self.lvl2hash = [''] * 3
        self.lvl2hashframe = [0]

        # Loop through level-3 nodes
        Xchar, Ychar, Zchar = self.lvl1hash[0][0], self.lvl1hash[1][0], self.lvl1hash[2][0]
        for i in range(1, len(self.lvl1hash[0])):
            if self.lvl1hash[0][i] == Xchar and self.lvl1hash[1][i] == Ychar and self.lvl1hash[2][i] == Zchar:
                continue
            else:
                self.lvl2hash[0] += Xchar
                self.lvl2hash[1] += Ychar
                self.lvl2hash[2] += Zchar
                self.lvl2hashframe.append(i)
                Xchar = self.lvl1hash[0][i]
                Ychar = self.lvl1hash[1][i]
                Zchar = self.lvl1hash[2][i]

        # '/' padding
        self.lvl2hash[0] += '/'
        self.lvl2hash[1] += '/'
        self.lvl2hash[2] += '/'

    # Get level-3 hash string and hash frame
    def _lvl3hash(self):
        # Initialize hash and hash frame variables
        self.lvl3hash = []
        self.lvl3hashframe = []

        # Group the three rows of level-2 hash strings into one
        # Remove 'n'
        # Change in direction is defined as Level-2 consecutive grouping smaller than main_direction_threshold
        # Change in direction is denoted with lowercase
        for i in range(len(self.lvl2hashframe)-1):
            # Line segment is larger than main_direction threshold
            if self.lvl2hashframe[i+1] - self.lvl2hashframe[i] >= self.main_direction_threshold:
                temp = self.lvl2hash[0][i] + self.lvl2hash[1][i] + self.lvl2hash[2][i]
                # Regex for substituting 'n' with blank
                temp = re.sub('[-]', '', temp)
            # Line segment is a change in direction
            else:
                temp = (self.lvl2hash[0][i] + self.lvl2hash[1][i] + self.lvl2hash[2][i]).lower()
                # Regex for substituting 'n' with blank
                temp = re.sub('[-]', '', temp)

            if temp != '':
                self.lvl3hash.append(temp)
                self.lvl3hashframe.append(self.lvl2hashframe[i])

        # Group consecutive change in directions (lowercase)
        temphash = [self.lvl3hash[0]]
        temphashframe = [self.lvl3hashframe[0]]
        for i in range(1, len(self.lvl3hash)):
            if self.lvl3hash[i].isupper():
                temphash.append(self.lvl3hash[i])
                temphashframe.append(self.lvl3hashframe[i])
            elif self.lvl3hash[i].islower() and temphash[-1].islower():
                temphash[-1] += self.lvl3hash[i]
            else:
                temphash.append(self.lvl3hash[i])
                temphashframe.append(self.lvl3hashframe[i])

        # Mark the last frame of the Level-1 hash
        temphashframe.append(self.lvl2hashframe[-1])

        self.lvl3hash = temphash
        self.lvl3hashframe = temphashframe

        while True:
            length = len(self.lvl3hash)
            # Remove main direction axes from change in direction
            for h in range(len(self.lvl3hash)):
                # Only make amendments to lowercase strings
                if self.lvl3hash[h].islower():
                    # Get strings of main direction
                    if h == 0:
                        continue
                    elif h == len(self.lvl3hash) - 1:
                        continue
                    else:
                        j = h - 1
                        while True:
                            if self.lvl3hash[j].isupper():
                                main_axis1 = self.lvl3hash[j]
                                break
                            j -= 1
                        main_axis2 = self.lvl3hash[h + 1]

                    # Identify which main axes to remove
                    include = [0, 1, 2]
                    if ('F' in main_axis1 or 'B' in main_axis1) and ('F' in main_axis2 or 'B' in main_axis2):
                        include.remove(0)
                    if ('L' in main_axis1 or 'R' in main_axis1) and ('L' in main_axis2 or 'R' in main_axis2):
                        include.remove(1)
                    if ('U' in main_axis1 or 'D' in main_axis1) and ('U' in main_axis2 or 'D' in main_axis2):
                        include.remove(2)

                    # Remove labels according to main axes
                    if 0 not in include:
                        self.lvl3hash[h] = list(filter(lambda a: a not in 'fb', self.lvl3hash[h]))
                    if 1 not in include:
                        self.lvl3hash[h] = list(filter(lambda a: a not in 'lr', self.lvl3hash[h]))
                    if 2 not in include:
                        self.lvl3hash[h] = list(filter(lambda a: a not in 'ud', self.lvl3hash[h]))

                    # Join string and remove duplicate characters
                    if self.lvl3hash[h] != []:
                        c = Counter(self.lvl3hash[h])
                        highest = max(c.values())
                        result = [k for k, v in c.items() if v == highest]
                    else:
                        result = ""
                    self.lvl3hash[h] = ''.join(set(result))

                    # Remove turn between two identical main direction
                    try:
                        if main_axis1 == main_axis2:
                            self.lvl3hash[h + 1] = ""
                            self.lvl3hash[h] = ""
                    except IndexError:
                        pass

            # List all index where "" empty string
            ix = [i for i, s in enumerate(self.lvl3hash) if s == '']
            ix.reverse()

            for i in ix:
                self.lvl3hash.pop(i)
                self.lvl3hashframe.pop(i)

            if len(self.lvl3hash) == length:
                break

        # END Padding
        self.lvl3hash.append("END")

    # Get post-interpolated to pre-interpolated conversion of data points
    def _get_prepost_idx(self):
        self.idx = []
        for fr in self.lvl3hashframe:
            self.idx.append(np.where((self.pre_post_idx >= fr) == True)[0][0])

    @staticmethod
    def __find_angle(p1, p2, p3):
        p1 = np.array(p1)
        p2 = np.array(p2)
        p3 = np.array(p3)
        with np.errstate(divide='ignore', invalid='ignore'):
            n1 = (p3 - p2) / norm(p3 - p2)
            n2 = (p1 - p2) / norm(p1 - p2)
        return math.degrees(math.atan2(norm(np.cross(n1, n2)), np.dot(n1, n2)))

    def __curvature(self):

        def circumcenter(A, B, C):
            D = np.cross(B - A, C - A)
            b = norm(A - C)
            c = norm(A - B)

            E = np.cross(D, B - A)
            F = np.cross(D, C - A)
            with np.errstate(divide='ignore', invalid='ignore'):
                G = (b * b * E - c * c * F) / norm(D) ** 2 / 2
            M = A + G
            R = norm(G)
            if R == 0:
                k = G
            else:
                k = G / (R * R)
            return R, M, k

        N = self.X.shape[0]
        L = np.zeros(N)
        R = np.full(N, np.NAN)
        k = np.full((N, 3), np.NAN)
        for i in range(1, N - 1):
            R[i], _, k[i, :] = circumcenter(self.X[i], self.X[i - 1], self.X[i + 1])
            L[i] = L[i - 1] + norm(self.X[i] - self.X[i - 1])
        i = N - 1
        L[i] = L[i - 1] + L[i - 1] + norm(self.X[i] - self.X[i - 1])
        return L, R, k

    # Re-run analysis
    def rerun(self):
        self._lvl1hash()
        self._lvl2hash()
        self._lvl3hash()
        self._get_prepost_idx()
        self.plot = Plot(self.x, self.y, self.z, self.lvl2hashframe, self.lvl3hashframe)


####################################
# Class for getting plot materials #
####################################
class Plot:

    def __init__(self, x, y, z, lvl2hashframe, lvl3hashframe):
        self.x = x
        self.y = y
        self.z = z
        self.lvl2hashframe = lvl2hashframe
        self.lvl3hashframe = lvl3hashframe
        self.max_min = np.array([max(x), min(x), max(y), min(y), max(z), min(z)])

    def initplot_lvl1(self):
        mainplot = [self.x[0:2], self.y[0:2], self.z[0:2]]
        return [mainplot, self.max_min]

    def initplot_lvl2(self):
        mainplot = [self.x[0:self.lvl2hashframe[1]], self.y[0:self.lvl2hashframe[1]], self.z[0:self.lvl2hashframe[1]]]
        return [mainplot, self.max_min]

    def initplot_lvl3(self):
        mainplot = [self.x[0:self.lvl3hashframe[1]], self.y[0:self.lvl3hashframe[1]], self.z[0:self.lvl3hashframe[1]]]
        return [mainplot, self.max_min]

    def updateplot_lvl1(self, node):
        mainplot = [self.x[node:node+2], self.y[node:node+2], self.z[node:node+2]]
        faintplot_tail = [self.x[node-1:node+1], self.y[node-1:node+1], self.z[node-1:node+1]] if node != 0 else None
        return [mainplot, faintplot_tail, self.max_min]

    def updateplot_lvl2(self, node):
        mainplot = [self.x[self.lvl2hashframe[node]:self.lvl2hashframe[node+1]+1],
                    self.y[self.lvl2hashframe[node]:self.lvl2hashframe[node+1]+1],
                    self.z[self.lvl2hashframe[node]:self.lvl2hashframe[node+1]+1]]
        faintplot_tail = [self.x[self.lvl2hashframe[node]-1:self.lvl2hashframe[node]+1],
                          self.y[self.lvl2hashframe[node]-1:self.lvl2hashframe[node]+1],
                          self.z[self.lvl2hashframe[node]-1:self.lvl2hashframe[node]+1]] if node != 0 else None
        return [mainplot, faintplot_tail, self.max_min]

    def updateplot_lvl3(self, node):
        mainplot = [self.x[self.lvl3hashframe[node]:self.lvl3hashframe[node+1]+1],
                    self.y[self.lvl3hashframe[node]:self.lvl3hashframe[node+1]+1],
                    self.z[self.lvl3hashframe[node]:self.lvl3hashframe[node+1]+1]]
        faintplot_tail = [self.x[self.lvl3hashframe[node]-1:self.lvl3hashframe[node]+1],
                          self.y[self.lvl3hashframe[node]-1:self.lvl3hashframe[node]+1],
                          self.z[self.lvl3hashframe[node]-1:self.lvl3hashframe[node]+1]] if node != 0 else None
        return [mainplot, faintplot_tail, self.max_min]
