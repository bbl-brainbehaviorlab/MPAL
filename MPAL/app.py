#!/usr/bin/env python3

'''
Libraries needed:
numpy, scipy, pandas, matplotlib, pyqt5
'''

import os
import csv
import pickle
from functools import partial

from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
from scipy.io import savemat

from analysis import *
from plot import *

# App info
appname = "MPAL"
version = "1.0.0"
release_date = "January 31, 2020"
update_date = "January 31, 2020"


#########################
# Main class of the app #
#########################
class App(QtWidgets.QMainWindow):

    def __init__(self):
        # Initialize main window
        super().__init__()
        self.setWindowTitle(appname)
        self.setGeometry(10, 10, 700, 800)
        self.setContextMenuPolicy(QtCore.Qt.NoContextMenu)

        # Initialize UI components
        self.settings = Settings()
        self.openfile = OpenFile()
        self.initUI()
        self.dropdownUI()
        credit = QtWidgets.QLabel("{} v{}".format(appname, version))
        self.statusBar().addPermanentWidget(credit)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Set color palette
        self.setAutoFillBackground(True)
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.Window, QtGui.QColor(220, 220, 220))
        p.setColor(QtGui.QPalette.WindowText, QtCore.Qt.black)
        p.setColor(QtGui.QPalette.Base, QtCore.Qt.white)
        p.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(220, 220, 220))
        p.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
        p.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.black)
        p.setColor(QtGui.QPalette.PlaceholderText, QtCore.Qt.black)
        p.setColor(QtGui.QPalette.Text, QtCore.Qt.black)
        p.setColor(QtGui.QPalette.Button, QtGui.QColor(220, 220, 220))
        p.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.black)
        p.setColor(QtGui.QPalette.BrightText, QtCore.Qt.black)
        self.setPalette(p)

        # Set variable for operation check
        self.operating = False

        # Set variable for processing level
        self.processing_level = 1

        # Set variable for position tracking
        self.current_pos = 0

        # Set initial plot attributes
        self.zoom = 1.0

        self.show()

    # Initialize UI layout and elements
    def initUI(self):
        # Create main widget with main_layout
        # Put upper_layout and botton_layout inside main_layout
        # Put plot_layout and label_layout in upper_layout
        # Put bottom_left_layout, scroll_layout, and bottom_right_layout in bottom_layout
        main_widget = QtWidgets.QWidget(self)
        main_layout = QtWidgets.QVBoxLayout(main_widget)
        upper_layout = QtWidgets.QVBoxLayout()
        bottom_layout = QtWidgets.QHBoxLayout()
        plot_layout = QtWidgets.QVBoxLayout()
        label_layout = QtWidgets.QVBoxLayout()
        bottom_left_layout = QtWidgets.QHBoxLayout()
        bottom_mid_layout = QtWidgets.QHBoxLayout()
        bottom_right_layout = QtWidgets.QHBoxLayout()

        main_layout.addLayout(upper_layout)
        main_layout.addLayout(bottom_layout)
        upper_layout.addLayout(plot_layout)
        upper_layout.addLayout(label_layout)
        bottom_layout.addLayout(bottom_left_layout)
        bottom_layout.addLayout(bottom_mid_layout)
        bottom_layout.addLayout(bottom_right_layout)

        # Initialize 3D plot object
        self.m = PlotCanvas(dpi=self.settings.dpi)
        plot_layout.addWidget(self.m)

        # Separation line after plot
        line = QtWidgets.QFrame(main_widget)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        plot_layout.addWidget(line)

        # Create label to describe point trajectory
        # Put it in label_layout
        font = QtGui.QFont()
        font.setPointSize(16)
        self.trajlabel = QtWidgets.QLabel("/", main_widget)
        self.trajlabel.setFont(font)
        self.trajlabel.setAlignment(QtCore.Qt.AlignCenter)
        label_layout.addWidget(self.trajlabel)

        # Create zoom out, zoom in buttons, and zoom label
        # Put them in bottom_left_layout
        bottom_left_layout.addStretch()
        self.zoom_out_btn = QtWidgets.QPushButton("-", main_widget)
        self.zoom_out_btn.setMaximumWidth(40)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self.zoom_out_btn.sizePolicy().hasHeightForWidth())
        self.zoom_out_btn.setSizePolicy(sizePolicy)
        self.zoom_out_btn.setShortcut('Down')
        self.zoom_out_btn.setStatusTip("Zoom out")
        self.zoom_out_btn.setDefault(False)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        bottom_left_layout.addWidget(self.zoom_out_btn)

        self.zoom_lbl = QtWidgets.QLabel("1.0", main_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self.zoom_lbl.sizePolicy().hasHeightForWidth())
        self.zoom_lbl.setSizePolicy(sizePolicy)
        self.zoom_lbl.setAlignment(QtCore.Qt.AlignCenter)
        bottom_left_layout.addWidget(self.zoom_lbl)

        self.zoom_in_btn = QtWidgets.QPushButton("+", main_widget)
        self.zoom_in_btn.setMaximumWidth(40)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self.zoom_in_btn.sizePolicy().hasHeightForWidth())
        self.zoom_in_btn.setSizePolicy(sizePolicy)
        self.zoom_in_btn.setShortcut('Up')
        self.zoom_in_btn.setStatusTip("Zoom in")
        self.zoom_in_btn.setDefault(False)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        bottom_left_layout.addWidget(self.zoom_in_btn)
        bottom_left_layout.addStretch()

        # Button for changing the labels
        bottom_mid_layout.addStretch()
        self.change_btn = QtWidgets.QPushButton("Change Labels", main_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self.change_btn.sizePolicy().hasHeightForWidth())
        self.change_btn.setSizePolicy(sizePolicy)
        self.change_btn.setStatusTip("Make changes to labels")
        self.change_btn.setDefault(False)
        self.change_btn.setDisabled(True)
        self.change_btn.clicked.connect(self.change_label)
        bottom_mid_layout.addWidget(self.change_btn)
        bottom_mid_layout.addStretch()

        # Create scroll left, scroll right buttons, and scroll textbox
        # Put them in bottom_right_layout
        self.scroll_left_btn = QtWidgets.QPushButton("<", main_widget)
        self.scroll_left_btn.setMaximumWidth(40)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self.scroll_left_btn.sizePolicy().hasHeightForWidth())
        self.scroll_left_btn.setSizePolicy(sizePolicy)
        self.scroll_left_btn.setShortcut('Left')
        self.scroll_left_btn.setStatusTip("Scroll to the previous segment")
        self.scroll_left_btn.setDefault(False)
        self.scroll_left_btn.setDisabled(True)
        self.scroll_left_btn.clicked.connect(self.scroll_left)
        bottom_right_layout.addWidget(self.scroll_left_btn)

        self.scroll_txt_le = QtWidgets.QLineEdit("0", main_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self.scroll_txt_le.sizePolicy().hasHeightForWidth())
        self.scroll_txt_le.setSizePolicy(sizePolicy)
        self.scroll_txt_le.setMaxLength(8)
        self.scroll_txt_le.setAlignment(QtCore.Qt.AlignCenter)
        self.scroll_txt_le.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]\\d{0,8}")))
        self.scroll_txt_le.setReadOnly(True)
        self.scroll_txt_le.textChanged.connect(self.scroll_textChange)
        self.scroll_txt_le.returnPressed.connect(self.scroll_enter)
        self.scroll_txt_le.installEventFilter(self)
        bottom_right_layout.addWidget(self.scroll_txt_le)

        self.scroll_right_btn = QtWidgets.QPushButton(">", main_widget)
        self.scroll_right_btn.setMaximumWidth(40)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self.scroll_right_btn.sizePolicy().hasHeightForWidth())
        self.scroll_right_btn.setSizePolicy(sizePolicy)
        self.scroll_right_btn.setShortcut('Right')
        self.scroll_right_btn.setStatusTip("Scroll to the next segment")
        self.scroll_right_btn.setDefault(False)
        self.scroll_right_btn.setDisabled(True)
        self.scroll_right_btn.clicked.connect(self.scroll_right)
        bottom_right_layout.addWidget(self.scroll_right_btn)
        bottom_right_layout.addStretch()

        # Finishing touches
        main_widget.setFocus()
        self.setCentralWidget(main_widget)
        QtCore.QMetaObject.connectSlotsByName(self)

    # Create drop down menu items
    def dropdownUI(self):
        # Create menu bar
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        # Create "File" menu
        file_menu = QtWidgets.QMenu('&File', self)

        newButton = QtWidgets.QAction('&New', self)
        newButton.setStatusTip("Clear windows")
        newButton.triggered.connect(self.newfile)
        file_menu.addAction(newButton)

        openButton = QtWidgets.QAction('&Open...', self)
        openButton.setShortcut('Ctrl+O')
        openButton.setStatusTip("Open file")
        openButton.triggered.connect(self.fileopen)
        file_menu.addAction(openButton)

        self.exportcoordsButton = QtWidgets.QAction('&Export Coordinates', self)
        self.exportcoordsButton.setStatusTip("Export trajectory coordinates to CSV")
        self.exportcoordsButton.setDisabled(True)
        self.exportcoordsButton.triggered.connect(self.export_coords)
        file_menu.addAction(self.exportcoordsButton)

        self.saveButton = QtWidgets.QAction('&Save Results...', self)
        self.saveButton.setShortcut('Ctrl+S')
        self.saveButton.setStatusTip("Save results")
        self.saveButton.setDisabled(True)
        self.saveButton.triggered.connect(self.save)
        file_menu.addAction(self.saveButton)

        # TODO: save trajectory animation
        self.saveTrajectoryButton = QtWidgets.QAction('&Save Trajectory Animation', self)
        self.saveTrajectoryButton.setStatusTip("Save trajectory animation")
        self.saveTrajectoryButton.setDisabled(True)
        # self.saveTrajectoryButton.triggered.connect(self.savetrajectory)
        file_menu.addAction(self.saveTrajectoryButton)

        file_menu.addSeparator()
        exitButton = QtWidgets.QAction('&Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.setStatusTip("Exit application")
        exitButton.triggered.connect(self.close)
        file_menu.addAction(exitButton)

        menubar.addMenu(file_menu)

        # Create "Edit" menu
        edit_menu = QtWidgets.QMenu('&Edit', self)

        menubar.addMenu(edit_menu)

        # Create "View" menu
        view_menu = QtWidgets.QMenu('&View', self)

        self.jumpstartButton = QtWidgets.QAction('&Jump to Front', self)
        self.jumpstartButton.setShortcut('Ctrl+Left')
        self.jumpstartButton.setStatusTip("Jump to the first label")
        self.jumpstartButton.triggered.connect(self.jumpstart)
        self.jumpstartButton.setDisabled(True)
        view_menu.addAction(self.jumpstartButton)

        self.jumpendButton = QtWidgets.QAction('&Jump to End', self)
        self.jumpendButton.setShortcut('Ctrl+Right')
        self.jumpendButton.setStatusTip("Jump to the last label")
        self.jumpendButton.triggered.connect(self.jumpend)
        self.jumpendButton.setDisabled(True)
        view_menu.addAction(self.jumpendButton)

        view_menu.addSeparator()

        self.lvl3Button = QtWidgets.QAction('&Show Level 1 Processing', self)
        self.lvl3Button.setShortcut('Ctrl+1')
        self.lvl3Button.setStatusTip("Display level 1 processing trajectory and labels")
        self.lvl3Button.triggered.connect(self.lvl1switch)
        self.lvl3Button.setDisabled(True)
        view_menu.addAction(self.lvl3Button)

        self.lvl2Button = QtWidgets.QAction('&Show Level 2 Processing', self)
        self.lvl2Button.setShortcut('Ctrl+2')
        self.lvl2Button.setStatusTip("Display level 2 processing trajectory and labels")
        self.lvl2Button.triggered.connect(self.lvl2switch)
        self.lvl2Button.setDisabled(True)
        view_menu.addAction(self.lvl2Button)

        self.lvl1Button = QtWidgets.QAction('&Show Level 3 Processing', self)
        self.lvl1Button.setShortcut('Ctrl+3')
        self.lvl1Button.setStatusTip("Display level 3 processing trajectory and labels")
        self.lvl1Button.triggered.connect(self.lvl3switch)
        self.lvl1Button.setDisabled(True)
        view_menu.addAction(self.lvl1Button)

        view_menu.addSeparator()

        self.animationButton = QtWidgets.QAction('&Show Animated Trajectory', self)
        self.animationButton.setShortcut('Ctrl+T')
        self.animationButton.setStatusTip("Display an animated trajactory")
        self.animationButton.triggered.connect(self.trajectory)
        self.animationButton.setDisabled(True)
        view_menu.addAction(self.animationButton)

        menubar.addMenu(view_menu)

        # Create "Options" menu
        options_menu = QtWidgets.QMenu('&Options', self)

        settingsButton = QtWidgets.QAction('&Settings', self)
        settingsButton.setStatusTip("Edit settings")
        settingsButton.triggered.connect(self.open_settings)
        options_menu.addAction(settingsButton)

        options_menu.addSeparator()

        self.rerunButton = QtWidgets.QAction('&Re-run Analysis', self)
        self.rerunButton.setStatusTip("Re-run the analysis (ALL CHANGES WILL BE LOST!)")
        self.rerunButton.triggered.connect(self.rerun)
        self.rerunButton.setDisabled(True)
        options_menu.addAction(self.rerunButton)

        menubar.addMenu(options_menu)

        # Create "Help" menu
        help_menu = QtWidgets.QMenu('&Help', self)

        aboutButton = QtWidgets.QAction('&About {}'.format(appname), self)
        aboutButton.setStatusTip("About {}".format(appname))
        aboutButton.triggered.connect(self.about)
        help_menu.addAction(aboutButton)

        howtouseButton = QtWidgets.QAction('&How to use?', self)
        howtouseButton.setStatusTip("Instructions on how to use this application")
        howtouseButton.triggered.connect(self.howtouse)
        help_menu.addAction(howtouseButton)

        menubar.addMenu(help_menu)

    def newfile(self):
        self.processing_level = 1
        self.current_pos = 0
        self.trajlabel.setText('/')
        self.zoom = 1.0
        self.zoom_lbl.setText(str(self.zoom))
        self.m.axes.dist = 10
        self.scroll_left_btn.setDisabled(True)
        self.scroll_txt_le.setText('0')
        self.scroll_txt_le.setReadOnly(True)
        self.scroll_right_btn.setDisabled(True)
        self.change_btn.setDisabled(True)
        self.saveButton.setDisabled(True)
        self.exportcoordsButton.setDisabled(True)
        self.saveTrajectoryButton.setDisabled(True)
        self.jumpstartButton.setDisabled(True)
        self.jumpendButton.setDisabled(True)
        self.lvl3Button.setDisabled(True)
        self.lvl2Button.setDisabled(True)
        self.lvl1Button.setDisabled(True)
        self.animationButton.setDisabled(True)
        self.rerunButton.setDisabled(True)
        self.m.clearplot()
        self.operating = False

    def fileopen(self):
        # Set open file flag to false
        self.openfile.valid = False

        # Show the open file dialog
        self.openfile.showUI()

        # Check if the file is valid
        if self.openfile.valid:
            # Reset variables
            self.processing_level = 1
            self.current_pos = 0
            self.scroll_txt_le.setText('0')
            self.zoom = 1.0
            self.zoom_lbl.setText(str(self.zoom))
            self.m.axes.dist = 10

            # Run Analysis
            self.analysis = Analysis(self.openfile.file_path,
                                     self.openfile.col_x, self.openfile.col_y, self.openfile.col_z,
                                     self.settings.x_threshold, self.settings.y_threshold, self.settings.z_threshold,
                                     self.settings.main_direction_threshold,
                                     invert_x=self.openfile.invert_x, invert_y=self.openfile.invert_y,
                                     invert_z=self.openfile.invert_z,
                                     header=self.openfile.header, smooth=self.openfile.smooth,
                                     smooth_order=self.openfile.smooth_order, smooth_window=self.openfile.smooth_window,
                                     interpolate=self.openfile.interpolate, interdist=self.openfile.interpolate_val)

            # Initialize plot
            self.m.initplot(self.analysis.plot.initplot_lvl1(), title='3D trajectory (Level 1)',
                            x_axis='X (Left/Right)', y_axis='Y (Forward/Backward)', z_axis='Z (Up/Down)',
                            invert_x=self.openfile.invert_x, invert_y=self.openfile.invert_y,
                            invert_z=self.openfile.invert_z)

            # Initialize segment labels
            self.trajlabel.setText(self.analysis.lvl1hash[0][0] +
                                   self.analysis.lvl1hash[1][0] +
                                   self.analysis.lvl1hash[2][0])

            # Enable GUI elements
            self.scroll_txt_le.setReadOnly(False)
            self.scroll_right_btn.setDisabled(False)
            self.change_btn.setDisabled(False)
            self.saveButton.setDisabled(False)
            self.exportcoordsButton.setDisabled(False)
            self.saveTrajectoryButton.setDisabled(False)
            self.jumpstartButton.setDisabled(False)
            self.jumpendButton.setDisabled(False)
            self.lvl3Button.setDisabled(False)
            self.lvl2Button.setDisabled(False)
            self.lvl1Button.setDisabled(False)
            self.animationButton.setDisabled(False)
            self.rerunButton.setDisabled(False)
            self.operating = True

    def save(self):
        name = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", self.openfile.file_path[:-4] + "_MPAL",
                                                     "Pickle Files (*.pkl);;MATLAB Files (*.mat);;CSV Files (*.csv)",
                                                     options=QtWidgets.QFileDialog.DontUseNativeDialog)
        if name[0] != '':
            if name[1] == "Pickle Files (*.pkl)":
                with open(name[0] + '.pkl', 'wb') as handle:
                    pickle.dump([self.analysis.original_corr,
                                 self.analysis.X,
                                 self.analysis.x_threshold,
                                 self.analysis.y_threshold,
                                 self.analysis.z_threshold,
                                 self.analysis.main_direction_threshold,
                                 self.analysis.parameters,
                                 self.analysis.lvl1hash,
                                 self.analysis.lvl2hash,
                                 self.analysis.lvl2hashframe,
                                 self.analysis.lvl3hash,
                                 self.analysis.lvl3hashframe,
                                 self.analysis.idx], handle)
            elif name[1] == "MATLAB Files (*.mat)":
                savemat(name[0] + '.mat',
                        {'original_corr': self.analysis.original_corr,
                         'X': self.analysis.X,
                         'x_threshold': self.analysis.x_threshold,
                         'y_threshold': self.analysis.y_threshold,
                         'z_threshold': self.analysis.z_threshold,
                         'main_direction_threshold': self.analysis.main_direction_threshold,
                         'lvl3hash': self.analysis.lvl1hash,
                         'lvl2hash': self.analysis.lvl2hash,
                         'lvl2hashframe': self.analysis.lvl2hashframe,
                         'lvl1hash': self.analysis.lvl3hash,
                         'lvl1hashframe': self.analysis.lvl3hashframe,
                         'idx': self.analysis.idx})
            elif name[1] == "CSV Files (*.csv)":
                # Ensure length of the three outputs are the same
                # (THEY SHOULD BE THE SAME, OTHERWISE SOMETHING WENT WRONG)
                if len(self.analysis.lvl3hash) == len(self.analysis.lvl3hashframe) == len(self.analysis.idx):
                    out1 = np.array(list(map(str, self.analysis.lvl3hash)))
                    out2 = np.array(list(map(str, self.analysis.lvl3hashframe)))
                    out3 = np.array(list(map(str, self.analysis.idx)))
                else:
                    len_arr = max(
                        [len(self.analysis.lvl3hash), len(self.analysis.lvl3hashframe), len(self.analysis.idx)])

                    tmpout1 = np.array(list(map(str, self.analysis.lvl3hash)))
                    out1 = np.empty_like(tmpout1, shape=(len_arr,))
                    out1[:len(self.analysis.lvl3hash)] = tmpout1

                    tmpout2 = np.array(list(map(str, self.analysis.lvl3hashframe)))
                    out2 = np.empty_like(tmpout2, shape=(len_arr,))
                    out2[:len(self.analysis.lvl3hashframe)] = tmpout2

                    tmpout3 = np.array(list(map(str, self.analysis.idx)))
                    out3 = np.empty_like(tmpout3, shape=(len_arr,))
                    out3[:len(self.analysis.idx)] = tmpout3

                # Column of index
                number = np.arange(1, len(out1) + 1)

                # Output
                out = np.vstack((number, out1, out2, out3)).T
                with open(name[0] + '.csv', 'w') as handle:
                    wr = csv.writer(handle, quoting=csv.QUOTE_MINIMAL)
                    wr.writerow(["number", "label_of_segment", "onset_index", "onset_index_pre_interpolation"])
                    wr.writerows(out)

    def export_coords(self):
        name = QtWidgets.QFileDialog.getSaveFileName(self, "Export coordinates",
                                                     self.openfile.file_path[:-4] + "_COORDS",
                                                     "CSV Files (*.csv)",
                                                     options=QtWidgets.QFileDialog.DontUseNativeDialog)

        if name[0] != '':
            with open(name[0], 'w') as handle:
                writer = csv.writer(handle, quoting=csv.QUOTE_NONE)
                writer.writerows(self.analysis.X)

    def jumpstart(self):
        if self.operating:
            self.current_pos = 0
            self.scroll_txt_le.setText("0")
            if self.processing_level == 1:
                self.m.updateplot(self.analysis.plot.updateplot_lvl1(self.current_pos))
                self.trajlabel.setText(self.analysis.lvl1hash[0][self.current_pos] +
                                       self.analysis.lvl1hash[1][self.current_pos] +
                                       self.analysis.lvl1hash[2][self.current_pos])
            elif self.processing_level == 2:
                self.m.updateplot(self.analysis.plot.updateplot_lvl2(self.current_pos))
                self.trajlabel.setText(self.analysis.lvl2hash[0][self.current_pos] +
                                       self.analysis.lvl2hash[1][self.current_pos] +
                                       self.analysis.lvl2hash[2][self.current_pos])
            elif self.processing_level == 3:
                self.m.updateplot(self.analysis.plot.updateplot_lvl3(self.current_pos))
                self.trajlabel.setText(self.analysis.lvl3hash[self.current_pos])

    def jumpend(self):
        if self.operating:
            if self.processing_level == 1:
                self.current_pos = len(self.analysis.lvl1hash[0]) - 2
                self.scroll_txt_le.setText(str(self.current_pos))
                self.m.updateplot(self.analysis.plot.updateplot_lvl1(self.current_pos))
                self.trajlabel.setText(self.analysis.lvl1hash[0][self.current_pos] +
                                       self.analysis.lvl1hash[1][self.current_pos] +
                                       self.analysis.lvl1hash[2][self.current_pos])
            elif self.processing_level == 2:
                self.current_pos = len(self.analysis.lvl2hash[0]) - 2
                self.scroll_txt_le.setText(str(self.current_pos))
                self.m.updateplot(self.analysis.plot.updateplot_lvl2(self.current_pos))
                self.trajlabel.setText(self.analysis.lvl2hash[0][self.current_pos] +
                                       self.analysis.lvl2hash[1][self.current_pos] +
                                       self.analysis.lvl2hash[2][self.current_pos])
            elif self.processing_level == 3:
                self.current_pos = len(self.analysis.lvl3hash) - 2
                self.scroll_txt_le.setText(str(self.current_pos))
                self.m.updateplot(self.analysis.plot.updateplot_lvl3(self.current_pos))
                self.trajlabel.setText(self.analysis.lvl3hash[self.current_pos])

    def lvl1switch(self):
        if self.processing_level != 1:
            self.processing_level = 1
            self.current_pos = 0
            self.scroll_txt_le.setText('0')
            self.m.initplot(self.analysis.plot.initplot_lvl1(), title='3D trajectory (Level 1)',
                            x_axis='X (Left/Right)', y_axis='Y (Forward/Backward)', z_axis='Z (Up/Down)',
                            invert_x=self.openfile.invert_x, invert_y=self.openfile.invert_y,
                            invert_z=self.openfile.invert_z)
            self.trajlabel.setText(self.analysis.lvl1hash[0][0] +
                                   self.analysis.lvl1hash[1][0] +
                                   self.analysis.lvl1hash[2][0])

    def lvl2switch(self):
        if self.processing_level != 2:
            self.processing_level = 2
            self.current_pos = 0
            self.scroll_txt_le.setText('0')
            self.m.initplot(self.analysis.plot.initplot_lvl2(), title='3D trajectory (Level 2)',
                            x_axis='X (Left/Right)', y_axis='Y (Forward/Backward)', z_axis='Z (Up/Down)',
                            invert_x=self.openfile.invert_x, invert_y=self.openfile.invert_y,
                            invert_z=self.openfile.invert_z)
            self.trajlabel.setText(self.analysis.lvl2hash[0][0] +
                                   self.analysis.lvl2hash[1][0] +
                                   self.analysis.lvl2hash[2][0])

    def lvl3switch(self):
        if self.processing_level != 3:
            self.processing_level = 3
            self.current_pos = 0
            self.scroll_txt_le.setText('0')
            self.m.initplot(self.analysis.plot.initplot_lvl3(), title='3D trajectory (Level 3)',
                            x_axis='X (Left/Right)', y_axis='Y (Forward/Backward)', z_axis='Z (Up/Down)',
                            invert_x=self.openfile.invert_x, invert_y=self.openfile.invert_y,
                            invert_z=self.openfile.invert_z)
            self.trajlabel.setText(self.analysis.lvl3hash[0])

    def trajectory(self):
        Animation(self.analysis.x, self.analysis.y, self.analysis.z,
                  self.openfile.invert_x, self.openfile.invert_y, self.openfile.invert_z,
                  dpi=self.settings.dpi)

    def open_settings(self):
        self.settings.change()
        if self.operating:
            if self.settings.rerun: self.rerun()
            # TODO: Update plot dpi from settings
            # if self.settings.plot_rerun: self.m.fig.set_dpi(self.settings.dpi)

    # Re-run analysis with new thresholds from settings
    def rerun(self):
        if self.operating:
            # Set new thresholds of analysis object
            self.analysis.x_threshold = self.settings.x_threshold
            self.analysis.y_threshold = 90 - self.settings.y_threshold
            self.analysis.z_threshold = 90 - self.settings.z_threshold
            self.analysis.main_direction_threshold = self.settings.main_direction_threshold

            # Re-run analysis
            self.analysis.rerun()

            # Reset plotting and labels
            self.processing_level = 1
            self.current_pos = 0
            self.scroll_txt_le.setText('0')
            self.m.initplot(self.analysis.plot.initplot_lvl1(), title='3D trajectory (Level 1)',
                            x_axis='X (Left/Right)', y_axis='Y (Forward/Backward)', z_axis='Z (Up/Down)',
                            invert_x=self.openfile.invert_x, invert_y=self.openfile.invert_y,
                            invert_z=self.openfile.invert_z)
            self.trajlabel.setText(self.analysis.lvl1hash[0][0] +
                                   self.analysis.lvl1hash[1][0] +
                                   self.analysis.lvl1hash[2][0])

    def about(self):
        QtWidgets.QMessageBox.about(self, "About {}".format(appname),
                                    "<b>{} (Version {})</b><br>"
                                    "First release on {}<br>"
                                    "Last update on {}".
                                    format(appname, version, release_date, update_date))

    # TODO: Beautify the dialog
    @staticmethod
    def howtouse():
        # Create text
        text = "Instructions\n" \
               "---------------------------------------------------------------------------------------------\n" \
               "1. Open a .csv file containing three columns (x, y, z coordinates)\n\n" \
               "2. The middle of the screen displays a line segment of the 3D trajectory\n" \
               "\ta) The blue line shows the current segment\n" \
               "\tb) The red dot shows the heading direction\n" \
               "\tc) The faint red line shows the previous segment\n\n" \
               "3. Below the 3D trajectory plot shows a label that describes the heading direction of the\n" \
               "\tcurrent line segment\n" \
               "\ta) If LEVEL-1/ LEVEL-2 PROCESSING is currently in display, three labels will be shown, each\n" \
               "\t\tdescribing the line heading direction on one of the dimensions:\n" \
               "\t\ti)   X-dimension: F = Forward, B = Backward, - = No Change\n" \
               "\t\tii)  Y-dimension: L = Left, R = Right, - = No Change\n" \
               "\t\tiii) Z-dimension: U = Up, D = Down, - = No Change\n" \
               "\tb) If LEVEL-3 PROCESSING is currently in display, one to three labels will be shown, each\n" \
               "\t\tdescribing the line heading direction on one of the dimensions (Uppercase letters show\n" \
               "\t\tthe main heading direction; Lowercase letters show a change in direction\n" \
               "\t\ti)   X-dimension: F/f = Forward, B/b = Backward\n" \
               "\t\tii)  Y-dimension: L/l = Left, R/r = Right\n" \
               "\t\tiii) Z-dimension: U/u = Up, D/d = Down\n\n" \
               "4. At the bottom right of the GUI, you may scroll to the previous/next line segment. You may also\n" \
               "\ttype the segment number manually into the text field\n\n" \
               "5. At the bottom left of the GUI, you may zoom in/out of the middle plot\n\n" \
               "6. If you wish to make amendments to the label predictions, click the change label button at the\n" \
               "\tbottom, this will create a pop-up dialog window that allows you to change the labels\n\n" \
               "7. Save the output pattern string as a .pkl/.mat/.csv file\n"

        # Create dialog
        d = QtWidgets.QDialog()
        d.setWindowTitle("Instructions")
        d.setWindowModality(QtCore.Qt.ApplicationModal)

        # Create layout to hold widget
        layout = QtWidgets.QVBoxLayout(d)

        # Create widget
        te = QtWidgets.QTextEdit()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(te.sizePolicy().hasHeightForWidth())
        te.setSizePolicy(sizePolicy)
        te.setReadOnly(True)
        te.setText(text)
        te.setTabStopDistance(QtGui.QFontMetricsF(te.font()).width(' ') * 5)

        font = te.document().defaultFont()
        fontMetrics = QtGui.QFontMetrics(font)
        textSize = fontMetrics.size(0, te.toPlainText())
        w = textSize.width() + 50
        h = textSize.height() + 50
        te.setMinimumSize(w, h)
        te.setMaximumSize(w, h)
        te.resize(w, h)

        layout.addWidget(te)

        d.exec_()

    # TODO: change zooming method
    # Action for zooming out
    def zoom_out(self):
        if self.operating:
            if self.zoom >= 0.2:
                self.m.axes.dist += 1
                self.zoom -= .1
                self.zoom_lbl.setText(str(round(self.zoom, 1)))
                if self.processing_level == 3:
                    self.m.updateplot(self.analysis.plot.updateplot_lvl3(self.current_pos))
                elif self.processing_level == 2:
                    self.m.updateplot(self.analysis.plot.updateplot_lvl2(self.current_pos))
                elif self.processing_level == 1:
                    self.m.updateplot(self.analysis.plot.updateplot_lvl1(self.current_pos))

    # Action for zooming in
    def zoom_in(self):
        if self.operating:
            if self.zoom <= 1.9:
                self.m.axes.dist -= 1
                self.zoom += .1
                self.zoom_lbl.setText(str(round(self.zoom, 1)))
                if self.processing_level == 3:
                    self.m.updateplot(self.analysis.plot.updateplot_lvl3(self.current_pos))
                elif self.processing_level == 2:
                    self.m.updateplot(self.analysis.plot.updateplot_lvl2(self.current_pos))
                elif self.processing_level == 1:
                    self.m.updateplot(self.analysis.plot.updateplot_lvl1(self.current_pos))

    # Action for scroll left
    def scroll_left(self):
        if self.operating:
            if self.current_pos > 0:
                self.current_pos -= 1
                self.scroll_txt_le.setText(str(self.current_pos))
                if self.processing_level == 1:
                    self.m.updateplot(self.analysis.plot.updateplot_lvl1(self.current_pos))
                    self.trajlabel.setText(self.analysis.lvl1hash[0][self.current_pos] +
                                           self.analysis.lvl1hash[1][self.current_pos] +
                                           self.analysis.lvl1hash[2][self.current_pos])
                elif self.processing_level == 2:
                    self.m.updateplot(self.analysis.plot.updateplot_lvl2(self.current_pos))
                    self.trajlabel.setText(self.analysis.lvl2hash[0][self.current_pos] +
                                           self.analysis.lvl2hash[1][self.current_pos] +
                                           self.analysis.lvl2hash[2][self.current_pos])
                elif self.processing_level == 3:
                    self.m.updateplot(self.analysis.plot.updateplot_lvl3(self.current_pos))
                    self.trajlabel.setText(self.analysis.lvl3hash[self.current_pos])

    # Action for scroll right
    def scroll_right(self):
        if self.operating:
            if self.processing_level == 1:
                if self.current_pos < len(self.analysis.lvl1hash[0]) - 2:
                    self.current_pos += 1
                    self.scroll_txt_le.setText(str(self.current_pos))
                    self.m.updateplot(self.analysis.plot.updateplot_lvl1(self.current_pos))
                    self.trajlabel.setText(self.analysis.lvl1hash[0][self.current_pos] +
                                           self.analysis.lvl1hash[1][self.current_pos] +
                                           self.analysis.lvl1hash[2][self.current_pos])
            elif self.processing_level == 2:
                if self.current_pos < len(self.analysis.lvl2hash[0]) - 2:
                    self.current_pos += 1
                    self.scroll_txt_le.setText(str(self.current_pos))
                    self.m.updateplot(self.analysis.plot.updateplot_lvl2(self.current_pos))
                    self.trajlabel.setText(self.analysis.lvl2hash[0][self.current_pos] +
                                           self.analysis.lvl2hash[1][self.current_pos] +
                                           self.analysis.lvl2hash[2][self.current_pos])
            elif self.processing_level == 3:
                if self.current_pos < len(self.analysis.lvl3hash) - 2:
                    self.current_pos += 1
                    self.scroll_txt_le.setText(str(self.current_pos))
                    self.m.updateplot(self.analysis.plot.updateplot_lvl3(self.current_pos))
                    self.trajlabel.setText(self.analysis.lvl3hash[self.current_pos])

    # Action for hitting enter on scroll line edit
    def scroll_enter(self):
        if self.operating:
            if self.scroll_txt_le.text() != "":
                if self.processing_level == 1:
                    if int(self.scroll_txt_le.text()) <= len(self.analysis.lvl1hash[0]) - 2:
                        self.current_pos = int(self.scroll_txt_le.text())
                        self.m.updateplot(self.analysis.plot.updateplot_lvl1(self.current_pos))
                        self.trajlabel.setText(self.analysis.lvl1hash[0][self.current_pos] +
                                               self.analysis.lvl1hash[1][self.current_pos] +
                                               self.analysis.lvl1hash[2][self.current_pos])
                elif self.processing_level == 2:
                    if int(self.scroll_txt_le.text()) <= len(self.analysis.lvl2hash[0]) - 2:
                        self.current_pos = int(self.scroll_txt_le.text())
                        self.m.updateplot(self.analysis.plot.updateplot_lvl2(self.current_pos))
                        self.trajlabel.setText(self.analysis.lvl2hash[0][self.current_pos] +
                                               self.analysis.lvl2hash[1][self.current_pos] +
                                               self.analysis.lvl2hash[2][self.current_pos])
                elif self.processing_level == 3:
                    if int(self.scroll_txt_le.text()) <= len(self.analysis.lvl3hash) - 2:
                        self.current_pos = int(self.scroll_txt_le.text())
                        self.m.updateplot(self.analysis.plot.updateplot_lvl3(self.current_pos))
                        self.trajlabel.setText(self.analysis.lvl3hash[self.current_pos])
                self.scroll_txt_le.clearFocus()

    # Action for detecting text change on scroll line edit (to prevent passing upper boundary)
    def scroll_textChange(self):
        if self.operating:
            if self.scroll_txt_le.text() != "":
                if self.processing_level == 1:
                    limit = len(self.analysis.lvl1hash[0]) - 2
                elif self.processing_level == 2:
                    limit = len(self.analysis.lvl2hash[0]) - 2
                elif self.processing_level == 3:
                    limit = len(self.analysis.lvl3hash) - 2

                if int(self.scroll_txt_le.text()) > limit:
                    self.scroll_left_btn.setDisabled(True)
                    self.scroll_right_btn.setDisabled(True)
                    self.scroll_txt_le.setText(self.scroll_txt_le.text()[:-1])
                elif int(self.scroll_txt_le.text()) == limit:
                    self.scroll_left_btn.setDisabled(False)
                    self.scroll_right_btn.setDisabled(True)
                elif int(self.scroll_txt_le.text()) == 0:
                    self.scroll_left_btn.setDisabled(True)
                    self.scroll_right_btn.setDisabled(False)
                else:
                    self.scroll_left_btn.setDisabled(False)
                    self.scroll_right_btn.setDisabled(False)

    # Logic for changing the labels
    def change_label(self):
        labelchange = LabelChange(self.current_pos, self.analysis, self.processing_level, self.trajlabel)

    # Detect focus out
    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.FocusOut and source is self.scroll_txt_le:
            self.scroll_txt_le.setText(str(self.current_pos))
        return super(App, self).eventFilter(source, event)


