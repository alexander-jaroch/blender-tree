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

    leaf_count = bpy.props.IntProperty (
        name = "Leaf Count",
        description = "Number of leaves",
        default = 50,
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

    def add_plane(self, bm, branch_face, factor):
        w = 0.01
        h = 0.08
        bf_normal = branch_face.normal
        loc_x, loc_y, loc_z = self.local_axes(bf_normal)
        corners = [0 * loc_x , loc_x*h , loc_x*h + loc_y*w, loc_y*w]
        vertices = []
        for i in range(4):
            vertices.append(bm.verts.new(corners[i]))
        bm.faces.new(vertices)
        face_center = branch_face.calc_center_median()   
                    
        translate = Matrix.Translation(vertices[0].co)            
                                    
        rot_x = Matrix.Rotation(uniform(-math.pi, math.pi), 4, loc_x)
        rot_z = Matrix.Rotation(factor * uniform(math.pi/5, math.pi/4), 4, loc_z)
        rot_y = Matrix.Rotation(factor * uniform(math.pi/7, math.pi/6), 4, loc_y)
        
        transform = rot_z @ rot_y @ rot_x
        #transform = scale                   
        bmesh.ops.transform(bm, matrix=transform, verts=vertices, space=translate)
        bmesh.ops.translate(bm, vec=face_center, verts=vertices)

    def execute(self, context):
        col = bpy.data.collections[0]
    
        for child in bpy.data.objects:
            bpy.data.objects.remove(child)
            
        for child in bpy.data.meshes:
            bpy.data.meshes.remove(child)

        mesh = bpy.data.meshes.new("Tree")                                  # create empty mesh
        mesh_leaves = bpy.data.meshes.new("Leaves")                         # create empty mesh for leaves

        obj = bpy.data.objects.new(mesh.name, mesh)                         # create empty object with mesh
        obj_leaves = bpy.data.objects.new(mesh_leaves.name, mesh_leaves)    # create empty object with mesh_leaves

        col.objects.link(obj)                        # add object to collection
        col.objects.link(obj_leaves)                   # add object_leaves to collection      
        obj_leaves.parent = obj                   #parent object_leaves to obj

        bpy.context.view_layer.objects.active = obj     # select object

        # create empty BMesh
        bm = bmesh.new()
        bm_leaves = bmesh.new()
        
        radius_bottom = self.radius_bottom
        radius_top = self.radius_top
        radius_reduction = self.radius_reduction
        height = self.height
        segments = self.segments
        branch_top = self.branch_top
        branch_height = self.branch_height
        branch_count = self.branch_count
        leaf_count = self.leaf_count

        # height segments
        circumference = 2 * math.pi * (radius_top + radius_bottom) / 2
        width = circumference / segments
        height_segments = math.ceil(height / width)

        total_segments = segments * height_segments
        # calculate angle delta
        delta = (2 * math.pi) / segments
        height_delta = height / height_segments

        # create trunk
        last_ring = []
        side_faces = []
        for n in range(height_segments + 1):
            radius = (1 - n / height_segments) * radius_bottom + (n / height_segments) * radius_top
            ring = []
            for i in range(segments):
                x = radius * math.cos(i * delta)
                y = radius * math.sin(i * delta)
                v = bm.verts.new((x, y, n * height_delta))
                ring.append(v)
            if n == 0:
                bm.faces.new(ring)
            else:
                for i in range(segments):
                    face = [last_ring[i], last_ring[(i + 1) % segments], ring[(i + 1) % segments], ring[i]]
                    if n > branch_height:
                        side_faces.append(face)
                    bm.faces.new(face)
                if n == height_segments:
                    bm.faces.new(ring)
            last_ring = ring
            radius_bottom = radius_bottom * radius_reduction
            
        # create branches
        used_faces = [False] * len(side_faces)
        bm.faces.ensure_lookup_table()
        branch_start = len(bm.faces)

        actual_branch_count = 0

        for i in range(branch_count):
            l = len(side_faces)
            r = randint(branch_height * segments, l - (branch_top + 1) * segments - 1)
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
                        
                    bmface = bm.faces.get(face)            
                    extrude_faces.append(bmface)
                    
                branch_extrude = 8
                for x in range(branch_extrude):
                                
                    extruded = bmesh.ops.extrude_face_region(bm, geom=extrude_faces)            
                    translate_verts = [v for v in extruded['geom'] if isinstance(v, bmesh.types.BMVert)]

                    length = (1 - r / total_segments) * 2 / branch_extrude
                    
                    direction = self.avg_normal(self.get_normals(extrude_faces)) * -1 * length
                    
                    bmesh.ops.translate(bm, vec=direction, verts=translate_verts)
                    
                    bmesh.ops.delete(bm, geom=extrude_faces, context="FACES")
                    
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
                        bmesh.ops.transform(bm, matrix=transform, verts=list(face_verts), space=translate)   
                        
                actual_branch_count = actual_branch_count + 1
                    
        print("added " + str(actual_branch_count) + " branches")

        max_len = len(bm.faces)
            
        for i in range(leaf_count):
            # add twigs
            bm.faces.ensure_lookup_table()
            extrude_faces = [bm.faces[randint(branch_start, max_len - 1)]]
                    
            # scale first face ?
            
            branch_extrude = 16
            for x in range(branch_extrude):
                extruded = bmesh.ops.extrude_face_region(bm, geom=extrude_faces)            
                translate_verts = [v for v in extruded['geom'] if isinstance(v, bmesh.types.BMVert)]

                length = 0.001
                
                if x > 0:
                    length = 0.0125
                
                direction = self.avg_normal(self.get_normals(extrude_faces)) * -1 * length
                
                bmesh.ops.translate(bm, vec=direction, verts=translate_verts)
                
                bmesh.ops.delete(bm, geom=extrude_faces, context="FACES")
                
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
                    bmesh.ops.transform(bm, matrix=transform, verts=list(face_verts), space=translate)
            
                    self.add_plane(bm_leaves, face, 1)
                    self.add_plane(bm_leaves, face, -1)
                    
        #Smooth Mesh
        for face in bm.faces:
            face.smooth = True
               
        # BMesh to Mesh
        bm.to_mesh(mesh)
        bm.free()

        bm_leaves.to_mesh(mesh_leaves)
        bm_leaves.free()

        #Smooth Mesh

        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}

def register():
    print("Registering Generate Pine Tree")
    bpy.utils.register_class(GeneratePineTree)

def unregister():
    print("Unregistering Generate Pine Tree")
    bpy.utils.unregister_class(GeneratePineTree)