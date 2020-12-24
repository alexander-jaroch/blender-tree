bl_info = {
    "name": "Generate Fir Tree Add-on",
    "author" : "Jaroch, Alexander; Kaserer, Patrick; Wolf, Vivian",
    "version" : (0, 0, 1),
    "blender" : (2, 90, 0),
    "description" : "Generate a radomized tree according to user settings",    
    "category": "Mesh",
    "support": "TESTING",
    "location" : "View 3D > Object Mode > Add > Mesh",
}

import bpy
import math
import bmesh
from random import randint, random, uniform
from mathutils import Vector, Matrix

class GenerateFirTree(bpy.types.Operator):
    bl_idname = "mesh.generate_fir_tree"
    bl_label = "Generate randomized tree according to user settings"
    bl_options = {'REGISTER', 'UNDO'}

    radius_bottom = bpy.props.FlaotProperty(
        name = "Radius Bottom",
        description = "Radius at bottom of tree trunk",
        default = 0.15,
        min = 0, 
        soft_max = 1,
    )

    radius_top = bpy.props.FlaotProperty(
        name = "Radius Top",
        description = "Radius at top of tree trunk",
        default = 0.02,
        min = 0, 
        soft_max = 1,
    )

    radius_reduction = bpy.props.FloatProperty(
        name = "Radius Reduction",
        description = "Factor at which radius is reduced per ring",
        default = 0.99,
        min = 0,
        max = 1
    )

    height = bpy.props.FloatProperty(
        name = "Height",
        description = "Height of tree",
        default = 4,
        min = 0,
        soft_max = 10
    )

    segments = bpy.props.IntProperty (
        name = "Segments",
        description = "Number of segments in ring",
        default = 16,
        min = 3,
        soft_max = 16
    )

    # calculate count of height segments
    height_segments = height * 32

    branch_height = bpy.props.IntProperty (
        name = "Branch Height",
        description = "Height at which branches begin",
        default = 10,
        min = 1,
        max = height_segments - 1 
    )

    branch_top = 5

    branch_count = bpy.props.IntProperty (
        name = "Branch Count",
        description = "Number of branches",
        default = 100,
        min = 0,
        soft_max = 100
    )

    def execute(self, context):
        # TO DO
        return {'FINISHED'}

def register():
    print("Registering Generate Fir Tree")
    bpy.utils.register_class(GenerateFirTree)

def unregister():
    print("Unregistering Generate Fir Tree")
    bpy.utils.unregister_class(GenerateFirTree)