####################
# Open file dialog #
####################
class OpenFile:

    def __init__(self):

        # Initialize object variables
        self.valid = False
        self.file_path = ""
        self.file_path_ref1 = ""
        self.file_path_ref2 = ""
        self.header = None
        self.header_ref = None
        self.col_x = 1
        self.col_y = 2
        self.col_z = 3
        self.col_x_ref = 1
        self.col_y_ref = 2
        self.col_z_ref = 3
        self.build_ref_obj = False
        self.build_ref_radius1 = 0.001
        self.build_ref_radius2 = 0.001
        self.smooth = False
        self.smooth_order = 2
        self.smooth_window = 7
        self.interpolate = False
        self.interpolate_val = 0.5
        self.invert_x = False
        self.invert_y = False
        self.invert_z = False

    def showUI(self):
        # Set up dialog UI
        self.d = QtWidgets.QDialog()
        self.d.setWindowTitle("Open File")
        self.d.setGeometry(50, 50, 400, 250)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(self.d.sizePolicy().hasHeightForWidth())
        self.d.setSizePolicy(sizePolicy)
        self.d.setWindowModality(QtCore.Qt.ApplicationModal)

        # Set main layout of the dialog
        main_layout = QtWidgets.QVBoxLayout(self.d)

        # Create layouts inside main layout
        layout1 = QtWidgets.QGridLayout()
        main_layout.addLayout(layout1)

        # Initialize tabs
        self.fileinfo_tab = FileInfoWidget(self.header, self.col_x, self.col_y, self.col_z,
                                           self.invert_x, self.invert_y, self.invert_z)
        self.reference_tab = ReferenceWidget(self.header_ref, self.col_x_ref, self.col_y_ref, self.col_z_ref,
                                             self.build_ref_obj, self.build_ref_radius1, self.build_ref_radius2)
        self.preprocessing_tab = PreprocessingWidget(self.smooth, self.smooth_order, self.smooth_window,
                                                     self.interpolate, self.interpolate_val)

        # Tab widget
        tab_widget = QtWidgets.QTabWidget()
        tab_widget.addTab(self.fileinfo_tab, "File")
        tab_widget.addTab(self.reference_tab, "References (Optional)")
        tab_widget.addTab(self.preprocessing_tab, "Preprocessing")
        layout1.addWidget(tab_widget, 0, 0, 1, 2)

        self.fileinfo_tab.okbtn_status_change.connect(self.okbtn_status)

        # OK button
        self.ok_btn = QtWidgets.QPushButton("OK", self.d)
        self.ok_btn.setDefault(True)
        self.ok_btn.setDisabled(True)
        self.ok_btn.clicked.connect(partial(self.ok))
        layout1.addWidget(self.ok_btn)

        # Cancel button
        cancel_btn = QtWidgets.QPushButton("Cancel", self.d)
        cancel_btn.clicked.connect(self.d.close)
        layout1.addWidget(cancel_btn)

        self.d.exec_()

    def okbtn_status(self):
        if len(self.fileinfo_tab.file_le.text()) > 0:
            self.ok_btn.setDisabled(False)
        else:
            self.ok_btn.setDisabled(True)

    # TODO: file-breaking prevention (equal rows, data type)
    # TODO: header check
    # TODO: column selection check
    def checkerror(self):
        # Initialize error flag
        valid = True

        # Initialize error message
        error_string = ""

        # Error about smoothing
        if self.preprocessing_tab.smooth_cb.isChecked():
            # Check if smoothing polynomial order is smaller than window length
            if int(self.preprocessing_tab.smooth_order_sb.value()) >= int(
                    self.preprocessing_tab.smooth_window_sb.value()):
                valid = False
                error_string += "- Smoothing polynomial order must be smaller than window length <br>"

            # Check if smoothing window length is an odd number
            if int(self.preprocessing_tab.smooth_window_sb.value()) % 2 == 0:
                valid = False
                error_string += "- Smoothing window length must be an odd number <br>"

        return valid, error_string

    def ok(self):
        self.valid, error_string = self.checkerror()

        if self.valid:
            # Set files
            self.file_path = self.fileinfo_tab.file_le.text()
            self.file_path_ref1 = self.reference_tab.ref_file_le1.text()
            self.file_path_ref2 = self.reference_tab.ref_file_le2.text()

            # Get header
            self.header = int(self.fileinfo_tab.header_sb.text()) if self.fileinfo_tab.header_cb.isChecked() else None
            self.header_ref = int(
                self.reference_tab.ref_header_sb.text()) if self.reference_tab.ref_header_cb.isChecked() else None

            # Get column numbers
            self.col_x = int(self.fileinfo_tab.col_x_sb.value())
            self.col_y = int(self.fileinfo_tab.col_y_sb.value())
            self.col_z = int(self.fileinfo_tab.col_z_sb.value())
            self.col_x_ref = int(self.reference_tab.ref_col_x_sb.value())
            self.col_y_ref = int(self.reference_tab.ref_col_y_sb.value())
            self.col_z_ref = int(self.reference_tab.ref_col_z_sb.value())

            # Get build object parameters
            self.build_ref_obj = self.reference_tab.build_ref_cb.isChecked()
            self.build_ref_radius1 = self.reference_tab.build_ref_radius1_sb.value()
            self.build_ref_radius2 = self.reference_tab.build_ref_radius2_sb.value()

            # Check if the smoothing option is checked
            if self.preprocessing_tab.smooth_cb.isChecked():
                self.smooth = True
                self.smooth_order = int(self.preprocessing_tab.smooth_order_sb.value())
                self.smooth_window = int(self.preprocessing_tab.smooth_window_sb.value())
            else:
                self.smooth = False
                self.smooth_order = 2
                self.smooth_window = 7

            # Check if the interpolating option is checked
            if self.preprocessing_tab.interpolate_cb.isChecked():
                self.interpolate = True
                self.interpolate_val = float(self.preprocessing_tab.interpolate_sb.value())
            else:
                self.interpolate = False
                self.interpolate_val = 0.5

            # Check if axes need to be inverted
            self.invert_x = self.fileinfo_tab.x_cb.isChecked()
            self.invert_y = self.fileinfo_tab.y_cb.isChecked()
            self.invert_z = self.fileinfo_tab.z_cb.isChecked()

            # Close dialog
            self.d.close()
        else:
            error_string = "Please address the following issue(s):<br><br>" + error_string

            error_msg = QtWidgets.QErrorMessage(self.d)
            error_msg.setFixedSize(350, 250)
            error_msg.setWindowModality(QtCore.Qt.WindowModal)
            error_msg.setWindowTitle("Error")
            error_msg.showMessage(error_string)


