import vtk
import os
import re

import sys
# print(os.listdir("./isabel/"))

# lsdir = ["velocity"]
base_dir = "./isabel/velocity/"
files_to_rename = os.listdir(base_dir)

for f in files_to_rename:
    break
    velocity_reader = vtk.vtkXMLImageDataReader()
    velocity_reader.SetFileName(base_dir+f)
    velocity_reader.Update()
    data = velocity_reader.GetOutput()
    data.GetPointData().GetVectors().SetName("velocity")
    writer = vtk.vtkXMLImageDataWriter()
    writer.SetInputData(data)

    writer.SetFileName("./velocity/"+f)
    writer.Write()

