import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import QtCore, QtWidgets, Qt
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtCore import pyqtSlot

import sys
import argparse


base_name = "frame_"
frame_counter = 0
mytime = 1

def connect(data, dest):
    dest.SetInputData(data)


def plug(outlet, inlet):
    inlet.SetInputConnection(outlet.GetOutputPort())


def AddRGBPoint(colorFunction, pt, r, g, b):
    colorFunction.AddRGBPoint(pt, r/255., g/255., b/255.)


def compose_file_name(base_dir, folder, filename, time):
    if time < 10:
        time = "0" + str(time)
    else:
        time = str(time)
    return base_dir + folder+ filename + time + ".vti"


seeds = [([1424.823838268583, 919.2205197256492, 0], [1889.3742429686026, 2023.894373394899, 16.5360950179])]

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("QVTKRenderWindowInteractor")
        MainWindow.setWindowTitle('Illustration of Interactive Isosurfacing')
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.gridlayout = QtWidgets.QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)
        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 1, 12)

        self.velocityB = QtWidgets.QCheckBox()
        self.cloudB = QtWidgets.QCheckBox()
        self.precipB = QtWidgets.QCheckBox()
        self.pressureB = QtWidgets.QCheckBox()
        self.groundB = QtWidgets.QCheckBox()
        self.redraw = QtWidgets.QPushButton()
        self.timeB = QtWidgets.QSpinBox()
        self.timeB.setRange(1, 48)
        # self.timeSlider = QtWidgets.QSlider()

        self.gridlayout.addWidget(QtWidgets.QLabel("Velocity"), 1, 1)
        self.gridlayout.addWidget(self.velocityB, 2, 1)
        self.gridlayout.addWidget(QtWidgets.QLabel("Cloud"), 1, 2)
        self.gridlayout.addWidget(self.cloudB, 2, 2)
        self.gridlayout.addWidget(QtWidgets.QLabel("Pressure"), 1, 3)
        self.gridlayout.addWidget(self.pressureB, 2, 3)
        self.gridlayout.addWidget(QtWidgets.QLabel("Precipitation"), 1, 4)
        self.gridlayout.addWidget(self.precipB, 2, 4)
        self.gridlayout.addWidget(QtWidgets.QLabel("Ground"), 1, 5)
        self.gridlayout.addWidget(self.groundB, 2, 5)
        self.gridlayout.addWidget(QtWidgets.QLabel("Time"), 1, 6)
        self.gridlayout.addWidget(self.timeB, 2, 6)
        self.gridlayout.addWidget(QtWidgets.QLabel("Redraw"), 1, 7)
        self.gridlayout.addWidget(self.redraw, 2, 7)



        MainWindow.setCentralWidget(self.centralWidget)