class FileInfoWidget(QtWidgets.QWidget):
    # Signal for OK button status change
    okbtn_status_change = QtCore.pyqtSignal()

    def __init__(self, header, col_x, col_y, col_z, invert_x, invert_y, invert_z, parent=None):
        super(FileInfoWidget, self).__init__(parent)

        # Set reference variables
        self.header = header
        self.col_x = col_x
        self.col_y = col_y
        self.col_z = col_z
        self.invert_x = invert_x
        self.invert_y = invert_y
        self.invert_z = invert_z

        # Set main layout of the tab
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop)

        # Create layouts inside main layout
        layout1 = QtWidgets.QGridLayout()
        layout2 = QtWidgets.QGridLayout()
        layout3 = QtWidgets.QGridLayout()
        main_layout.addLayout(layout1)
        main_layout.addLayout(layout2)
        main_layout.addLayout(layout3)

        # Select files
        file_lbl = QtWidgets.QLabel("Select file to be opened:", self)
        layout1.addWidget(file_lbl, 0, 0, 1, 2)

        self.file_le = QtWidgets.QLineEdit("", self)
        self.file_le.textChanged.connect(partial(self.textchange))
        layout1.addWidget(self.file_le, 1, 0, 1, 1)

        file_btn = QtWidgets.QPushButton("...", self)
        file_btn.clicked.connect(partial(self.selectfile))
        layout1.addWidget(file_btn, 1, 1, 1, 1)

        # Select header and columns
        fo_lbl = QtWidgets.QLabel("File Options: (Index starts at 1)", self)
        layout2.addWidget(fo_lbl, 0, 0, 1, 6)

        self.header_cb = QtWidgets.QCheckBox("Header? ", self)
        self.header_cb.setChecked(False if self.header is None else True)
        self.header_cb.stateChanged.connect(partial(self.statechange))
        layout2.addWidget(self.header_cb, 1, 0, 1, 2)

        header_lbl = QtWidgets.QLabel("Row: ", self)
        layout2.addWidget(header_lbl, 1, 2, 1, 1)

        self.header_sb = QtWidgets.QSpinBox(self)
        self.header_sb.setValue(1 if self.header is None else self.header)
        self.header_sb.setDisabled(not self.header_cb.isChecked())
        self.header_sb.setRange(1, 999)
        layout2.addWidget(self.header_sb, 1, 3, 1, 1)

        col_x_lbl = QtWidgets.QLabel("X-axis (L/R): ", self)
        layout2.addWidget(col_x_lbl, 2, 0, 1, 1)

        self.col_x_sb = QtWidgets.QSpinBox(self)
        self.col_x_sb.setValue(self.col_x)
        self.col_x_sb.setRange(1, 999)
        layout2.addWidget(self.col_x_sb, 2, 1, 1, 1)

        col_y_lbl = QtWidgets.QLabel("Y-axis (F/B): ", self)
        layout2.addWidget(col_y_lbl, 2, 2, 1, 1)

        self.col_y_sb = QtWidgets.QSpinBox(self)
        self.col_y_sb.setValue(self.col_y)
        self.col_y_sb.setRange(1, 999)
        layout2.addWidget(self.col_y_sb, 2, 3, 1, 1)

        col_z_lbl = QtWidgets.QLabel("Z-axis (U/D): ", self)
        layout2.addWidget(col_z_lbl, 2, 4, 1, 1)

        self.col_z_sb = QtWidgets.QSpinBox(self)
        self.col_z_sb.setValue(self.col_z)
        self.col_z_sb.setRange(1, 999)
        layout2.addWidget(self.col_z_sb, 2, 5, 1, 1)

        # Separation line
        line1 = QtWidgets.QFrame(self)
        line1.setFrameShape(QtWidgets.QFrame.HLine)
        line1.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout2.addWidget(line1, 3, 0, 1, 6)

        # Invert axes options
        invert_lbl = QtWidgets.QLabel("Invert Axis Options:", self)
        layout3.addWidget(invert_lbl, 0, 0, 1, 3)

        self.x_cb = QtWidgets.QCheckBox("Invert X-axis", self)
        self.x_cb.setChecked(self.invert_x)
        layout3.addWidget(self.x_cb, 1, 0, 1, 1)

        self.y_cb = QtWidgets.QCheckBox("Invert Y-axis", self)
        self.y_cb.setChecked(self.invert_y)
        layout3.addWidget(self.y_cb, 1, 1, 1, 1)

        self.z_cb = QtWidgets.QCheckBox("Invert Z-axis", self)
        self.z_cb.setChecked(self.invert_z)
        layout3.addWidget(self.z_cb, 1, 2, 1, 1)

    def selectfile(self):
        file_path = QtWidgets.QFileDialog.getOpenFileName(None, "Select File",
                                                          filter="CSV Files (*.csv)",
                                                          options=QtWidgets.QFileDialog.DontUseNativeDialog)
        if file_path[0] != "":
            self.file_le.setText(file_path[0])

    def statechange(self):
        self.header_sb.setEnabled(not self.header_sb.isEnabled())

    def textchange(self):
        # Emit signal to change OK button status
        self.okbtn_status_change.emit()


