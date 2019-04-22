import vtk
import render_data as createActor
import argparse
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import Qt, QtCore, QtWidgets
import sys


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


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("QVTKRenderWindowInteractor")
        MainWindow.setWindowTitle('Illustration of Interactive Isosurfacing')
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.gridlayout = QtWidgets.QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)
        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 1, 5)
        # play button widget

        # stop button widget

        # add/remove cloud button

        # add/remove temperature button

        # add/remove pressure button

        # add/remove velocity button

        # add/remove precipitation button

        # add/remove snow button
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
        self.time_step = 1
        self.config = {
            "velocity": [True, self.render_velocity],
            "TCF": [False, self.render_tcf],
            "QSNOWf": [False, self.render_qsnowf],
            "PRECIP": [False, self.render_precip],
            "P": [False, self.render_p],
            "CLOUD": [False, self.render_cloud]
        }
        self.base_dir = './isabel'
        self.data_folders = {
            "velocity" : "/velocity_",
            "TCF" : "/TCF",
            "QSNOWf" : "/QSNOWf",
            "PRECIP" : "/PRECIP_",
            "P" : "/P_",
            "CLOUD" : "/CLOUD_"
        }

        for item in self.config:
            should_render, render = self.config[item]
            if should_render:
                render()

        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

    def render_velocity(self):
        data_path = compose_file_name(self.base_dir, "/velocity", self.data_folders["velocity"], self.time_step)
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(data_path)
        reader.Update()

        # transform_filter.GetOutput().GetPointData().SetActiveVectors("velocity")

        # plane1 = vtk.vtkPlane()
        # plane1.SetNormal(0., 0., 1.)
        # plane1.Push(1)
        #
        # cutEdges = vtk.vtkCutter()
        # cutEdges.SetInputConnection(reader.GetOutputPort())
        # cutEdges.SetCutFunction(plane1)
        #
        # probFilter = vtk.vtkProbeFilter()
        # probFilter.SetSourceData(reader.GetOutput())
        # plug(cutEdges, probFilter)
        # probFilter.PassPointArraysOn()
        # probFilter.Update()
        #
        # extract = vtk.vtkMaskPoints()
        # extract.SetInputConnection(probFilter.GetOutputPort())
        # extract.RandomModeOn()
        # extract.SetOnRatio(20)
        #
        # arrow = vtk.vtkArrowSource()
        #
        # glyph = vtk.vtkGlyph3D()
        # plug(extract, glyph)
        # glyph.SetSourceConnection(arrow.GetOutputPort())
        # glyph.SetVectorModeToUseVector()
        # glyph.SetScaleFactor(0.0000008)
        # glyph.GetOutput().GetPointData().SetActiveScalars("velocity")

        rake = vtk.vtkLineSource()
        rake.SetPoint1(1424.823838268583, 919.2205197256492, 0)
        rake.SetPoint2(1889.3742429686026, 2023.894373394899, 16.5360950179)
        rake.SetResolution(1000)

        rakeMapper = vtk.vtkPolyDataMapper()
        rakeMapper.SetInputConnection(rake.GetOutputPort())
        rakeActor = vtk.vtkActor()
        rakeActor.SetMapper(rakeMapper)

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

        streamTube.GetOutput().GetPointData().SetActiveScalars("Vorticity")



        # myrange = transform_filter.GetOutput().GetPointData().GetScalars().GetRange()

        color = vtk.vtkColorTransferFunction()
        color.AddRGBPoint(0.41, 0., 0., 1)
        color.AddRGBPoint(47, 1., 0., 0)
        # color.AddRGBPoint(40, 1., 0., 0)
        # color.AddRGBPoint(50, 1., 1., 0)
        # color.AddRGBPoint(60, 0., 1., 0)
        # color.AddRGBPoint(99, 0., 1., 0.)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(streamTube.GetOutputPort())
        # mapper.SetScalarRange(reader.GetOutput().GetPointData().GetScalars().GetRange())
        mapper.SetLookupTable(color)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        # actor.GetProperty().SetOpacity(0.4)
        self.ren.AddActor(rakeActor)
        self.ren.AddActor(actor)

    def render_tcf(self):
        data_path = compose_file_name(self.base_dir, "/TCF", self.data_folders["TCF"], self.time_step)
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(data_path)
        reader.Update()

        transform = vtk.vtkTransform()
        transform.Scale(1, 1, 30)

        transform_filter = vtk.vtkTransformFilter()
        transform_filter.SetInputConnection(reader.GetOutputPort())
        transform_filter.SetTransform(transform)

        temp_range = transform_filter.GetOutput().GetPointData().GetScalars().GetRange()
        tempfunction = vtk.vtkColorTransferFunction()
        tempfunction.AddRGBPoint(temp_range[0], 1, 0, 0)
        tempfunction.AddRGBPoint(temp_range[1], 0, 0, 1)

        tempMapper = vtk.vtkDataSetMapper()
        tempMapper.SetInputData(transform_filter.GetOutput())
        # tempMapper.SetLookupTable(tempfunction)

        tempActor = vtk.vtkActor()
        tempActor.SetMapper(tempMapper)

        # ScalarBar = vtk.vtkScalarBarActor()
        # # ScalarBar.SetLookupTable(tempfunction)
        # ScalarBar.SetTitle("Temperature")
        # ScalarBar.SetNumberOfLabels(4)
        # ScalarBar.SetOrientationToHorizontal()
        # ScalarBar.SetWidth(.8)
        # ScalarBar.SetHeight(0.08)
        # ScalarBar.SetPosition(0.1, 0.05)

        self.ren.AddActor(tempActor)
        # self.ren.AddActor(ScalarBar)

    def render_qsnowf(self):
        pass

    def render_precip(self):
        pass

    def render_p(self):
        # input: file containing all data for P.vti
        # output: actor for current timestep
        data_path = compose_file_name(self.base_dir, "/P", self.data_folders["P"], self.time_step)
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(data_path)
        reader.Update()
        print(reader.GetOutput().GetDimensions())

        transform = vtk.vtkTransform()
        transform.Scale(1, 1, 30)
        transform.Update()

        transform_filter = vtk.vtkTransformFilter()
        transform_filter.SetInputConnection(reader.GetOutputPort())
        transform_filter.SetTransform(transform)
        transform_filter.Update()
        #
        # pressure_range = transform.GetOutput().GetPointData().GetScalars().GetRange()
        # pressurefunction = vtk.vtkColorTransferFunction()
        # pressurefunction.AddRGBPoint(pressure_range[0], 1, 0, 0)
        # pressurefunction.AddRGBPoint(pressure_range[1], 0, 0, 1)

        pressureMapper = vtk.vtkDataSetMapper()
        pressureMapper.SetInputData(transform_filter.GetOutput())
        # pressureMapper.SetLookupTable(pressurefunction)

        pressureActor = vtk.vtkActor()
        pressureActor.SetMapper(pressureMapper)
        pressureActor.GetProperty().SetOpacity(0.3)

        ScalarBar = vtk.vtkScalarBarActor()
        # ScalarBar.SetLookupTable(pressurefunction)
        ScalarBar.SetTitle("Pressure")
        ScalarBar.SetNumberOfLabels(4)
        ScalarBar.SetOrientationToHorizontal()
        ScalarBar.SetWidth(.8)
        ScalarBar.SetHeight(0.08)
        ScalarBar.SetPosition(0.1, 0.05)
        # pressureMapper.SetLookupTable(pressurefunction)

        # ScalarBarActor = vtk.vtkActor2D()

        self.ren.AddActor(pressureActor)
        # self.ren.AddActor(ScalarBar)

    def render_cloud(self):
        data_path = compose_file_name(self.base_dir, "/CLOUD", self.data_folders["CLOUD"], self.time_step)
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(data_path)
        reader.Update()

        spacing = reader.GetOutput().GetSpacing()
        reader.GetOutput().SetSpacing(spacing[0], spacing[1], spacing[2]*30)
        range = reader.GetOutput().GetPointData().GetScalars().GetRange()

        opacityTransferFunction = vtk.vtkPiecewiseFunction()
        opacityTransferFunction.AddPoint(range[0], 0.0)
        opacityTransferFunction.AddPoint(range[1], 0.1)

        color = vtk.vtkColorTransferFunction()
        # Blue
        color.AddRGBPoint(range[0], 1., 1., 1)
        color.AddRGBPoint((range[0] + range[1]) / 2, 1., 1., 1)
        color.AddRGBPoint(range[1], 1., 1., 1)

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
        self.ren.AddVolume(volume)





if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    window = Master()
    window.show()
    window.setWindowState(QtCore.Qt.WindowMaximized)  # Maximize the window
    window.iren.Initialize()  # Need this line to actually show
    sys.exit(app.exec_())
    # callbacks value changed
    # window.ui.sliderMinGrad.valueChanged.connect(window.MinGrad_callback)




