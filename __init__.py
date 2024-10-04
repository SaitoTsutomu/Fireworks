import re
from pathlib import Path

import bpy
import tomllib

bl_info = {
    "name": "Fireworks",
    "author": "tsutomu",
    "version": (0, 2),
    "blender": (4, 2, 0),
    "support": "TESTING",
    "category": "Object",
    "description": "",
    "location": "View3D > Sidebar > Edit Tab",
    "warning": "",
    "doc_url": "https://github.com/SaitoTsutomu/Fireworks",
}


def make_material(st, name, attr):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.blend_method = "HASHED"
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    if "color_ramp" in attr:
        col_rmp = mat.node_tree.nodes.new(type="ShaderNodeValToRGB")
        attr_elms = attr.get("color_ramp", {})
        for _ in range(len(col_rmp.color_ramp.elements), len(attr_elms)):
            col_rmp.color_ramp.elements.new(position=0)
        for element, attr_elm in zip(col_rmp.color_ramp.elements, attr_elms):
            element.position = attr_elm.get("position", 0)
            element.color = attr_elm.get("color", [1, 1, 1, 1])
        mat.node_tree.links.new(col_rmp.outputs["Color"], bsdf.inputs["Emission Color"])
        mat.node_tree.links.new(col_rmp.outputs["Alpha"], bsdf.inputs["Alpha"])
        drv = col_rmp.inputs["Fac"].driver_add("default_value").driver
        val = st.frame_end - st.frame_start + st.lifetime
        drv.expression = f"(frame - {st.frame_start}) / {val}"
    else:
        bsdf.inputs["Emission Color"].default_value = attr.get("color", [1, 1, 1, 1])
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


def set_bloom():
    scene = bpy.data.scenes["Scene"]
    scene.use_nodes = True
    nodes = scene.node_tree.nodes
    glare = nodes.new(type="CompositorNodeGlare")
    glare.glare_type = "BLOOM"
    glare.quality = "LOW"
    glare.location = 50, 200
    node1 = scene.node_tree.nodes["Render Layers"]
    node2 = scene.node_tree.nodes["Composite"]
    scene.node_tree.links.new(node1.outputs[0], glare.inputs[0])
    scene.node_tree.links.new(glare.outputs[0], node2.inputs[0])
    for area in bpy.data.screens["Layout"].areas:
        if area.ui_type == "VIEW_3D":
            area.spaces[0].shading.type = "RENDERED"
            area.spaces[0].shading.use_compositor = "ALWAYS"


class CFW_OT_make_fireworks(bpy.types.Operator):
    bl_idname = "object.make_fireworks"
    bl_label = "Make"
    bl_description = ""

    filepath: bpy.props.StringProperty()  # type: ignore[valid-type]

    def execute(self, context):  # noqa: PLR0915
        context.scene.eevee.use_bloom = True
        if "fireworks" in bpy.data.collections:
            bpy.data.collections.remove(bpy.data.collections["fireworks"])
            bpy.ops.outliner.orphans_purge(do_recursive=True)
        col = bpy.data.collections.new(name="fireworks")
        bpy.context.scene.collection.children.link(col)
        lc = bpy.context.view_layer.layer_collection.children["fireworks"]
        bpy.context.view_layer.active_layer_collection = lc
        toml = tomllib.loads((Path(__file__).parent / self.filepath).read_text())
        for name, attr in toml.items():
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
            for ps_name, ps_attr in attr.get("particle_systems", {}).items():
                bpy.ops.object.particle_system_add()
                ps = obj.particle_systems[-1]
                ps.name = ps_name
                st = ps.settings
                st.count = ps_attr["count"]
                m = re.match(ptn, ps_attr["frame_start"])
                bs = {"launch": launch, "explode": explode}[m.group(1)]
                st.frame_start = bs + ((m.group(2) == "+") * 2 - 1) * int(m.group(3))
                m = re.match(ptn, ps_attr["frame_end"])
                bs = {"launch": launch, "explode": explode}[m.group(1)]
                st.frame_end = bs + ((m.group(2) == "+") * 2 - 1) * int(m.group(3))
                st.lifetime = ps_attr["lifetime"]
                st.lifetime_random = 1
                st.render_type = "OBJECT"
                spark = make_spark(st, f"{name}_{ps_name}", ps_attr.get("material", {}))
                st.instance_object = spark
                st.particle_size = attr.get("particle_size", 0.05)
                st.factor_random = ps_attr.get("factor_random", 0)
                st.normal_factor = st.effector_weights.gravity = ps_attr.get("gravity", 1)
        bpy.context.scene.frame_set(launch)
        set_bloom()  # ブルームの設定
        # ワールドの背景色を黒に設定
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = [0, 0, 0, 1]
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
    bpy.types.Scene.filepath = bpy.props.StringProperty(default="./fireworks.toml")


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.filepath


if __name__ == "__main__":
    register()