class ReferenceWidget(QtWidgets.QWidget):

    def __init__(self, header_ref, col_x_ref, col_y_ref, col_z_ref,
                 build_ref_obj, build_ref_radius1, build_ref_radius2, parent=None):
        super(ReferenceWidget, self).__init__(parent)

        # Set reference variables
        self.header_ref = header_ref
        self.col_x_ref = col_x_ref
        self.col_y_ref = col_y_ref
        self.col_z_ref = col_z_ref
        self.build_ref_obj = build_ref_obj
        self.build_ref_radius1 = build_ref_radius1
        self.build_ref_radius2 = build_ref_radius2

        # Set main layout of the tab
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop)

        # Create layouts inside main layout
        layout1 = QtWidgets.QGridLayout()
        layout2 = QtWidgets.QGridLayout()
        layout3 = QtWidgets.QGridLayout()
        main_layout.addLayout(layout1)
        main_layout.addLayout(layout2)
        main_layout.addLayout(layout3)

        # Optional file
        ref_file_lbl = QtWidgets.QLabel("Select reference sensor file(s) to be opened (Optional):", self)
        layout1.addWidget(ref_file_lbl, 0, 0, 1, 2)

        self.ref_file_le1 = QtWidgets.QLineEdit("", self)
        self.ref_file_le1.textChanged.connect(partial(self.textchange))
        layout1.addWidget(self.ref_file_le1, 1, 0, 1, 1)

        self.ref_file_btn1 = QtWidgets.QPushButton("...", self)
        self.ref_file_btn1.setObjectName("1")
        self.ref_file_btn1.clicked.connect(partial(self.selectfile, self.ref_file_btn1.objectName()))
        layout1.addWidget(self.ref_file_btn1, 1, 1, 1, 1)

        self.ref_file_le2 = QtWidgets.QLineEdit("", self)
        self.ref_file_le2.setDisabled(True)
        self.ref_file_le2.textChanged.connect(partial(self.textchange))
        layout1.addWidget(self.ref_file_le2, 2, 0, 1, 1)

        self.ref_file_btn2 = QtWidgets.QPushButton("...", self)
        self.ref_file_btn2.setObjectName("2")
        self.ref_file_btn2.setDisabled(True)
        self.ref_file_btn2.clicked.connect(partial(self.selectfile, self.ref_file_btn2.objectName()))
        layout1.addWidget(self.ref_file_btn2, 2, 1, 1, 1)

        # Select header and columns
        ref_fo_lbl = QtWidgets.QLabel("File Options: (Index starts at 1)", self)
        layout2.addWidget(ref_fo_lbl, 0, 0, 1, 6)

        self.ref_header_cb = QtWidgets.QCheckBox("Header? ", self)
        self.ref_header_cb.setObjectName('1')
        self.ref_header_cb.setChecked(False if self.header_ref is None else True)
        self.ref_header_cb.setDisabled(True)
        self.ref_header_cb.stateChanged.connect(partial(self.statechange, self.ref_header_cb.objectName()))
        layout2.addWidget(self.ref_header_cb, 1, 0, 1, 2)

        ref_header_lbl = QtWidgets.QLabel("Row: ", self)
        layout2.addWidget(ref_header_lbl, 1, 2, 1, 1)

        self.ref_header_sb = QtWidgets.QSpinBox(self)
        self.ref_header_sb.setValue(1 if self.header_ref is None else self.header_ref)
        self.ref_header_sb.setDisabled(True)
        self.ref_header_sb.setRange(1, 999)
        layout2.addWidget(self.ref_header_sb, 1, 3, 1, 1)

        ref_col_x_lbl = QtWidgets.QLabel("X-axis (L/R): ", self)
        layout2.addWidget(ref_col_x_lbl, 2, 0, 1, 1)

        self.ref_col_x_sb = QtWidgets.QSpinBox(self)
        self.ref_col_x_sb.setValue(self.col_x_ref)
        self.ref_col_x_sb.setDisabled(True)
        self.ref_col_x_sb.setRange(1, 999)
        layout2.addWidget(self.ref_col_x_sb, 2, 1, 1, 1)

        ref_col_y_lbl = QtWidgets.QLabel("Y-axis (F/B): ", self)
        layout2.addWidget(ref_col_y_lbl, 2, 2, 1, 1)

        self.ref_col_y_sb = QtWidgets.QSpinBox(self)
        self.ref_col_y_sb.setValue(self.col_y_ref)
        self.ref_col_y_sb.setDisabled(True)
        self.ref_col_y_sb.setRange(1, 999)
        layout2.addWidget(self.ref_col_y_sb, 2, 3, 1, 1)

        ref_col_z_lbl = QtWidgets.QLabel("Z-axis (U/D): ", self)
        layout2.addWidget(ref_col_z_lbl, 2, 4, 1, 1)

        self.ref_col_z_sb = QtWidgets.QSpinBox(self)
        self.ref_col_z_sb.setValue(self.col_z_ref)
        self.ref_col_z_sb.setDisabled(True)
        self.ref_col_z_sb.setRange(1, 999)
        layout2.addWidget(self.ref_col_z_sb, 2, 5, 1, 1)

        # Separation line
        line1 = QtWidgets.QFrame(self)
        line1.setFrameShape(QtWidgets.QFrame.HLine)
        line1.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout2.addWidget(line1, 3, 0, 1, 6)

        # Build reference object
        self.build_ref_cb = QtWidgets.QCheckBox("Build reference object? (Unit depends on coordinates unit)", self)
        self.build_ref_cb.setDisabled(True)
        self.build_ref_cb.setObjectName('2')
        self.build_ref_cb.setChecked(self.build_ref_obj)
        self.build_ref_cb.stateChanged.connect(partial(self.statechange, self.build_ref_cb.objectName()))
        layout3.addWidget(self.build_ref_cb, 0, 0, 1, 2)

        build_ref_lbl1 = QtWidgets.QLabel("Radius of top file's reference: ", self)
        layout3.addWidget(build_ref_lbl1, 1, 0, 1, 1)

        self.build_ref_radius1_sb = QtWidgets.QDoubleSpinBox(self)
        self.build_ref_radius1_sb.setDisabled(True)
        self.build_ref_radius1_sb.setValue(self.build_ref_radius1)
        self.build_ref_radius1_sb.setDecimals(3)
        self.build_ref_radius1_sb.setRange(0.001, 99999.999)
        self.build_ref_radius1_sb.setSingleStep(0.001)
        layout3.addWidget(self.build_ref_radius1_sb, 1, 1, 1, 1)

        build_ref_lbl2 = QtWidgets.QLabel("Radius of bottom file's reference: ", self)
        layout3.addWidget(build_ref_lbl2, 2, 0, 1, 1)

        self.build_ref_radius2_sb = QtWidgets.QDoubleSpinBox(self)
        self.build_ref_radius2_sb.setDisabled(True)
        self.build_ref_radius2_sb.setValue(self.build_ref_radius2)
        self.build_ref_radius2_sb.setDecimals(3)
        self.build_ref_radius2_sb.setRange(0.001, 99999.999)
        self.build_ref_radius2_sb.setSingleStep(0.001)
        layout3.addWidget(self.build_ref_radius2_sb, 2, 1, 1, 1)

    def selectfile(self, le):
        file_path = QtWidgets.QFileDialog.getOpenFileName(None, "Select File",
                                                          filter="CSV Files (*.csv)",
                                                          options=QtWidgets.QFileDialog.DontUseNativeDialog)
        if le == '1':
            if file_path[0] != "":
                self.ref_file_le1.setText(file_path[0])
        if le == '2':
            if file_path[0] != "":
                self.ref_file_le2.setText(file_path[0])

    def statechange(self, cb_no):
        if cb_no == '1':
            self.ref_header_sb.setEnabled(not self.ref_header_sb.isEnabled())
        elif cb_no == '2':
            self.build_ref_radius1_sb.setEnabled(self.build_ref_cb.isChecked())
            self.build_ref_radius2_sb.setEnabled(self.build_ref_cb.isChecked())

    def textchange(self):
        # Set if the options for reference file input should be available
        if len(self.ref_file_le1.text()) > 0:
            self.ref_file_le2.setDisabled(False)
            self.ref_file_btn2.setDisabled(False)
            self.ref_header_cb.setDisabled(False)
            self.ref_header_sb.setDisabled(not self.ref_header_cb.isChecked())
            self.ref_col_x_sb.setDisabled(False)
            self.ref_col_y_sb.setDisabled(False)
            self.ref_col_z_sb.setDisabled(False)
        else:
            self.ref_file_le2.setDisabled(True)
            self.ref_file_btn2.setDisabled(True)
            self.ref_header_cb.setDisabled(True)
            self.ref_header_sb.setDisabled(True)
            self.ref_col_x_sb.setDisabled(True)
            self.ref_col_y_sb.setDisabled(True)
            self.ref_col_z_sb.setDisabled(True)

        # Set if build reference object should be available
        if len(self.ref_file_le1.text()) > 0 and len(self.ref_file_le2.text()) > 0:
            self.build_ref_cb.setDisabled(False)
            self.build_ref_radius1_sb.setDisabled(not self.build_ref_cb.isChecked())
            self.build_ref_radius2_sb.setDisabled(not self.build_ref_cb.isChecked())
        else:
            self.build_ref_cb.setDisabled(True)
            self.build_ref_radius1_sb.setDisabled(True)
            self.build_ref_radius2_sb.setDisabled(True)


