import bpy
import math
import bmesh
from random import randint, random, uniform
from mathutils import Vector, Matrix

col = bpy.data.collections[0]
    
for child in bpy.data.objects:
    bpy.data.objects.remove(child)
    
for child in bpy.data.meshes:
    bpy.data.meshes.remove(child)

mesh = bpy.data.meshes.new("Tree")                                  # create empty mesh
mesh_leaves = bpy.data.meshes.new("Leaves")                         # create empty mesh for leaves

obj = bpy.data.objects.new(mesh.name, mesh)                         # create empty object with mesh
obj_leaves = bpy.data.objects.new(mesh_leaves.name, mesh_leaves)    # create empty object with mesh_leaves

col.objects.link(obj)  
col.objects.link(obj_leaves)                         # add object to collection
obj_leaves.parent = obj                    # add object_leaves to collection

bpy.context.view_layer.objects.active = obj     # select object

# create empty BMesh
bm = bmesh.new()
bm_leaves = bmesh.new()

# cylinder variables
radius_bottom = 0.15
radius_top = 0.02
radius_reduction = 0.99
height = 4
segments = 16
branch_top = 5
branch_height = 10
branch_count = 40
leaf_count = 10

# height segments
circumference = 2 * math.pi * (radius_top + radius_bottom) / 2
width = circumference / segments
height_segments = math.ceil(height / width)

total_segments = segments * height_segments

def get_index(n, i):
    operations_border = [0, -segments + 1, segments, 1]
    operations_normal = [0, 1, segments, segments + 1]

    if n % segments == segments - 1:
        return n + operations_border[i]
    else:
        return n + operations_normal[i]
    
def avg_normal(normals):
    avg = Vector((0, 0, 0))
    for normal in normals:
        avg = avg + normal
    return avg / len(normals)

def get_normals(faces):
    normals = []
    for face in faces:
        normals.append(face.normal)
    return normals

# calculates center of given BMFaces and returns its center and a set of used verts 
def calc_center_of_faces(faces):    
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

def local_axes(x_local):    
    z_rot = Matrix([(0, -1, 0), (1, 0, 0), (0, 0, 1)])    
    y_proj = Vector((x_local.x, x_local.y, 0))
    y_local = y_proj @ z_rot    
    z_local = x_local.cross(y_local)    
    return (x_local.normalized(), y_local.normalized(), z_local.normalized())

def add_plane(bm, branch_face, factor):
    w = 0.01
    h = 0.08
    bf_normal = branch_face.normal
    loc_x, loc_y, loc_z = local_axes(bf_normal)
    corners = [0 * loc_x , loc_x*h , loc_x*h + loc_y*w, loc_y*w]
    vertices = []
    for i in range(4):
        vertices.append(bm.verts.new(corners[i]))
    face = bm.faces.new(vertices)
    face_center = branch_face.calc_center_median()   
                
    translate = Matrix.Translation(vertices[0].co)            
                                   
    rot_x = Matrix.Rotation(uniform(-math.pi, math.pi), 4, loc_x)
    rot_z = Matrix.Rotation(factor * uniform(math.pi/5, math.pi/4), 4, loc_z)
    rot_y = Matrix.Rotation(factor * uniform(math.pi/7, math.pi/6), 4, loc_y)
    
    transform = rot_z @ rot_y @ rot_x
    #transform = scale                   
    bmesh.ops.transform(bm, matrix=transform, verts=vertices, space=translate)
    bmesh.ops.translate(bm, vec=face_center, verts=vertices)

            
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
        index = get_index(r, k)
        
        if used_faces[index]:
            used = True
            break
        
    if not used:   
        for k in range(4):
            index = get_index(r, k)
            
            face = side_faces[index]
            used_faces[index] = True
                
            bmface = bm.faces.get(face)            
            extrude_faces.append(bmface)
            
        branch_extrude = 8
        for x in range(branch_extrude):
                        
            extruded = bmesh.ops.extrude_face_region(bm, geom=extrude_faces)            
            translate_verts = [v for v in extruded['geom'] if isinstance(v, bmesh.types.BMVert)]

            length = (1 - r / total_segments) * 2 / branch_extrude
            
            direction = avg_normal(get_normals(extrude_faces)) * -1 * length
            
            bmesh.ops.translate(bm, vec=direction, verts=translate_verts)
             
            bmesh.ops.delete(bm, geom=extrude_faces, context="FACES")
            
            extrude_faces = [f for f in extruded['geom'] if isinstance(f, bmesh.types.BMFace)]
            
            center, face_verts = calc_center_of_faces(extrude_faces)            
            translate = Matrix.Translation(-center)            
            x_loc, y_loc, z_loc = local_axes(direction)
            
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
        
        direction = avg_normal(get_normals(extrude_faces)) * -1 * length
        
        bmesh.ops.translate(bm, vec=direction, verts=translate_verts)
         
        bmesh.ops.delete(bm, geom=extrude_faces, context="FACES")
        
        extrude_faces = [f for f in extruded['geom'] if isinstance(f, bmesh.types.BMFace)]
        
        center, face_verts = calc_center_of_faces(extrude_faces)            
        translate = Matrix.Translation(-center)            
        x_loc, y_loc, z_loc = local_axes(direction)
        
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
      
            add_plane(bm_leaves, face, 1)
            add_plane(bm_leaves, face, -1)

#Smooth Mesh
for face in bm.faces:
    face.smooth = True             

# BMesh to Mesh
bm.to_mesh(mesh)
bm.free()

bm_leaves.to_mesh(mesh_leaves)
bm_leaves.free()

#bpy.ops.object.editmode_toggle()