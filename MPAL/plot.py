import numpy as np
from PyQt5 import QtWidgets, QtCore
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D, proj3d
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib
matplotlib.use('Qt5Agg')


##################
# Plotting class #
##################
class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=3, height=2, dpi=60):
        self.fig = plt.figure(figsize=(width, height), dpi=dpi)
        super(FigureCanvas, self).__init__(self.fig)
        self.axes = self.fig.add_subplot(111, projection='3d')
        self.axes.set_aspect("equal")
        self.box = self.fig.gca(projection='3d')
        self.box.set_aspect("equal")

        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.draw()

    # Initialize plots of first node
    def initplot(self, plot, title='', x_axis='', y_axis='', z_axis='', invert_x=False, invert_y=False, invert_z=False):
        # Clear all plots
        self.clearplot()

        # Initialize plot title and axes
        self.title = title
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.z_axis = z_axis
        self.invert_x = invert_x
        self.invert_y = invert_y
        self.invert_z = invert_z
        if self.invert_x: self.axes.invert_xaxis()
        if self.invert_y: self.axes.invert_yaxis()
        if self.invert_z: self.axes.invert_zaxis()

        self.axes.set_aspect("equal")
        self.axes.set_title(self.title)
        # self.axes.set_title("[Distance: {}CM]".format(dist), loc="right")
        self.axes.set_xlabel(self.x_axis)
        self.axes.set_ylabel(self.y_axis)
        self.axes.set_zlabel(self.z_axis)
        self.box.set_aspect("equal")

        # Get the max and min of all data for bounding box set-up
        max_min = plot[1]

        # Create 3D bounding box to simulate equal aspect ratio
        ranges = np.array([max_min[0] - max_min[1], max_min[2] - max_min[3], max_min[4] - max_min[5]])
        max_range = ranges.max()
        Xb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][0].flatten() + 0.5 * (max_min[0] + max_min[1])
        Yb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (max_min[2] + max_min[3])
        Zb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (max_min[4] + max_min[5])
        for xb, yb, zb in zip(Xb, Yb, Zb):
            self.box.plot([xb], [yb], [zb], 'w')
        self.axes.grid(True)

        # Draw plots and point
        self.axes.plot(plot[0][0], plot[0][1], plot[0][2], 'b', linewidth=2)
        self.axes.scatter(plot[0][0][-1], plot[0][1][-1], plot[0][2][-1], c='r',
                          marker="o", s=(Xb.max() + Yb.max() + Zb.max()) / 7, alpha=.4)

        self.draw()

    # Update plots
    def updateplot(self, plot):
        # Clear all plots
        self.clearplot()

        # Set up the axes and title
        self.axes.set_aspect("equal")
        self.axes.set_title(self.title)
        # self.axes.set_title("[Distance: {}CM]".format(dist), loc="right")
        self.axes.set_xlabel(self.x_axis)
        self.axes.set_ylabel(self.y_axis)
        self.axes.set_zlabel(self.z_axis)
        if self.invert_x: self.axes.invert_xaxis()
        if self.invert_y: self.axes.invert_yaxis()
        if self.invert_z: self.axes.invert_zaxis()
        self.box.set_aspect("equal")

        # Get the max and min of all data for bounding box set-up
        max_min = plot[2]

        # Create 3D bounding box to simulate equal aspect ratio
        ranges = np.array([max_min[0] - max_min[1], max_min[2] - max_min[3], max_min[4] - max_min[5]])
        max_range = ranges.max()
        Xb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][0].flatten() + 0.5 * (max_min[0] + max_min[1])
        Yb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (max_min[2] + max_min[3])
        Zb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (max_min[4] + max_min[5])
        for xb, yb, zb in zip(Xb, Yb, Zb):
            self.box.plot([xb], [yb], [zb], 'w')
        self.axes.grid(True)

        # Draw plots and point
        self.axes.plot(plot[0][0], plot[0][1], plot[0][2], 'b', linewidth=2)
        self.axes.scatter(plot[0][0][-1], plot[0][1][-1], plot[0][2][-1], c='r',
                          marker="o", s=(Xb.max() + Yb.max() + Zb.max()) / 7, alpha=.4)
        if plot[1] is not None:
            self.axes.plot(plot[1][0], plot[1][1], plot[1][2], 'r', alpha=.2)

        self.draw()

    # Clear all plots
    def clearplot(self):
        self.axes.clear()
        self.box.clear()
        self.draw()


######################
# Animation plotting #
######################
class Animation(QtWidgets.QDialog):

    def __init__(self, x, y, z, invert_x=False, invert_y=False, invert_z=False, dpi=60):
        super().__init__()

        # Create attributes
        self.x = x
        self.y = y
        self.z = z
        self.invert_x = invert_x
        self.invert_y = invert_y
        self.invert_z = invert_z

        # Dialog window settings
        self.setWindowTitle("Showing Trajectory...")
        self.move(300, 10)
        self.setFixedSize(600, 600)
        self.setWindowModality(QtCore.Qt.NonModal)

        # Create figure elements
        self.fig = plt.figure(figsize=(3, 2), dpi=dpi)

        self.canvas = FigureCanvas(self.fig)
        FigureCanvas.setSizePolicy(self.canvas, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self.canvas)

        # Set layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Call animate function
        self.animate()
        self.canvas.draw()

        # Display dialog
        self.exec_()

    # Main function for animation plotting
    def animate(self):

        # Frame update function
        def update_line(num, data, line):
            line_start = max((num - 100, 0))
            dot_start = max((num - 1, 0))
            scat._offsets3d = (data[0, dot_start:num], data[1, dot_start:num], data[2, dot_start:num])
            line.set_data(data[:2, line_start:num])
            line.set_3d_properties(data[2, line_start:num])
            self.ax.set_title("3D animated trajectory (Frame={})".format(num))

        self.ax = self.fig.gca(projection='3d')
        self.ax.set_aspect("equal")
        self.ax.set_xlabel('X (Left/Right)')
        self.ax.set_ylabel('Y (Forward/Backward)')
        self.ax.set_zlabel('Z (Up/Down)')
        if self.invert_x: self.ax.invert_xaxis()
        if self.invert_y: self.ax.invert_yaxis()
        if self.invert_z: self.ax.invert_zaxis()

        # Create 3D bounding box to simulate equal aspect ratio
        max_range = np.array([self.x.max() - self.x.min(), self.y.max() - self.y.min(),
                              self.z.max() - self.z.min()]).max()
        Xb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][0].flatten() + 0.5 * (self.x.max() + self.x.min())
        Yb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (self.y.max() + self.y.min())
        Zb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][2].flatten() + 0.5 * (self.z.max() + self.z.min())
        for xb, yb, zb in zip(Xb, Yb, Zb):
            self.ax.plot([xb], [yb], [zb], 'w')
        self.ax.grid(True)

        data = np.array(list(zip(self.x, self.y, self.z))).T
        line, = self.ax.plot(data[0, 0:1], data[1, 0:1], data[2, 0:1])
        scat = self.ax.scatter(data[0, 0], data[1, 0], data[2, 0], c='#771F1F')

        self.ani = FuncAnimation(self.fig, update_line, len(self.x), fargs=(data, line), interval=0,
                                 blit=False, repeat=True)