class PreprocessingWidget(QtWidgets.QWidget):

    def __init__(self, smooth, smooth_order, smooth_window, interpolate, interpolate_val, parent=None):
        super(PreprocessingWidget, self).__init__(parent)

        # Set reference variables
        self.smooth = smooth
        self.smooth_order = smooth_order
        self.smooth_window = smooth_window
        self.interpolate = interpolate
        self.interpolate_val = interpolate_val

        # Set main layout of the tab
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop)

        # Create layouts inside main layout
        layout1 = QtWidgets.QGridLayout()
        main_layout.addLayout(layout1)

        # Preprocessing options
        self.smooth_cb = QtWidgets.QCheckBox("Smooth", self)
        self.smooth_cb.setObjectName('1')
        self.smooth_cb.setChecked(self.smooth)
        self.smooth_cb.toggled.connect(partial(self.statechange, self.smooth_cb.objectName()))
        layout1.addWidget(self.smooth_cb, 0, 0, 1, 4)

        smooth_order_lbl = QtWidgets.QLabel("Polynomial Order:", self)
        layout1.addWidget(smooth_order_lbl, 1, 0, 1, 1)

        self.smooth_order_sb = QtWidgets.QSpinBox(self)
        self.smooth_order_sb.setValue(self.smooth_order)
        self.smooth_order_sb.setDisabled(not self.smooth)
        self.smooth_order_sb.setRange(1, 99)
        layout1.addWidget(self.smooth_order_sb, 1, 1, 1, 1)

        smooth_window_lbl = QtWidgets.QLabel("Window Length:", self)
        layout1.addWidget(smooth_window_lbl, 1, 2, 1, 1)

        self.smooth_window_sb = QtWidgets.QSpinBox(self)
        self.smooth_window_sb.setValue(self.smooth_window)
        self.smooth_window_sb.setDisabled(not self.smooth)
        self.smooth_window_sb.setRange(1, 99999)
        layout1.addWidget(self.smooth_window_sb, 1, 3, 1, 1)

        self.interpolate_cb = QtWidgets.QCheckBox("Interpolate", self)
        self.interpolate_cb.setObjectName('2')
        self.interpolate_cb.setChecked(self.interpolate)
        self.interpolate_cb.toggled.connect(partial(self.statechange, self.interpolate_cb.objectName()))
        layout1.addWidget(self.interpolate_cb, 2, 0, 1, 4)

        self.interpolate_sb = QtWidgets.QDoubleSpinBox(self)
        self.interpolate_sb.setValue(self.interpolate_val)
        self.interpolate_sb.setDecimals(3)
        self.interpolate_sb.setRange(0.001, 99999.999)
        self.interpolate_sb.setSingleStep(0.001)
        self.interpolate_sb.setDisabled(not self.interpolate)
        layout1.addWidget(self.interpolate_sb, 3, 0, 1, 1)

        interpolate_lbl = QtWidgets.QLabel("(Unit depends on coordinates unit)", self)
        layout1.addWidget(interpolate_lbl, 3, 1, 1, 3)

    def statechange(self, cb_no):
        if cb_no == '1':
            self.smooth_order_sb.setEnabled(not self.smooth_order_sb.isEnabled())
            self.smooth_window_sb.setEnabled(not self.smooth_window_sb.isEnabled())
        elif cb_no == '2':
            self.interpolate_sb.setEnabled(not self.interpolate_sb.isEnabled())


