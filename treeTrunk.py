import bpy
import math
import bmesh

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
radius_top = 0.06
radius_reduction = 0.9
height = 5
height_segments = 4
segments = 16
branch_height = 2

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

# BMesh to Mesh
bm.to_mesh(mesh)
bm.free()

bpy.ops.object.editmode_toggle()
