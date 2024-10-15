from os import rename
from run_extract_Texture import export_images
from run_extract_Model import *
from run_extract_Actor import export_actor
from helper_c3 import SECTION_TYPES, SECTION_TEMPLATES
from helper_c3_export import *
from run_extract_Collision import export_collision
from helper_x3d import x3d_export
import traceback, os, shutil
import bpy

def try_export_texture(b, new_out_folder, part) -> tuple[bool, str, dict]:
    try:
        output_text = ''
        base_images = export_images(b, part)
        assert len(base_images.images) > 0
        output_text += f"Part {part} interpreted as textures.\n"
        base_images.write_images_to_folder(new_out_folder)
        base_images.write_mtl_file(join(new_out_folder, 'mtl.mtl'), "")
        section_data = C3TextureSection(part)
        return 1, output_text, section_data
    except:
        traceback.print_exc()
        return 0, '', None

def try_export_model(b, new_out_folder, part) -> tuple[bool, str, dict]:
    try:
        output_text = ''
        section_data = export_model(b, new_out_folder, part)
        output_text += f"Part {part} interpreted as model.\n"
        return 1, output_text, section_data
    except:
        traceback.print_exc()
        return 0, '', None

def try_export_actor(b, new_out_folder, part) -> tuple[bool, str, dict]:
    try:
        output_text = ''
        section_data = export_actor(b, new_out_folder, part)
        output_text += f"Part {part} interpreted as actor.\n"
        return 1, output_text, section_data
    except:
        traceback.print_exc()
        return 0, '', None

def try_export_dummy(b, new_out_folder, part) -> tuple[bool, str, dict]:
    return 0, '', None

def try_export_collision(b, new_out_folder, part) -> tuple[bool, str, dict]:
    try:
        output_text = ''
        export_collision(b, new_out_folder, 0)
        section_data = C3CollisionSection()
        output_text += f"Part {part} interpreted as collision.\n"
        return 1, output_text, section_data
    except:
        traceback.print_exc()
        return 0, '', None

export_methods = {
    SECTION_TYPES.texture: try_export_texture,
    SECTION_TYPES.GEO: try_export_model,
    SECTION_TYPES.ACT: try_export_actor,
    SECTION_TYPES.collision: try_export_collision
}

def interpret_bytes(b:bytearray, output_folder:str, format:str):
    parts_of_file = get_parts_of_file(b)
    output_text = f"{len(parts_of_file)} {'part' if len(parts_of_file) == 1 else 'parts'} of file.\n"
    offsets_text = "Offsets of parts: " + ", ".join([hex(offset) for offset in parts_of_file]) + "\n"
    output_text += offsets_text

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    any_outputs = False
    section_template = SECTION_TEMPLATES.get(format, None)
    export_groups = None
    if section_template is not None:
        export_groups = C3ExportGroup()
        for group_name in section_template:
            exportObj = C3Export(group_name)
            export_groups.exports[group_name] = exportObj

    # interpret the parts of the file
    if len(parts_of_file) > 0 and parts_of_file[0] == 80_92_000: # base address is a c3 file
        parts_of_file = []
    for part in [x for x in range(len(parts_of_file))]:
        # print(f'extracting part {part}')
        any_outputs_in_this_part = False
        
        new_out_folder = join(output_folder, f"part {part}")
        if not os.path.exists(new_out_folder):
            os.mkdir(new_out_folder)

        this_group = None

        if section_template is None:
            possible_section_types = list(range(SECTION_TYPES.type_count))
        else:
            possible_section_types = []
            for group in section_template:
                for s_type in section_template[group]:
                    if section_template[group][s_type] == part:
                        possible_section_types = [s_type]
                        this_group = group

        for s_type in possible_section_types:
            success, output_str, data = export_methods[s_type](b, new_out_folder, part)
            if success:
                any_outputs = any_outputs_in_this_part = True
                output_text += output_str
                if this_group is not None:
                    export_groups.exports[this_group].sections[s_type] = data

        if not any_outputs_in_this_part:
            shutil.rmtree(new_out_folder)

    if any_outputs:
        write_text(output_text, join(output_folder, "notes.txt"))
    else:
        write_text(output_text + "No output types found.\n", join(output_folder, "notes.txt"))

    # if section_template is not None:
    #     # obj_export(output_folder, export_groups)
    #     x3d_export(output_folder, export_groups)
    return export_groups

def do_blender_import(folder_name):
    return ""