#######################
# Change label dialog #
#######################
class LabelChange(QtWidgets.QDialog):

    def __init__(self, pos, analysis, processing_level, trajlabel):
        super(LabelChange, self).__init__()

        # Assign object attributes
        self.pos = pos
        self.analysis = analysis
        self.processing_level = processing_level
        self.trajlabel = trajlabel

        # Initialize dialog box
        self.setWindowTitle("Change Labels")
        self.setGeometry(10, 10, 300, 250)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # Create main layout
        main_layout = QtWidgets.QVBoxLayout(self)

        # Initialize widgets for each dimension
        x_layout = QtWidgets.QGridLayout()
        main_layout.addLayout(x_layout)
        y_layout = QtWidgets.QGridLayout()
        main_layout.addLayout(y_layout)
        z_layout = QtWidgets.QGridLayout()
        main_layout.addLayout(z_layout)
        button_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(button_layout)

        # XYZ dimension labels
        X_label = QtWidgets.QLabel("X-axis:", self)
        x_layout.addWidget(X_label, 0, 0, 1, 3)
        Y_label = QtWidgets.QLabel("Y-axis:", self)
        y_layout.addWidget(Y_label, 0, 0, 1, 3)
        Z_label = QtWidgets.QLabel("Z-axis:", self)
        z_layout.addWidget(Z_label, 0, 0, 1, 3)

        # Level-1 and level-2
        if self.processing_level in [1, 2]:
            # Get the labels and current position
            if self.processing_level == 1:
                labels = [self.analysis.lvl1hash[0][self.pos], self.analysis.lvl1hash[1][self.pos],
                          self.analysis.lvl1hash[2][self.pos]]
            else:
                labels = [self.analysis.lvl2hash[0][self.pos], self.analysis.lvl2hash[1][self.pos],
                          self.analysis.lvl2hash[2][self.pos]]

            # X-dimension radio buttons
            X_buttongroup = QtWidgets.QButtonGroup()
            self.L_rb = QtWidgets.QRadioButton('L', self)
            X_buttongroup.addButton(self.L_rb)
            x_layout.addWidget(self.L_rb, 1, 0, 1, 1)
            self.R_rb = QtWidgets.QRadioButton('R', self)
            X_buttongroup.addButton(self.R_rb)
            x_layout.addWidget(self.R_rb, 1, 1, 1, 1)
            self.nx_rb = QtWidgets.QRadioButton('-', self)
            X_buttongroup.addButton(self.nx_rb)
            x_layout.addWidget(self.nx_rb, 1, 2, 1, 1)

            if self.L_rb.text() in labels[0]:
                self.L_rb.setChecked(True)
            elif self.R_rb.text() in labels[0]:
                self.R_rb.setChecked(True)
            elif self.nx_rb.text() in labels[0]:
                self.nx_rb.setChecked(True)

            # Y-dimension radio buttons
            Y_buttongroup = QtWidgets.QButtonGroup()
            self.F_rb = QtWidgets.QRadioButton('F', self)
            Y_buttongroup.addButton(self.F_rb)
            y_layout.addWidget(self.F_rb, 1, 0, 1, 1)
            self.B_rb = QtWidgets.QRadioButton('B', self)
            Y_buttongroup.addButton(self.B_rb)
            y_layout.addWidget(self.B_rb, 1, 1, 1, 1)
            self.ny_rb = QtWidgets.QRadioButton('-', self)
            Y_buttongroup.addButton(self.ny_rb)
            y_layout.addWidget(self.ny_rb, 1, 2, 1, 1)

            if self.F_rb.text() in labels[1]:
                self.F_rb.setChecked(True)
            elif self.B_rb.text() in labels[1]:
                self.B_rb.setChecked(True)
            elif self.ny_rb.text() in labels[1]:
                self.ny_rb.setChecked(True)

            # Z-dimension radio buttons
            Z_buttongroup = QtWidgets.QButtonGroup()
            self.U_rb = QtWidgets.QRadioButton('U', self)
            Z_buttongroup.addButton(self.U_rb)
            z_layout.addWidget(self.U_rb, 1, 0, 1, 1)
            self.D_rb = QtWidgets.QRadioButton('D', self)
            Z_buttongroup.addButton(self.D_rb)
            z_layout.addWidget(self.D_rb, 1, 1, 1, 1)
            self.nz_rb = QtWidgets.QRadioButton('-', self)
            Z_buttongroup.addButton(self.nz_rb)
            z_layout.addWidget(self.nz_rb, 1, 2, 1, 1)

            if self.U_rb.text() in labels[2]:
                self.U_rb.setChecked(True)
            elif self.D_rb.text() in labels[2]:
                self.D_rb.setChecked(True)
            elif self.nz_rb.text() in labels[2]:
                self.nz_rb.setChecked(True)
        # Level-3
        else:
            # Get label at current position
            labels = self.analysis.lvl3hash[self.pos]

            # X-dimension radio buttons
            self.L_rb = QtWidgets.QCheckBox('L', self)
            x_layout.addWidget(self.L_rb, 1, 0, 1, 1)
            self.R_rb = QtWidgets.QCheckBox('R', self)
            x_layout.addWidget(self.R_rb, 1, 1, 1, 1)
            self.l_rb = QtWidgets.QCheckBox('l', self)
            x_layout.addWidget(self.l_rb, 1, 2, 1, 1)
            self.r_rb = QtWidgets.QCheckBox('r', self)
            x_layout.addWidget(self.r_rb, 1, 3, 1, 1)

            if self.L_rb.text() in labels:
                self.L_rb.setChecked(True)
            elif self.R_rb.text() in labels:
                self.R_rb.setChecked(True)
            elif self.l_rb.text() in labels:
                self.l_rb.setChecked(True)
            elif self.r_rb.text() in labels:
                self.r_rb.setChecked(True)

            # Y-dimension radio buttons
            self.F_rb = QtWidgets.QCheckBox('F', self)
            y_layout.addWidget(self.F_rb, 1, 0, 1, 1)
            self.B_rb = QtWidgets.QCheckBox('B', self)
            y_layout.addWidget(self.B_rb, 1, 1, 1, 1)
            self.f_rb = QtWidgets.QCheckBox('f', self)
            y_layout.addWidget(self.f_rb, 1, 2, 1, 1)
            self.b_rb = QtWidgets.QCheckBox('b', self)
            y_layout.addWidget(self.b_rb, 1, 3, 1, 1)

            if self.F_rb.text() in labels:
                self.F_rb.setChecked(True)
            elif self.B_rb.text() in labels:
                self.B_rb.setChecked(True)
            elif self.f_rb.text() in labels:
                self.f_rb.setChecked(True)
            elif self.b_rb.text() in labels:
                self.b_rb.setChecked(True)

            # Z-dimension radio buttons
            self.U_rb = QtWidgets.QCheckBox('U', self)
            z_layout.addWidget(self.U_rb, 1, 0, 1, 1)
            self.D_rb = QtWidgets.QCheckBox('D', self)
            z_layout.addWidget(self.D_rb, 1, 1, 1, 1)
            self.u_rb = QtWidgets.QCheckBox('u', self)
            z_layout.addWidget(self.u_rb, 1, 2, 1, 1)
            self.d_rb = QtWidgets.QCheckBox('d', self)
            z_layout.addWidget(self.d_rb, 1, 3, 1, 1)

            if self.U_rb.text() in labels:
                self.U_rb.setChecked(True)
            elif self.D_rb.text() in labels:
                self.D_rb.setChecked(True)
            elif self.u_rb.text() in labels:
                self.u_rb.setChecked(True)
            elif self.d_rb.text() in labels:
                self.d_rb.setChecked(True)

        # Create separation line for each dimension
        line1 = QtWidgets.QFrame()
        line1.setFrameShape(QtWidgets.QFrame.HLine)
        line1.setFrameShadow(QtWidgets.QFrame.Sunken)
        x_layout.addWidget(line1, 2, 0, 1, x_layout.columnCount())
        line2 = QtWidgets.QFrame()
        line2.setFrameShape(QtWidgets.QFrame.HLine)
        line2.setFrameShadow(QtWidgets.QFrame.Sunken)
        y_layout.addWidget(line2, 2, 0, 1, x_layout.columnCount())
        line3 = QtWidgets.QFrame()
        line3.setFrameShape(QtWidgets.QFrame.HLine)
        line3.setFrameShadow(QtWidgets.QFrame.Sunken)
        z_layout.addWidget(line3, 2, 0, 1, x_layout.columnCount())

        # OK button and cancel button
        okbtn = QtWidgets.QPushButton("OK", self)
        okbtn.setDefault(True)
        okbtn.clicked.connect(self.change_label)
        button_layout.addWidget(okbtn)

        cancelbtn = QtWidgets.QPushButton("Cancel", self)
        cancelbtn.clicked.connect(self.close)
        button_layout.addWidget(cancelbtn)

        self.exec_()

    def change_label(self):
        # Change analysis level 1/2 hash according to the buttons selected
        if self.processing_level in [1, 2]:
            if self.processing_level == 1:
                hash = self.analysis.lvl1hash
            else:
                hash = self.analysis.lvl2hash

            if self.L_rb.isChecked():
                hash[1] = hash[1][:self.pos] + self.L_rb.text() + hash[1][self.pos + 1:]
            elif self.R_rb.isChecked():
                hash[1] = hash[1][:self.pos] + self.R_rb.text() + hash[1][self.pos + 1:]
            elif self.ny_rb.isChecked():
                hash[1] = hash[1][:self.pos] + self.ny_rb.text() + hash[1][self.pos + 1:]

            if self.F_rb.isChecked():
                hash[0] = hash[0][:self.pos] + self.F_rb.text() + hash[0][self.pos + 1:]
            elif self.B_rb.isChecked():
                hash[0] = hash[0][:self.pos] + self.B_rb.text() + hash[0][self.pos + 1:]
            elif self.nx_rb.isChecked():
                hash[0] = hash[0][:self.pos] + self.nx_rb.text() + hash[0][self.pos + 1:]

            if self.U_rb.isChecked():
                hash[2] = hash[2][:self.pos] + self.U_rb.text() + hash[2][self.pos + 1:]
            elif self.D_rb.isChecked():
                hash[2] = hash[2][:self.pos] + self.D_rb.text() + hash[2][self.pos + 1:]
            elif self.nz_rb.isChecked():
                hash[2] = hash[2][:self.pos] + self.nz_rb.text() + hash[2][self.pos + 1:]

            if self.processing_level == 1:
                self.analysis.lvl1hash = hash
                self.trajlabel.setText(self.analysis.lvl1hash[0][self.pos] +
                                       self.analysis.lvl1hash[1][self.pos] +
                                       self.analysis.lvl1hash[2][self.pos])
            else:
                self.analysis.lvl2hash = hash
                self.trajlabel.setText(self.analysis.lvl2hash[0][self.pos] +
                                       self.analysis.lvl2hash[1][self.pos] +
                                       self.analysis.lvl2hash[2][self.pos])
        # Change analysis level 3 hash according to the buttons selected
        else:
            hash = ''

            if self.L_rb.isChecked():
                hash += self.L_rb.text()
            if self.R_rb.isChecked():
                hash += self.R_rb.text()
            if self.l_rb.isChecked():
                hash += self.l_rb.text()
            if self.r_rb.isChecked():
                hash += self.r_rb.text()

            if self.F_rb.isChecked():
                hash += self.F_rb.text()
            if self.B_rb.isChecked():
                hash += self.B_rb.text()
            if self.f_rb.isChecked():
                hash += self.f_rb.text()
            if self.b_rb.isChecked():
                hash += self.b_rb.text()

            if self.U_rb.isChecked():
                hash += self.U_rb.text()
            if self.D_rb.isChecked():
                hash += self.D_rb.text()
            if self.u_rb.isChecked():
                hash += self.u_rb.text()
            if self.d_rb.isChecked():
                hash += self.d_rb.text()

            self.analysis.lvl3hash[self.pos] = hash
            self.trajlabel.setText(self.analysis.lvl3hash[self.pos])

        self.close()


