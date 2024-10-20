import importlib

if 'bpy' in locals():
    if "interpret_c3" in locals():
        importlib.reload(interpret_c3)
else:
    from .interpret import interpret_c3

import bpy, bpy_extras

from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        orientation_helper,
        axis_conversion,
        path_reference_mode,
        )

bl_info = {
    "name": "MSSB Model Import",
    "blender": (3, 4, 0),
    "location": "File > Import",
    "category": "Import-Export",
}

@orientation_helper(axis_forward='Z', axis_up='Y')
class ImportMSSBModel(bpy.types.Operator, ImportHelper):
    bl_idname = "mssb.model_import"
    bl_label = "MSSB model file (.dat)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".dat"
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})

    def execute(self, context):
        global_matrix = axis_conversion(from_forward=self.axis_forward,
                                        from_up=self.axis_up,
                                        ).to_4x4()
        return interpret_c3.init_blender_import(context, self.filepath, global_matrix)

    def draw(self, context):
        pass

def menu_func_import(self, context):
    self.layout.operator(ImportMSSBModel.bl_idname, text="MSSB model file (.dat)")

def register():
    bpy.utils.register_class(ImportMSSBModel)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)  # Adds the new operator to an existing menu.

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(ImportMSSBModel)

# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()