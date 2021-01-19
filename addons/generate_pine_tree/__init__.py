from mathutils import Vector, Matrix
from random import randint, random, uniform
import bmesh
import math
import bpy_extras
import bpy

bl_info = {
    "name": "Generate Pine Tree Add-on",
    "author": "Jaroch, Alexander; Kaserer, Patrick; Wolf, Vivian",
    "version": (0, 0, 1),
    "blender": (2, 90, 0),
    "description": "Generate a radomized tree according to user settings",
    "category": "Mesh",
    "support": "TESTING",
    "location": "View 3D > Object Mode > Add > Mesh",
}


class GeneratePineTree(bpy.types.Operator, bpy_extras.object_utils.AddObjectHelper):
    bl_idname = "mesh.generate_pine_tree"
    bl_label = "Generate Pine Tree"
    bl_options = {'REGISTER', 'UNDO'}

    radius_top = bpy.props.FloatProperty(
        name="Radius Top",
        description="Radius at top of tree trunk",
        default=0.02,
        min=0,
        soft_max=1,
        step=1
    )

    radius_bottom = bpy.props.FloatProperty(
        name="Radius Bottom",
        description="Radius at bottom of tree trunk",
        default=0.15,
        min=0.1,
        soft_max=1,
        step=1
    )

    radius_reduction = bpy.props.FloatProperty(
        name="Reduction (%)",
        description="Factor at which radius is reduced per ring",
        default=1,
        min=0,
        max=100,
        soft_max=10,
        step=5
    )

    height = bpy.props.FloatProperty(
        name="Height",
        description="Height of tree",
        default=3,
        min=0.5,
        soft_max=10,
        step=10
    )

    segments = bpy.props.IntProperty(
        name="Segments",
        description="Number of segments in ring",
        default=16,
        min=3,
        max=32,
        soft_max=16
    )

    branch_height_lower = bpy.props.FloatProperty(
        name="Branch Start (%)",
        description="Height at which branches begin",
        default=10,
        min=0,
        max=100,
        step=50
    )

    branch_height_upper = bpy.props.FloatProperty(
        name="Branch End (%)",
        description="Height at which branches end",
        default=90,
        min=0,
        max=100,
        step=50
    )

    branch_count = bpy.props.IntProperty(
        name="Branch Count",
        description="Number of branches",
        default=20,
        min=0,
        max=40
    )

    branch_length = bpy.props.FloatProperty(
        name="Branch Length",
        description="Maximum branch length",
        default=1.5,
        min=0.25,
        soft_max=5,
        step=10
    )

    twig_count = bpy.props.IntProperty(
        name="Twig Count",
        description="Number of twigs with leaves",
        default=0,
        min=0,
        max=600
    )

    do_generate_branches = bpy.props.BoolProperty(
        name="Generate Branches",
        description="Start generating branches",
        default=False
    )

    # not yet user input (reason: scale and rotation of branches and twigs do not use these values)
    branch_segments = 8
    twig_segments = 16

    # mesh attributes
    mesh_tree = None
    mesh_leaves = None
    bmesh_tree = None
    bmesh_leaves = None

    delta = 0
    height_delta = 0
    height_segments = 0

    branch_faces = []
    branch_start = 0
    branch_end = 0
    branch_extrudable = []

    def clear(self):
        for child in bpy.data.objects:
            bpy.data.objects.remove(child)

        for child in bpy.data.meshes:
            bpy.data.meshes.remove(child)

    def create_meshes(self, context):
        collection = context.collection

        self.mesh_tree = bpy.data.meshes.new("Tree")
        self.mesh_leaves = bpy.data.meshes.new("Leaves")

        tree = bpy.data.objects.new(self.mesh_tree.name, self.mesh_tree)
        leaves = bpy.data.objects.new(self.mesh_leaves.name, self.mesh_leaves)
        leaves.parent = tree

        collection.objects.link(tree)
        collection.objects.link(leaves)

        context.view_layer.objects.active = tree

        self.bmesh_tree = bmesh.new()
        self.bmesh_leaves = bmesh.new()

    def calculate_values(self):
        self.delta = (2 * math.pi) / self.segments
        radius = (self.radius_top + self.radius_bottom) / 2
        width = self.delta * radius

        self.height_segments = math.ceil(self.height / width)
        self.height_delta = self.height / self.height_segments

    def branch_height(self, height):
        if self.branch_height_lower > self.branch_height_upper:
            lower = self.branch_height_lower
            self.branch_height_lower = self.branch_height_upper
            self.branch_height_upper = lower

        return height > self.branch_height_lower / 100 * self.height_segments and height < self.branch_height_upper / 100 * self.height_segments

    def reduce(self, value, ratio):
        return value - value * ratio

    def generate_trunk(self):
        new_radius = self.radius_bottom
        last_ring = []
        self.branch_faces = []
        
        # creater new ring
        for n in range(self.height_segments + 1):
            radius = (1 - n / self.height_segments) * new_radius + (n / self.height_segments) * self.radius_top
            ring = []
            for i in range(self.segments):
                x = radius * math.cos(i * self.delta)
                y = radius * math.sin(i * self.delta)
                v = self.bmesh_tree.verts.new((x, y, n * self.height_delta))
                ring.append(v)

            if n == 0:
                self.bmesh_tree.faces.new(ring)
            else:
                # create new faces from old and new ring
                for i in range(self.segments):
                    face = [last_ring[i], last_ring[(i + 1) % self.segments], ring[(i + 1) % self.segments], ring[i]]
                    branch_face = self.bmesh_tree.faces.new(face)
                    if self.branch_height(n):
                        self.branch_faces.append(branch_face)
                if n == self.height_segments:
                    self.bmesh_tree.faces.new(ring)

             # curve reduce
            new_radius = self.reduce(new_radius, self.radius_reduction / 100)
            last_ring = ring

    def adjacent_indices(self, n):
        indices = []
        operations_border = [0, -self.segments + 1, self.segments, 1]
        operations_normal = [0, 1, self.segments, self.segments + 1]

        for i in range(4):
            if n % self.segments == self.segments - 1:
                indices.append(n + operations_border[i])
            else:
                indices.append(n + operations_normal[i])
        return indices

    def check_branch_extrudable(self, indices):
        for index in indices:
            if self.branch_extrudable[index]:
                return False
        return True

    def get_branch_faces(self, indices):
        faces = []
        for index in indices:
            faces.append(self.branch_faces[index])
            self.branch_extrudable[index] = True
        return faces

    def calc_average_face_normal(self, faces):
        average = Vector((0, 0, 0))
        for face in faces:
            average = average + face.normal
        return average / len(faces)

    def extrude_faces(self, faces, direction):
        extrude = bmesh.ops.extrude_face_region(self.bmesh_tree, geom=faces)
        vertices = [vert for vert in extrude['geom'] if isinstance(vert, bmesh.types.BMVert)]

        bmesh.ops.translate(self.bmesh_tree, vec=direction, verts=vertices)
        bmesh.ops.delete(self.bmesh_tree, geom=faces, context="FACES")

        return [face for face in extrude['geom'] if isinstance(face, bmesh.types.BMFace)]

    def calc_center_of_faces(self, faces):
        center = Vector((0, 0, 0))
        verts = set()
        vert_count = 0
        for face in faces:
            for vert in face.verts:
                center = center + vert.co
                vert_count = vert_count + 1
                verts.add(vert)
        center = center / vert_count
        return (center, list(verts))

    def local_axes(self, x_local):
        z_rot = Matrix([(0, -1, 0), (1, 0, 0), (0, 0, 1)])
        y_proj = Vector((x_local.x, x_local.y, 0))
        y_local = y_proj @ z_rot
        z_local = x_local.cross(y_local)
        return (x_local.normalized(), y_local.normalized(), z_local.normalized())

    def rotate_faces(self, faces, direction, scale_factor, rad_x, rad_y, rad_z):
        center, vertices = self.calc_center_of_faces(faces)
        translate = Matrix.Translation(-center)
        x_loc, y_loc, z_loc = self.local_axes(direction)

        scale = Matrix.Scale(scale_factor, 4)
        rot_x = Matrix.Rotation(rad_x, 4, x_loc)
        rot_y = Matrix.Rotation(rad_y, 4, y_loc)
        rot_z = Matrix.Rotation(rad_z, 4, z_loc)

        transform = rot_z @ rot_y @ rot_x @ scale
        bmesh.ops.transform(self.bmesh_tree, matrix=transform, verts=vertices, space=translate)

    def generate_branches(self):
        self.bmesh_tree.faces.ensure_lookup_table()
        self.branch_start = len(self.bmesh_tree.faces)
        self.branch_extrudable = [False] * len(self.branch_faces)

        for _ in range(self.branch_count):
            random_index = randint(0, len(self.branch_faces) - self.segments - 1)
            adjacent_indices = self.adjacent_indices(random_index)

            if self.check_branch_extrudable(adjacent_indices):
                faces = self.get_branch_faces(adjacent_indices)
                
                for _ in range(self.branch_segments):
                    total_segments = self.segments * self.height_segments
                    segment_length = (1 - random_index / total_segments) * self.branch_length / self.branch_segments

                    direction = self.calc_average_face_normal(faces) * segment_length
                    faces = self.extrude_faces(faces, direction)
                    self.rotate_faces(faces, direction, uniform(0.65, 0.8), uniform(-0.2, 0.2), uniform(-0.1, 0.3), uniform(-0.2, 0.2))

        self.bmesh_tree.faces.ensure_lookup_table()
        self.branch_end = len(self.bmesh_tree.faces)

    def add_leaf(self, face, factor, width, height):
        center = face.calc_center_median()
        translate = Matrix.Translation(-center)
        x_loc, y_loc, z_loc = self.local_axes(face.normal)

        c1 = center
        c2 = center + y_loc * width
        c3 = center + x_loc * height + y_loc * width
        c4 = center + x_loc * height
        corners = [c1, c2, c3, c4]

        vertices = []
        for corner in corners:
            vertices.append(self.bmesh_leaves.verts.new(corner))
        self.bmesh_leaves.faces.new(vertices)

        rot_x = Matrix.Rotation(uniform(-math.pi, math.pi), 4, x_loc)
        rot_y = Matrix.Rotation(factor * uniform(math.pi/7, math.pi/6), 4, y_loc)
        rot_z = Matrix.Rotation(factor * uniform(math.pi/5, math.pi/4), 4, z_loc)

        transform = rot_z @ rot_y @ rot_x
        bmesh.ops.transform(self.bmesh_leaves, matrix=transform, verts=vertices, space=translate)

    def add_leaves(self, face, width, height):
        self.add_leaf(face, 1, width, height)
        self.add_leaf(face, -1, width, height)

    def generate_twigs(self):
        for _ in range(self.twig_count):
            random_index = randint(self.branch_start, self.branch_end - 1)

            self.bmesh_tree.faces.ensure_lookup_table()
            faces = [self.bmesh_tree.faces[random_index]]

            for k in range(self.twig_segments):
                segment_length = 0.0125
                scale = uniform(0.9, 0.95)
                if k == 0:
                    segment_length = 0.001
                    scale = uniform(0.1, 0.05)

                direction = self.calc_average_face_normal(faces) * segment_length
                faces = self.extrude_faces(faces, direction)
                self.rotate_faces(faces, direction, scale, uniform(-0.05, 0.05), uniform(-0.025, 0.075), uniform(-0.05, 0.05))

                for face in faces:
                    self.add_leaves(face, uniform(0.005, 0.01), uniform(0.04, 0.08))

    def smooth_tree(self):
        for face in self.bmesh_tree.faces:
            face.smooth = True

    def interpolate_colors(self, a, b, r):
        return a * r + b * (1 - r)

    def colorize(self, bmesh_part, first_color, second_color):
        color_layer = bmesh_part.loops.layers.color.new("color")
        color_table = {v: self.interpolate_colors(first_color, second_color, uniform(0, 1)) for v in bmesh_part.verts}
        for face in bmesh_part.faces:
            for loop in face.loops:
                loop[color_layer] = color_table[loop.vert]

    def colorize_trunk(self):
        brown_dark = Vector((0.2431, 0.1960, 0.1569, 1))
        brown_light = Vector((0.3177, 0.2549, 0.2039, 1))
        self.colorize(self.bmesh_tree, brown_dark, brown_light)

    def colorize_leaves(self):
        green_dark = Vector((0.0627, 0.2862, 0.0627, 1))
        green_light = Vector((0.3294, 0.5490, 0.1843, 1))
        self.colorize(self.bmesh_leaves, green_dark, green_light)

    def free_meshes(self):
        self.bmesh_tree.to_mesh(self.mesh_tree)
        self.bmesh_tree.free()

        self.bmesh_leaves.to_mesh(self.mesh_leaves)
        self.bmesh_leaves.free()

        # bpy.ops.object.editmode_toggle()

    def generate_tree(self, context):
        # self.clear()
        self.create_meshes(context)
        self.calculate_values()
        self.generate_trunk()

        if self.do_generate_branches:
            self.generate_branches()
            self.generate_twigs()

            self.do_generate_branches = False

        self.smooth_tree()
        self.colorize_trunk()
        self.colorize_leaves()

        self.free_meshes()

    def execute(self, context):
        self.generate_tree(context)
        return {'FINISHED'}


def add_object_button(self, context):
    self.layout.operator(
        GeneratePineTree.bl_idname,
        text="Pine Tree",
        icon='PLUGIN'
    )


def register():
    print("Registering Generate Pine Tree")
    bpy.utils.register_class(GeneratePineTree)
    bpy.types.VIEW3D_MT_mesh_add.append(add_object_button)


def unregister():
    print("Unregistering Generate Pine Tree")
    bpy.utils.unregister_class(GeneratePineTree)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_object_button)