##################################
# Settings parameters and dialog #
##################################
class Settings:

    def __init__(self):
        # Find settings.config file
        # Load if found, create file with default parameters if missing
        try:
            with open(os.path.join(script_dir, "config/settings.config"), 'r') as f:
                for line in f.readlines():
                    try:
                        exec(line)
                    except Exception:
                        pass
        except FileNotFoundError:
            default_text = "# DO NOT CHANGE THE CONTENT OF THIS FILE UNLESS YOU KNOW WHAT YOU ARE DOING!!!\n" \
                           "# IF ERROR OCCURS BECAUSE OF THIS FILE, SIMPLY DELETE THIS FILE THEN RUN THE APPLICATION TO RESET TO DEFAULT SETTINGS\n\n" \
                           "# Analysis settings parameters\n" \
                           "self.x_threshold = 60.0\n" \
                           "self.y_threshold = 60.0\n" \
                           "self.z_threshold = 60.0\n" \
                           "self.main_direction_threshold = 5\n\n" \
                           "# Plot settings parameters\n" \
                           "self.dpi = 60"
            with open(os.path.join(script_dir, "config/settings.config"), 'w') as f:
                f.writelines(default_text)
            self.x_threshold = 60.0
            self.y_threshold = 60.0
            self.z_threshold = 60.0
            self.main_direction_threshold = 5
            self.dpi = 60

    def change(self):
        # Initialize variable
        self.rerun = False

        # Initialize dialog box
        self.d = QtWidgets.QDialog()
        self.d.setWindowTitle("Settings")
        self.d.setGeometry(100, 100, 400, 200)
        self.d.setWindowModality(QtCore.Qt.ApplicationModal)

        # Initialize tabs
        self.analysistab = AnalysisSettingsWidget(self.x_threshold, self.y_threshold, self.z_threshold,
                                                  self.main_direction_threshold)
        self.plottab = PlotSettingsWidget(self.dpi)

        # Tab widget
        tab_widget = QtWidgets.QTabWidget()
        tab_widget.addTab(self.analysistab, "Analysis")
        tab_widget.addTab(self.plottab, "Plot (WIP)")

        # Set dialog layout
        layout = QtWidgets.QGridLayout(self.d)
        layout.addWidget(tab_widget, 0, 0, 1, 2)

        # Create buttons to submit or cancel
        self.okbtn = QtWidgets.QPushButton("OK", self.d)
        self.okbtn.setDefault(True)
        self.okbtn.clicked.connect(self.ok)
        layout.addWidget(self.okbtn, 1, 0, 1, 1)

        cancelbtn = QtWidgets.QPushButton("Cancel", self.d)
        cancelbtn.clicked.connect(self.d.close)
        layout.addWidget(cancelbtn, 1, 1, 1, 1)

        self.d.exec_()

    def ok(self):
        any_change = False

        # Check if inputs are valid
        if len(self.analysistab.xturn_le.text()) > 0 and len(self.analysistab.yturn_le.text()) > 0 and \
                len(self.analysistab.zturn_le.text()) > 0 and len(self.analysistab.md_le.text()) > 0 and \
                len(self.plottab.dpi_le.text()) > 0 and \
                float(self.analysistab.xturn_le.text()) <= 90 and float(self.analysistab.yturn_le.text()) <= 90 and \
                float(self.analysistab.zturn_le.text()) <= 90:

            # Check if thresholds have changed
            if self.x_threshold == float(self.analysistab.xturn_le.text()) and \
                    self.y_threshold == float(self.analysistab.yturn_le.text()) and \
                    self.z_threshold == float(self.analysistab.zturn_le.text()) and \
                    self.main_direction_threshold == int(self.analysistab.md_le.text()):
                self.rerun = False
            else:
                any_change = True
                self.x_threshold = float(self.analysistab.xturn_le.text())
                self.y_threshold = float(self.analysistab.yturn_le.text())
                self.z_threshold = float(self.analysistab.zturn_le.text())
                self.main_direction_threshold = int(self.analysistab.md_le.text())
                reply = QtWidgets.QMessageBox.question(self.d, "Re-run Analysis?",
                                                       "Do you wish to re-run the analysis with new thresholds?<br>"
                                                       "(Warning: ALL CHANGES WILL BE LOST!)",
                                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                       QtWidgets.QMessageBox.No)
                self.rerun = True if reply == QtWidgets.QMessageBox.Yes else False

            # Check if plot settings have changed
            if self.dpi == int(self.plottab.dpi_le.text()):
                self.plot_rerun = False
            else:
                any_change = True
                self.dpi = int(self.plottab.dpi_le.text())
                self.plot_rerun = True

            # Rewrite settings.config
            if any_change:
                new_settings = "# DO NOT CHANGE THE CONTENT OF THIS FILE UNLESS YOU KNOW WHAT YOU ARE DOING!!!\n" \
                               "# IF ERROR OCCURS BECAUSE OF THIS FILE, SIMPLY DELETE THIS FILE THEN RUN THE APPLICATION TO RESET TO DEFAULT SETTINGS\n\n" \
                               "# Analysis settings parameters\n" \
                               "self.x_threshold = {}\n" \
                               "self.y_threshold = {}\n" \
                               "self.z_threshold = {}\n" \
                               "self.main_direction_threshold = {}\n\n" \
                               "# Plot settings parameters\n" \
                               "self.dpi = {}".format(self.x_threshold, self.y_threshold, self.z_threshold,
                                                      self.main_direction_threshold, self.dpi)
                with open(os.path.join(script_dir, "config/settings.config"), 'w') as f:
                    f.writelines(new_settings)

            self.d.close()
        else:
            error_dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, "Error", "The settings are invalid.")
            error_dialog.exec_()


