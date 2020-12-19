import bpy
import math
import bmesh
from random import randint

col = bpy.data.collections.get("Collection")    # get collection from scene hirarchy

# hide children of collection
for child in col.objects:
    child.hide_set(1)

mesh = bpy.data.meshes.new("Cylinder")          # create empty mesh
obj = bpy.data.objects.new(mesh.name, mesh)     # create empty object with mesh
col.objects.link(obj)                           # add object to collection
bpy.context.view_layer.objects.active = obj     # select object

# create empty BMesh
bm = bmesh.new()

# cylinder variables
radius_bottom = 0.25
radius_top = 0.05
radius_reduction = 0.995
height = 5
height_segments = height * 32
segments = 16
branch_height = 20
branch_count = 20

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

operations_border = [0, -segments + 1, segments, 1]
operations_normal = [0, 1, segments, segments + 1]

c = 0

for i in range(branch_count):
    extrude_faces = []
    l = len(side_faces)
    r = randint(branch_height * segments, l - segments - 2)
    used = False
    
    for k in range(4):
        if r % segments == 0:
            used = used or used_faces[r + operations_border[k]]
        else:
            used = used or used_faces[r + operations_normal[k]]
        
    if not used:
        for k in range(4):
            if r % segments == segments - 1:
                face = side_faces[r + operations_border[k]]
                used_faces[r + operations_border[k]] = True
            else:
                face = side_faces[r + operations_normal[k]]        
                used_faces[r + operations_border[k]] = True    
            extrude_faces.append(face)
            bm.faces.get(face).select_set(True)
        c = c + 1
        
print("extruded " + str(c) + " faces")


# BMesh to Mesh
bm.to_mesh(mesh)
bm.free()

bpy.ops.object.editmode_toggle()
