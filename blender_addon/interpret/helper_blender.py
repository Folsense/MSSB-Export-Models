from dataclasses import dataclass
from os.path import join, exists
from os import mkdir, listdir, rename
import typing
import numpy as np
import shutil, os, bpy

from .helper_vector import *
from .helper_c3 import SECTION_TYPES
from .helper_c3_export import *
from .helper_rotation import sqtTransform

bpy_imgs = {}

def transform_coord_to_blender(coord):
    return [coord[0], coord[2], -coord[1]]

def transform_uv_coord_to_blender(coord):
    return [coord[0], -coord[1]]

def do_blender_import(ctx, global_matrix, model_data, file_dir):
    base_collection = bpy.data.collections.new(os.path.basename(file_dir))
    ctx.scene.collection.children.link(base_collection)
    for group_name in model_data.exports:
        # group_name is defined in the template
        export:C3Export = model_data.exports[group_name]
        if SECTION_TYPES.ACT in export.sections and SECTION_TYPES.GEO in export.sections:
            transformMeshByBones(export)
        if SECTION_TYPES.GEO in export.sections:
            GEOData:C3GEOSection = export.sections[SECTION_TYPES.GEO]
            group_collection = bpy.data.collections.new(group_name)
            base_collection.children.link(group_collection)
            # scene = x3d.Scene()
            for GEOID, mesh in enumerate(GEOData.meshes):
                mesh_prefix = f"{group_name}_{GEOID}"
                mesh_collection = bpy.data.collections.new(mesh_prefix)
                group_collection.children.link(mesh_collection)

                coords = None
                texCoords = None
                normalCoords = None
                if mesh.positionList:
                    coords = [transform_coord_to_blender(coord) for coord in mesh.positionList]
                if mesh.normalList:
                    normalCoords = [transform_coord_to_blender(coord) for coord in mesh.normalList]
                if mesh.texCoordList:
                    texCoords = [transform_uv_coord_to_blender(l) for l in mesh.texCoordList]
                if mesh.colorList:
                    colorData = np.array(mesh.colorList)
                    colorData = [tuple(l) for l in colorData]
                for group_ind, group in enumerate(mesh.drawGroups):
                    draw_group_name = mesh_prefix+f"_{group_ind}"
                    faces = []
                    normals = []
                    color_attr_data = []
                    uv_coord_data = []
                    # make mesh
                    bpy_mesh = bpy.data.meshes.new(draw_group_name)
                    mesh_object = bpy.data.objects.new(draw_group_name, bpy_mesh)
                    mesh_collection.objects.link(mesh_object)
                    # get geometry data
                    for f in group.faces:
                        faces.append([v.positionInd for v in f.vertices])
                    # get normal data
                    if normalCoords:
                        for f in group.faces:
                            for v in f.vertices:
                                normals.append(normalCoords[v.normalInd])
                    # get uv coords
                    if texCoords:
                        for f in group.faces:
                            for v in f.vertices:
                                uv_coord_data.extend(texCoords[v.texCoordInd[0]])
                    # get vertex colors
                    if len(colorData):
                        for f in group.faces:
                            for v in f.vertices:
                                # if v.colorInd:
                                #     print(colorData[v.colorInd][3])
                                color_attr_data.extend(colorData[v.colorInd] if v.colorInd is not None else (255, 255, 255, 255))
                    # print(list(group.textureIndices.values()))
                    tex_ind = group.textureIndices.get(0)
                    if tex_ind is not None and SECTION_TYPES.texture in export.sections:
                        texture_part = export.sections[SECTION_TYPES.texture].part
                        img_path = os.path.join(file_dir, f"part {texture_part}/{tex_ind}.png")
                        mat_name = f"material_{group_name}_{GEOID}_{group_ind}"
                        material = create_blender_material(img_path, mat_name)
                        bpy_mesh.materials.append(material)
                    bpy_mesh.from_pydata(coords, [], faces)
                    if (len(color_attr_data)):
                        color_attribute = bpy_mesh.color_attributes.new("vertex_colors", "BYTE_COLOR", "CORNER")
                        color_attribute.data.foreach_set("color", color_attr_data)
                    if len(uv_coord_data):
                        uv_coords = bpy_mesh.uv_layers.new(name="UVMap")
                        uv_coords.data.foreach_set("uv", uv_coord_data)
                    if len(normals):
                        # I think this is probably wrong, dunno how to check that in blender so it's fine for now
                        bpy_mesh.has_custom_normals = True
                        bpy_mesh.use_auto_smooth = False
                        bpy_mesh.normals_split_custom_set_from_vertices(normals)
                    bpy_mesh.update()

def create_blender_material(img_path, name):
    if img_path not in bpy_imgs:
        bpy_imgs[img_path] = bpy.data.images.load(img_path)
    img = bpy_imgs[img_path]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material_output = material.node_tree.nodes.get('Material Output')
    principled_BSDF = material.node_tree.nodes.get('Principled BSDF')
    texImage_node = material.node_tree.nodes.new('ShaderNodeTexImage')
    texImage_node.image = img
    material.node_tree.links.new(texImage_node.outputs[0], principled_BSDF.inputs[0])
    material.node_tree.nodes["Principled BSDF"].inputs['Specular'].default_value = 0
    material.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.5
    return material