class AnalysisSettingsWidget(QtWidgets.QWidget):

    def __init__(self, x_threshold, y_threshold, z_threshold, main_direction_threshold, parent=None):
        super(AnalysisSettingsWidget, self).__init__(parent)
        layout = QtWidgets.QGridLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)

        # Create class attributes
        self.x_threshold = x_threshold
        self.y_threshold = y_threshold
        self.z_threshold = z_threshold
        self.main_direction_threshold = main_direction_threshold

        # Create labels and line-edit for entries
        xturn_lbl = QtWidgets.QLabel("X-axis (L/R) threshold (degrees):<br>"
                                     "(Default: 60) (0 to 90)", self)
        layout.addWidget(xturn_lbl, 1, 1, 1, 1)

        self.xturn_le = QtWidgets.QLineEdit(str(self.x_threshold), self)
        self.xturn_le.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("^([1-9]\d*|0)(\.\d+)$")))
        layout.addWidget(self.xturn_le, 1, 2, 1, 1)

        yturn_lbl = QtWidgets.QLabel("Y-axis (F/B) threshold (degrees):<br>"
                                     "(Default: 60) (0 to 90)", self)
        layout.addWidget(yturn_lbl, 2, 1, 1, 1)

        self.yturn_le = QtWidgets.QLineEdit(str(self.y_threshold), self)
        self.yturn_le.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("^([1-9]\d*|0)(\.\d+)$")))
        layout.addWidget(self.yturn_le, 2, 2, 1, 1)

        zturn_lbl = QtWidgets.QLabel("Z-axis (U/D) threshold (degrees):<br>"
                                     "(Default: 60) (0 to 90)", self)
        layout.addWidget(zturn_lbl, 3, 1, 1, 1)

        self.zturn_le = QtWidgets.QLineEdit(str(self.z_threshold), self)
        self.zturn_le.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("^([1-9]\d*|0)(\.\d+)$")))
        layout.addWidget(self.zturn_le, 3, 2, 1, 1)

        md_lbl = QtWidgets.QLabel("Main direction threshold (data points):<br>"
                                  "(Default: 5)", self)
        layout.addWidget(md_lbl, 4, 1, 1, 1)

        self.md_le = QtWidgets.QLineEdit(str(self.main_direction_threshold), self)
        self.md_le.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("^[1-9]\d*$")))
        layout.addWidget(self.md_le, 4, 2, 1, 1)


class PlotSettingsWidget(QtWidgets.QWidget):

    def __init__(self, dpi, parent=None):
        super(PlotSettingsWidget, self).__init__(parent)
        layout = QtWidgets.QGridLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)

        # Create class attributes
        self.dpi = dpi

        # Create labels and line-edit for entries
        dpi_lbl = QtWidgets.QLabel("Plot DPI:\n(Default: 60)", self)
        layout.addWidget(dpi_lbl, 1, 1, 1, 1)

        self.dpi_le = QtWidgets.QLineEdit(str(self.dpi), self)
        self.dpi_le.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("^[1-9]\d*$")))
        layout.addWidget(self.dpi_le, 1, 2, 1, 1)


########
# Main #
########
if __name__ == "__main__":
    global script_dir
    script_dir = os.path.dirname(os.path.realpath(__file__))

    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    ui = App()
    sys.exit(app.exec_())
