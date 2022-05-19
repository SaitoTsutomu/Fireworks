import re

import bpy
import yaml

bl_info = {
    "name": "Fireworks",
    "author": "tsutomu",
    "version": (0, 1),
    "blender": (3, 1, 0),
    "support": "TESTING",
    "category": "Object",
    "description": "",
    "location": "View3D > Sidebar > Edit Tab",
    "warning": "",
    "doc_url": "https://github.com/SaitoTsutomu/Fireworks",  # ドキュメントURL
}


def make_material(st, name, attr):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.blend_method = "HASHED"
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    if "color_ramp" in attr:
        clrm = mat.node_tree.nodes.new(type="ShaderNodeValToRGB")
        attr_elms = attr.get("color_ramp", {})
        for _ in range(len(clrm.color_ramp.elements), len(attr_elms)):
            clrm.color_ramp.elements.new(position=0)
        for element, attr_elm in zip(clrm.color_ramp.elements, attr_elms):
            element.position = attr_elm.get("position", 0)
            element.color = attr_elm.get("color", [1, 1, 1, 1])
        mat.node_tree.links.new(clrm.outputs["Color"], bsdf.inputs["Emission"])
        mat.node_tree.links.new(clrm.outputs["Alpha"], bsdf.inputs["Alpha"])
        drv = clrm.inputs["Fac"].driver_add("default_value").driver
        val = st.frame_end - st.frame_start + st.lifetime
        drv.expression = f"(frame - {st.frame_start}) / {val}"
    else:
        bsdf.inputs["Emission"].default_value = attr.get("color", [1, 1, 1, 1])
    bsdf.inputs["Emission Strength"].default_value = attr.get("strength", 10)
    return mat


def make_spark(st, name, attr):
    obj = bpy.context.object
    bpy.ops.mesh.primitive_cone_add(
        vertices=3,
        radius1=0.577351,
        depth=0.816497,
        calc_uvs=False,
    )
    spark = bpy.context.object
    spark.name = name
    spark.hide_set(state=True)
    spark.hide_render = True
    spark.active_material = make_material(st, name, attr)
    bpy.context.view_layer.objects.active = obj
    return spark


class CFW_OT_make_fireworks(bpy.types.Operator):
    bl_idname = "object.make_fireworks"
    bl_label = "Make"
    bl_description = ""

    filepath: bpy.props.StringProperty()  # type: ignore # noqa

    def execute(self, context):
        context.scene.eevee.use_bloom = True
        if "fireworks" in bpy.data.collections:
            bpy.data.collections.remove(bpy.data.collections["fireworks"])
            bpy.ops.outliner.orphans_purge(do_recursive=True)
        col = bpy.data.collections.new(name="fireworks")
        bpy.context.scene.collection.children.link(col)
        lc = bpy.context.view_layer.layer_collection.children["fireworks"]
        bpy.context.view_layer.active_layer_collection = lc
        with open(self.filepath) as fp:
            yml = yaml.safe_load(fp)
        for name, attr in yml.items():
            bpy.ops.mesh.primitive_ico_sphere_add(
                subdivisions=1,
                radius=attr.get("radius", 0.1),
                calc_uvs=False,
            )
            obj = context.object
            obj.name = name
            obj.active_material = make_material({}, name, attr.get("material", {}))
            launch = attr.get("launch", 1)
            explode = attr.get("explode", 48)
            obj.scale = 0.3, 0.3, 0.3
            obj.keyframe_insert(data_path="scale", frame=launch)
            obj.location = attr.get("launch_location", [0, 0, 0])
            launch_location = obj.location.copy()
            obj.keyframe_insert(data_path="location", frame=launch)
            obj.scale = 1, 1, 1
            obj.keyframe_insert(data_path="scale", frame=explode)
            obj.location = attr.get("explode_location", [0, 0, 10])
            obj.keyframe_insert(data_path="location", frame=explode)
            disappear = (explode - launch) * 1.3 + launch
            obj.scale = 0.001, 0.001, 0.001
            obj.keyframe_insert(data_path="scale", frame=disappear)
            disappear = (explode - launch) * 2 + launch
            obj.location = list(obj.location * 2 - launch_location)[:2] + [launch_location[2]]
            obj.keyframe_insert(data_path="location", frame=disappear)
            ptn = r"(launch|explode)\s([+-])\s*(\d+)\s*(?:|#.*)$"
            for psname, psattr in attr.get("particle_systems", {}).items():
                bpy.ops.object.particle_system_add()
                ps = obj.particle_systems[-1]
                ps.name = psname
                st = ps.settings
                st.count = psattr["count"]
                m = re.match(ptn, psattr["frame_start"])
                bs = {"launch": launch, "explode": explode}[m.group(1)]
                st.frame_start = bs + ((m.group(2) == "+") * 2 - 1) * int(m.group(3))
                m = re.match(ptn, psattr["frame_end"])
                bs = {"launch": launch, "explode": explode}[m.group(1)]
                st.frame_end = bs + ((m.group(2) == "+") * 2 - 1) * int(m.group(3))
                st.lifetime = psattr["lifetime"]
                st.lifetime_random = 1
                st.render_type = "OBJECT"
                spark = make_spark(st, f"{name}_{psname}", psattr.get("material", {}))
                st.instance_object = spark
                st.particle_size = attr.get("particle_size", 0.05)
                st.factor_random = psattr.get("factor_random", 0)
                st.normal_factor = st.effector_weights.gravity = psattr.get("gravity", 1)
        bpy.context.scene.frame_set(launch)
        return {"FINISHED"}


class CFW_PT_fireworks(bpy.types.Panel):
    bl_label = "Fireworks"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"
    bl_context = "objectmode"

    def draw(self, context):
        self.layout.prop(context.scene, "filepath", text="file")
        prop = self.layout.operator(
            CFW_OT_make_fireworks.bl_idname,
            text=CFW_OT_make_fireworks.bl_label,
        )
        prop.filepath = context.scene.filepath


classes = [
    CFW_OT_make_fireworks,
    CFW_PT_fireworks,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.filepath = bpy.props.StringProperty(default="/tmp/fireworks.yaml")


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.filepath


if __name__ == "__main__":
    register()