class Master(QtWidgets.QMainWindow):

    def __init__(self, parent=None):

        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # initialize window display by loading cloud, velocity, temp, pressure
        self.ren = vtk.vtkRenderer()
        self.ren.GradientBackgroundOn()  # Set gradient for background
        self.ren.SetBackground(0.75, 0.75, 0.75)  # Set background to silver
        self.ren.ResetCamera()
        self.time_step = mytime
        self.precip_volume = None
        self.cloud_volume = None
        self.velocity_actor = None
        self.P_volume = None
        self.ground_actor = None

        self.config = {
            "velocity": [True, self.render_velocity],
            "PRECIP": [False, self.render_precip],
            "P": [False, self.render_p],
            "CLOUD": [False, self.render_cloud],
            "GROUND": [True, self.render_ground]
        }
        self.base_dir = './isabel'

        self.data_folders = {
            "velocity" : "/velocity_",
            "PRECIP" : "/PRECIP_",
            "P" : "/P_",
            "CLOUD" : "/CLOUD_",
            "GROUND": "/Satellite.png"
        }

        for item in self.config:
            should_render, render = self.config[item]
            render()

        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        self.iren.AddObserver("KeyPressEvent", self.key_pressed_callback)

    def draw(self):
        for item in self.config:
            should_render, render = self.config[item]
            render()
        self.ui.vtkWidget.GetRenderWindow().Render()

    def time_callback(self, value):
        self.time_step = value

    def callback_generator(self, value_to_change):
        def callback(value):
            if value:
                self.config[value_to_change][0] = True
            else:
                self.config[value_to_change][0] = False
            print(self.config[value_to_change])
        return callback

    def redraw_callback(self):
        self.draw()

    def save_frame(self):
        global frame_counter
        # ---------------------------------------------------------------
        # Save current contents of render window to PNG file
        # ---------------------------------------------------------------
        file_name = str("./output/") + str(self.time_step).zfill(5) + ".png"
        image = vtk.vtkWindowToImageFilter()
        image.SetInput(self.ui.vtkWidget.GetRenderWindow())
        png_writer = vtk.vtkPNGWriter()
        png_writer.SetInputConnection(image.GetOutputPort())
        png_writer.SetFileName(file_name)
        self.ui.vtkWidget.GetRenderWindow().Render()
        png_writer.Write()
        frame_counter += 1
        print(file_name, " has been successfully exported")

    def write_camera_settings(self):
        # ---------------------------------------------------------------
        # Print out the current settings of the camera
        # ---------------------------------------------------------------
        camera = self.ren.GetActiveCamera()
        print("Camera settings:")
        print("  * position:        %s" % (camera.GetPosition(),))
        print("  * focal point:     %s" % (camera.GetFocalPoint(),))
        print("  * up vector:       %s" % (camera.GetViewUp(),))

        with open("camera_setting.conf", "w") as f:
            f.write(str(camera.GetPosition())[1:-1])
            f.write("\n")
            f.write(str(camera.GetFocalPoint())[1:-1])
            f.write("\n")
            f.write(str(camera.GetViewUp())[1:-1])
            f.write("\n")

    def load_camera_settings(self):
        # ---------------------------------------------------------------
        # Print out the current settings of the camera
        # ---------------------------------------------------------------
        camera = self.ren.GetActiveCamera()
        with open("camera_setting.conf", "r") as f:
            specs = f.readlines()
            camera.SetPosition(list(map(float, specs[0].split(","))))
            camera.SetFocalPoint(list(map(float, specs[1].split(","))))
            camera.SetViewUp(list(map(float, specs[2].split(","))))

    def key_pressed_callback(self, obj, event):
        # ---------------------------------------------------------------
        # Attach actions to specific keys
        # ---------------------------------------------------------------
        key = obj.GetKeySym()
        if key == "p":
            self.save_frame()
        elif key == "s":
            self.write_camera_settings()
        elif key == "l":
            self.load_camera_settings()
        elif key == "q":
            print("User requested exit.")
            sys.exit()
        self.ui.vtkWidget.GetRenderWindow().Render()

    def render_ground(self):
        self.ren.RemoveActor(self.ground_actor)
        if not self.config["GROUND"][0]:
            return
        ## Read the image
        png_reader = vtk.vtkPNGReader()
        png_reader.SetFileName(self.base_dir+self.data_folders["GROUND"])
        png_reader.Update()

        plane = vtk.vtkPlaneSource()
        plane.SetXResolution(500)
        plane.SetYResolution(500)
        plane.SetOrigin(0, 0, 0)
        plane.SetPoint1(1921, 0, 0)
        plane.SetPoint2(0, 2003.98, 0)

        atext = vtk.vtkTexture()
        atext.SetInputConnection(png_reader.GetOutputPort())
        atext.InterpolateOn()

        texturePlane = vtk.vtkTextureMapToPlane()
        texturePlane.SetInputConnection(plane.GetOutputPort())

        planeMapper = vtk.vtkPolyDataMapper()
        planeMapper.SetInputConnection(texturePlane.GetOutputPort())


        ## Position the primitives
        actor = vtk.vtkActor()
        actor.SetMapper(planeMapper)
        actor.SetTexture(atext)
        self.ground_actor = actor
        self.ren.AddActor(actor)

    def render_velocity(self):
        self.ren.RemoveActor(self.velocity_actor)
        if not self.config["velocity"][0]:
            return
        data_path = compose_file_name(self.base_dir, "/velocity", self.data_folders["velocity"], self.time_step)
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(data_path)
        reader.Update()

        rake = vtk.vtkLineSource()
        cur_seeds = seeds[self.time_step-1]
        rake.SetPoint1(cur_seeds[0][0], cur_seeds[0][1], cur_seeds[0][2])
        rake.SetPoint2(cur_seeds[1][0], cur_seeds[1][1], cur_seeds[1][2])
        rake.SetResolution(1000)

        integ = vtk.vtkRungeKutta45()
        sl = vtk.vtkStreamTracer()
        sl.SetInputData(reader.GetOutput())
        sl.SetSourceConnection(rake.GetOutputPort())
        sl.SetIntegrator(integ)
        sl.SetMaximumPropagation(10000)
        sl.SetInitialIntegrationStep(10)
        sl.SetIntegrationDirectionToBoth()

        transform = vtk.vtkTransform()
        transform.Scale(1, 1, 30)
        transform.Update()

        transform_filter = vtk.vtkTransformFilter()
        transform_filter.SetInputConnection(sl.GetOutputPort())
        transform_filter.SetTransform(transform)
        transform_filter.Update()

        # the filter generates (only when multiple lines are input).
        streamTube = vtk.vtkTubeFilter()
        streamTube.SetInputConnection(transform_filter.GetOutputPort())
        streamTube.SetInputArrayToProcess(1, 0, 0, vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS, "vectors")
        streamTube.SetRadius(2)
        streamTube.SetNumberOfSides(12)
        streamTube.SetVaryRadiusToVaryRadiusByVector()

        # streamTube.GetOutput().GetPointData().SetActiveScalars("Vorticity")
        # myrange = reader.GetOutput().GetPointData().GetScalars().GetRange()
        #
        # color = vtk.vtkColorTransferFunction()
        # color.AddRGBPoint(myrange[0], 0., 0., 1)
        # color.AddRGBPoint(myrange[1], 1., 0., 0)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(streamTube.GetOutputPort())
        # mapper.SetScalarRange(reader.GetOutput().GetPointData().GetScalars().GetRange())
        # mapper.SetLookupTable(color)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetOpacity(0.3)
        self.velocity_actor = actor
        self.ren.AddActor(actor)

    def render_precip(self):
        self.ren.RemoveVolume(self.precip_volume)
        if not self.config["PRECIP"][0]:
            return
        data_path = compose_file_name(self.base_dir, "/PRECIP", self.data_folders["PRECIP"], self.time_step)
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(data_path)
        reader.Update()

        spacing = reader.GetOutput().GetSpacing()
        reader.GetOutput().SetSpacing(spacing[0], spacing[1], spacing[2] * 30)
        myrange = reader.GetOutput().GetPointData().GetScalars().GetRange()

        opacityTransferFunction = vtk.vtkPiecewiseFunction()
        opacityTransferFunction.AddPoint(myrange[0], 0.0)
        opacityTransferFunction.AddPoint(myrange[1], 0.1)

        color = vtk.vtkColorTransferFunction()
        # Blue
        color.AddRGBPoint(myrange[0], 0.8, 0.8, 0.8)
        color.AddRGBPoint((myrange[0] + myrange[1]) / 2, 1., 1., 1)
        color.AddRGBPoint(myrange[1], 0.8, 0.8, 0.8)

        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.SetColor(color)
        volumeProperty.SetScalarOpacity(opacityTransferFunction)
        volumeProperty.SetInterpolationTypeToLinear()
        volumeProperty.ShadeOff()

        volumeMapper = vtk.vtkSmartVolumeMapper()
        volumeMapper.SetBlendModeToComposite()
        volumeMapper.SetAutoAdjustSampleDistances(0)
        volumeMapper.SetSampleDistance(0.5)
        volumeMapper.SetInputConnection(reader.GetOutputPort())

        # The volume holds the mapper and the property and
        # can be used to position/orient the volume
        volume = vtk.vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)
        self.precip_volume = volume
        self.ren.AddVolume(volume)

    def render_p(self):
        self.ren.RemoveVolume(self.P_volume)
        if not self.config["P"][0]:
            return
        # input: file containing all data for P.vti
        # output: actor for current timestep
        data_path = compose_file_name(self.base_dir, "/P", self.data_folders["P"], self.time_step)
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(data_path)
        reader.Update()

        spacing = reader.GetOutput().GetSpacing()
        reader.GetOutput().SetSpacing(spacing[0], spacing[1], spacing[2] * 30)
        myrange = reader.GetOutput().GetPointData().GetScalars().GetRange()

        opacityTransferFunction = vtk.vtkPiecewiseFunction()
        opacityTransferFunction.AddPoint(-3781, 0.3)
        opacityTransferFunction.AddPoint(-3097, 0.3)
        opacityTransferFunction.AddPoint(-2488, 0)
        opacityTransferFunction.AddPoint(-1334, 0)
        opacityTransferFunction.AddPoint(-661, 0.001)
        opacityTransferFunction.AddPoint(-354, 0)
        opacityTransferFunction.AddPoint(787, 0.0021)
        opacityTransferFunction.AddPoint(1225, 0.0062)
        opacityTransferFunction.AddPoint(2010, 0.1)
        opacityTransferFunction.AddPoint(2329, 0.1)

        color = vtk.vtkColorTransferFunction()
        # Blue
        color.AddRGBPoint(myrange[0], 0., 1., 0)
        color.AddRGBPoint((myrange[0] + myrange[1]) / 2, 1., 1., 0)
        color.AddRGBPoint(myrange[1], 1., 0., 0.)

        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.SetColor(color)
        volumeProperty.SetScalarOpacity(opacityTransferFunction)
        volumeProperty.SetInterpolationTypeToLinear()
        volumeProperty.ShadeOff()

        volumeMapper = vtk.vtkSmartVolumeMapper()
        volumeMapper.SetBlendModeToComposite()
        volumeMapper.SetAutoAdjustSampleDistances(0)
        volumeMapper.SetSampleDistance(0.5)
        volumeMapper.SetInputConnection(reader.GetOutputPort())

        # The volume holds the mapper and the property and
        # can be used to position/orient the volume
        volume = vtk.vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)
        self.P_volume = volume
        self.ren.AddVolume(volume)

    def render_cloud(self):
        self.ren.RemoveVolume(self.cloud_volume)
        if not self.config["CLOUD"][0]:
            return
        data_path = compose_file_name(self.base_dir, "/CLOUD", self.data_folders["CLOUD"], self.time_step)
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(data_path)
        reader.Update()

        spacing = reader.GetOutput().GetSpacing()
        reader.GetOutput().SetSpacing(spacing[0], spacing[1], spacing[2]*30)
        myrange = reader.GetOutput().GetPointData().GetScalars().GetRange()

        opacityTransferFunction = vtk.vtkPiecewiseFunction()
        opacityTransferFunction.AddPoint(myrange[0], 0.0)
        opacityTransferFunction.AddPoint(myrange[1], 0.1)

        color = vtk.vtkColorTransferFunction()
        # Blue
        color.AddRGBPoint(myrange[0], 0.8, 0.8, 0.8)
        color.AddRGBPoint((myrange[0] + myrange[1]) / 2, 1., 1., 1)
        color.AddRGBPoint(myrange[1], 0.8, 0.8, 0.8)

        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.SetColor(color)
        volumeProperty.SetScalarOpacity(opacityTransferFunction)
        volumeProperty.SetInterpolationTypeToLinear()
        volumeProperty.ShadeOff()

        volumeMapper = vtk.vtkSmartVolumeMapper()
        volumeMapper.SetBlendModeToComposite()
        volumeMapper.SetAutoAdjustSampleDistances(0)
        volumeMapper.SetSampleDistance(0.5)
        volumeMapper.SetInputConnection(reader.GetOutputPort())

        # The volume holds the mapper and the property and
        # can be used to position/orient the volume
        volume = vtk.vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)
        self.cloud_volume = volume
        self.ren.AddVolume(volume)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Visulizaing hurricane isabel <vfem.vtu> <wing.vtk>')
    parser.add_argument('-t', '--time',  type=int, help='1->48')
    parser.add_argument('-v', '--video', help='True or False')
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    if args.time:
        mytime = args.time

    window = Master()
    window.show()
    window.setWindowState(QtCore.Qt.WindowMaximized)  # Maximize the window
    window.load_camera_settings()
    window.ren.ResetCamera()

    if args.video:
        window.save_frame()
        sys.exit()
    else:
        window.iren.Initialize()  # Need this line to actually show

        if window.config["velocity"][0]:
            window.ui.velocityB.toggle()
        if window.config["PRECIP"][0]:
            window.ui.precipB.toggle()
        if window.config["P"][0]:
            window.ui.pressureB.toggle()
        if window.config["CLOUD"][0]:
            window.ui.cloudB.toggle()
        if window.config["GROUND"][0]:
            window.ui.groundB.toggle()

        window.ui.velocityB.stateChanged.connect(window.callback_generator("velocity"))
        window.ui.precipB.stateChanged.connect(window.callback_generator("PRECIP"))
        window.ui.pressureB.stateChanged.connect(window.callback_generator("P"))
        window.ui.cloudB.stateChanged.connect(window.callback_generator("CLOUD"))
        window.ui.groundB.stateChanged.connect(window.callback_generator("GROUND"))
        window.ui.timeB.valueChanged.connect(window.time_callback)

        window.ui.redraw.clicked.connect(window.redraw_callback)

        sys.exit(app.exec_())




