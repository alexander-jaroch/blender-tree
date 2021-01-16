bl_info = {
    "name": "Generate Pine Tree Add-on",
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

class GeneratePineTree(bpy.types.Operator):
    bl_idname = "mesh.generate_pine_tree"
    bl_label = "Generate Pine Tree"
    bl_options = {'REGISTER', 'UNDO'}

    generate_branches = bpy.props.BoolProperty(
        name = "Generate Branches",
        description = "Start generating branches",
        default = False
    )

    radius_bottom = bpy.props.FloatProperty(
        name = "Radius Bottom",
        description = "Radius at bottom of tree trunk",
        default = 0.15,
        min = 0.1, 
        soft_max = 1,
    )

    radius_top = bpy.props.FloatProperty(
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
        min = 0.5,
        soft_max = 1
    )

    height = bpy.props.FloatProperty(
        name = "Height",
        description = "Height of tree",
        default = 3,
        min = 0.5,
        soft_max = 10
    )

    segments = bpy.props.IntProperty (
        name = "Segments",
        description = "Number of segments in ring",
        default = 16,
        min = 3,
        soft_max = 16
    )

    branch_height = bpy.props.IntProperty (
        name = "Branch Height",
        description = "Height at which branches begin",
        default = 10,
        min = 1,
        max = 20
    )

    branch_top = bpy.props.IntProperty (
        name = "Upper Branch Limit",
        description = "Limit of branches at the top of the trunk",
        default = 5,
        min = 1,
        soft_max = 20
    )

    branch_count = bpy.props.IntProperty (
        name = "Branch Count",
        description = "Number of branches",
        default = 40,
        min = 0,
        max = 60
    )

    twig_count = bpy.props.IntProperty (
        name = "Twig Count",
        description = "Number of twigs with leaves",
        default = 0,
        min = 0,
        max = 400
    )

    def get_index(self, n, i):
        operations_border = [0, -self.segments + 1, self.segments, 1]
        operations_normal = [0, 1, self.segments, self.segments + 1]

        if n % self.segments == self.segments - 1:
            return n + operations_border[i]
        else:
            return n + operations_normal[i]
    
    def avg_normal(self, normals):
        avg = Vector((0, 0, 0))
        for normal in normals:
            avg = avg + normal
        return avg / len(normals)

    def get_normals(self, faces):
        normals = []
        for face in faces:
            normals.append(face.normal)
        return normals

    # calculates center of given BMFaces and returns its center and a set of used verts 
    def calc_center_of_faces(self, faces):    
        center = Vector((0,0,0))
        verts = set()
        vert_count = 0
        for face in faces:
            for vert in face.verts:           
                center = center + vert.co
                vert_count = vert_count + 1
                verts.add(vert)
        center = center / vert_count
        return (center, verts)

    def local_axes(self, x_local):    
        z_rot = Matrix([(0, -1, 0), (1, 0, 0), (0, 0, 1)])    
        y_proj = Vector((x_local.x, x_local.y, 0))
        y_local = y_proj @ z_rot    
        z_local = x_local.cross(y_local)    
        return (x_local.normalized(), y_local.normalized(), z_local.normalized())

    def add_plane(self, branch_face, factor):
        w = 0.01
        h = 0.08
        bf_normal = branch_face.normal
        loc_x, loc_y, loc_z = self.local_axes(bf_normal)
        corners = [0 * loc_x , loc_x*h , loc_x*h + loc_y*w, loc_y*w]
        vertices = []
        for i in range(4):
            vertices.append(self.bmesh_leaves.verts.new(corners[i]))
        self.bmesh_leaves.faces.new(vertices)
        face_center = branch_face.calc_center_median()   
                    
        translate = Matrix.Translation(vertices[0].co)            
                                    
        rot_x = Matrix.Rotation(uniform(-math.pi, math.pi), 4, loc_x)
        rot_z = Matrix.Rotation(factor * uniform(math.pi/5, math.pi/4), 4, loc_z)
        rot_y = Matrix.Rotation(factor * uniform(math.pi/7, math.pi/6), 4, loc_y)
        
        transform = rot_z @ rot_y @ rot_x
        #transform = scale                   
        bmesh.ops.transform(self.bmesh_leaves, matrix=transform, verts=vertices, space=translate)
        bmesh.ops.translate(self.bmesh_leaves, vec=face_center, verts=vertices)

    # mesh attributes
    mesh_tree = None
    mesh_leaves = None
    bmesh_tree = None
    bmesh_leaves = None

    new_radius = 0

    # clear scene
    def clear(self):
        for child in bpy.data.objects:
            bpy.data.objects.remove(child)
            
        for child in bpy.data.meshes:
            bpy.data.meshes.remove(child)

    # create and link empty meshes
    def create_meshes(self):
        collection = bpy.context.collection
    
        self.mesh_tree = bpy.data.meshes.new("Tree")
        self.mesh_leaves = bpy.data.meshes.new("Leaves")

        tree = bpy.data.objects.new(self.mesh_tree.name, self.mesh_tree)
        leaves = bpy.data.objects.new(self.mesh_leaves.name, self.mesh_leaves)
        leaves.parent = tree

        collection.objects.link(tree)
        collection.objects.link(leaves)

        bpy.context.view_layer.objects.active = tree

        self.bmesh_tree = bmesh.new()
        self.bmesh_leaves = bmesh.new()

    # return meshes
    def free_meshes(self):
        self.bmesh_tree.to_mesh(self.mesh_tree)
        self.bmesh_tree.free()

        self.bmesh_leaves.to_mesh(self.mesh_leaves)
        self.bmesh_leaves.free()

        #bpy.ops.object.editmode_toggle()

    def calculate_values():
        print("calc")

    # generate pine tree
    def generate(self):    
        #self.clear()
        self.create_meshes()

        # height segments
        circumference = 2 * math.pi * (self.radius_top + self.radius_bottom) / 2
        segment_width = circumference / self.segments
        height_segments = math.ceil(self.height / segment_width)

        # total segments
        total_segments = self.segments * height_segments
        # calculate angle delta
        delta = (2 * math.pi) / self.segments
        height_delta = self.height / height_segments

        # create trunk
        last_ring = []
        side_faces = []
        new_radius = self.radius_bottom

        for n in range(height_segments + 1):
            radius = (1 - n / height_segments) * new_radius + (n / height_segments) * self.radius_top
            ring = []
            for i in range(self.segments):
                x = radius * math.cos(i * delta)
                y = radius * math.sin(i * delta)
                v = self.bmesh_tree.verts.new((x, y, n * height_delta))
                ring.append(v)
            if n == 0:
                self.bmesh_tree.faces.new(ring)
            else:
                for i in range(self.segments):
                    face = [last_ring[i], last_ring[(i + 1) % self.segments], ring[(i + 1) % self.segments], ring[i]]
                    if n > self.branch_height:
                        side_faces.append(face)
                    self.bmesh_tree.faces.new(face)
                if n == height_segments:
                    self.bmesh_tree.faces.new(ring)
            last_ring = ring
            new_radius = new_radius * self.radius_reduction
        
        if self.generate_branches:
            # create branches
            used_faces = [False] * len(side_faces)
            self.bmesh_tree.faces.ensure_lookup_table()
            branch_start = len(self.bmesh_tree.faces)

            for i in range(self.branch_count):
                l = len(side_faces)
                r = randint(self.branch_height * self.segments, l - (self.branch_top + 1) * self.segments - 1)
                used = False
                    
                extrude_faces = []
                
                for k in range(4):
                    index = self.get_index(r, k)
                
                    if used_faces[index]:
                        used = True
                        break
                
                if not used:   
                    for k in range(4):
                        index = self.get_index(r, k)
                    
                        face = side_faces[index]
                        used_faces[index] = True
                        
                        bmface = self.bmesh_tree.faces.get(face)            
                        extrude_faces.append(bmface)
                    
                    branch_extrude = 8
                    for x in range(branch_extrude):
                                
                        extruded = bmesh.ops.extrude_face_region(self.bmesh_tree, geom=extrude_faces)            
                        translate_verts = [v for v in extruded['geom'] if isinstance(v, bmesh.types.BMVert)]

                        length = (1 - r / total_segments) * 2 / branch_extrude
                    
                        direction = self.avg_normal(self.get_normals(extrude_faces)) * -1 * length
                    
                        bmesh.ops.translate(self.bmesh_tree, vec=direction, verts=translate_verts)
                    
                        bmesh.ops.delete(self.bmesh_tree, geom=extrude_faces, context="FACES")
                    
                        extrude_faces = [f for f in extruded['geom'] if isinstance(f, bmesh.types.BMFace)]
                    
                        center, face_verts = self.calc_center_of_faces(extrude_faces)            
                        translate = Matrix.Translation(-center)            
                        x_loc, y_loc, z_loc = self.local_axes(direction)
                    
                        for face in extrude_faces:                                      
                            scale = Matrix.Scale(uniform(0.9, 0.95), 4)                
                            rot_x = Matrix.Rotation(uniform(-0.05, 0.05), 4, x_loc)
                            rot_y = Matrix.Rotation(uniform(-0.025, 0.075), 4, y_loc)
                            rot_z = Matrix.Rotation(uniform(-0.05, 0.05), 4, z_loc)
                        
                            transform = rot_z @ rot_y @ rot_x @ scale                         
                            bmesh.ops.transform(self.bmesh_tree, matrix=transform, verts=list(face_verts), space=translate)

            max_len = len(self.bmesh_tree.faces)            
            for i in range(self.twig_count):
                # add twigs
                self.bmesh_tree.faces.ensure_lookup_table()
                extrude_faces = [self.bmesh_tree.faces[randint(branch_start, max_len - 1)]]
                    
                # scale first face ?
            
                branch_extrude = 16
                for x in range(branch_extrude):
                    extruded = bmesh.ops.extrude_face_region(self.bmesh_tree, geom=extrude_faces)            
                    translate_verts = [v for v in extruded['geom'] if isinstance(v, bmesh.types.BMVert)]

                    length = 0.001
                
                    if x > 0:
                        length = 0.0125
                
                    direction = self.avg_normal(self.get_normals(extrude_faces)) * -1 * length
                
                    bmesh.ops.translate(self.bmesh_tree, vec=direction, verts=translate_verts)
                
                    bmesh.ops.delete(self.bmesh_tree, geom=extrude_faces, context="FACES")
                
                    extrude_faces = [f for f in extruded['geom'] if isinstance(f, bmesh.types.BMFace)]
                
                    center, face_verts = self.calc_center_of_faces(extrude_faces)            
                    translate = Matrix.Translation(-center)            
                    x_loc, y_loc, z_loc = self.local_axes(direction)
                
                    for face in extrude_faces:    
                        scale = Matrix.Scale(uniform(0.1, 0.05), 4)
                        if x > 0: 
                            scale = Matrix.Scale(uniform(0.9, 0.95), 4)    
                                        
                        rot_x = Matrix.Rotation(uniform(-0.05, 0.05), 4, x_loc)
                        rot_y = Matrix.Rotation(uniform(-0.025, 0.075), 4, y_loc)
                        rot_z = Matrix.Rotation(uniform(-0.05, 0.05), 4, z_loc)
                    
                        transform = rot_z @ rot_y @ rot_x @ scale 
                        #transform = scale                   
                        bmesh.ops.transform(self.bmesh_tree, matrix=transform, verts=list(face_verts), space=translate)
            
                        self.add_plane(face, 1)
                        self.add_plane(face, -1)

            self.generate_branches = False
                    
        #Smooth Mesh
        for face in self.bmesh_tree.faces:
            face.smooth = True

        self.free_meshes()

    def execute(self, context):
        self.generate()
        return {'FINISHED'}

def register():
    print("Registering Generate Pine Tree")
    bpy.utils.register_class(GeneratePineTree)

def unregister():
    print("Unregistering Generate Pine Tree")
    bpy.utils.unregister_class(GeneratePineTree)