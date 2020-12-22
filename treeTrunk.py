import bpy
import math
import bmesh
from random import randint, random
from mathutils import Vector, Matrix

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
height = 3
height_segments = height * 32
segments = 16
branch_height = 10
branch_count = 50

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

c = 0

for i in range(branch_count):
    l = len(side_faces)
    r = randint(branch_height * segments, l - segments - 2)
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
            
        branch_extrude = 5
        for x in range(branch_extrude):
                        
            extruded = bmesh.ops.extrude_face_region(bm, geom=extrude_faces)            
            translate_verts = [v for v in extruded['geom'] if isinstance(v, bmesh.types.BMVert)] 
           # print(str(translate_verts))

            length = (1 - r / total_segments) * 2 / branch_extrude
            
            random_t = (random() * 0.05 - 0.025, random() * 0.05 - 0.025, random() * 0.1)
            
            direction = avg_normal(get_normals(extrude_faces)) * -1 * length + Vector(random_t)
            
            bmesh.ops.translate(bm, vec=direction, verts=translate_verts)
            #m = Matrix.Translation((0, 0, 0)) * Matrix.Scale(0.7, 4) * Matrix.Translation(direction)
            #bmesh.ops.translate(bm, verts=translate_verts, space=m)  
            #bmesh.ops.scale(bm, verts=translate_verts, space=m) 
             
            bmesh.ops.delete(bm, geom=extrude_faces, context="FACES")
            
            extrude_faces = [f for f in extruded['geom'] if isinstance(f, bmesh.types.BMFace)]
            for face in extrude_faces:
                for m in range(len(extrude_faces)):
                    face.select_set(True)
                    calculation = extrude_faces[m].calc_center_median()
                    vertices = extrude_faces[m].verts
                    translation_matrix = Matrix.Translation(-calculation)
                    scale = Matrix.Scale(0.8,4)
                    bmesh.ops.transform(bm, matrix=scale, verts=vertices, space=translation_matrix)

                
            edges = [e for e in extruded['geom'] if isinstance(e, bmesh.types.BMEdge)]
            
            for edge in edges:
                edge.select_set(False)
            
        c = c + 1
        
print("extruded " + str(c) + " faces")


# BMesh to Mesh
bm.to_mesh(mesh)
bm.free()

bpy.ops.object.editmode_toggle()
