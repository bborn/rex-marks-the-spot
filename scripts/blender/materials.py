"""
Material and Shader Utilities

Create, configure, and apply materials using Blender's node-based system.
"""

import bpy
from typing import Optional, Tuple, Union


# Type aliases
Color3 = Tuple[float, float, float]
Color4 = Tuple[float, float, float, float]


def create_principled(
    name: str,
    color: Color4 = (0.8, 0.8, 0.8, 1.0),
    metallic: float = 0.0,
    roughness: float = 0.5,
    specular: float = 0.5,
    emission_color: Optional[Color4] = None,
    emission_strength: float = 0.0,
    alpha: float = 1.0,
    transmission: float = 0.0,
    ior: float = 1.45
) -> bpy.types.Material:
    """
    Create a Principled BSDF material.

    Args:
        name: Material name
        color: Base color (RGBA)
        metallic: Metallic value (0-1)
        roughness: Roughness value (0-1)
        specular: Specular/IOR Level value (0-1)
        emission_color: Emission color (RGBA), None for no emission
        emission_strength: Emission strength
        alpha: Material opacity (0-1)
        transmission: Glass/transmission amount (0-1)
        ior: Index of refraction for transmission

    Returns:
        The created material
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")

    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        # Note: "IOR Level" replaced "Specular" in Blender 4.0+
        if "IOR Level" in bsdf.inputs:
            bsdf.inputs["IOR Level"].default_value = specular
        elif "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = specular
        bsdf.inputs["Alpha"].default_value = alpha
        bsdf.inputs["Transmission Weight"].default_value = transmission
        bsdf.inputs["IOR"].default_value = ior

        if emission_color and emission_strength > 0:
            bsdf.inputs["Emission Color"].default_value = emission_color
            bsdf.inputs["Emission Strength"].default_value = emission_strength

    if alpha < 1.0 or transmission > 0:
        mat.blend_method = 'BLEND'

    return mat


def create_emission(
    name: str,
    color: Color4 = (1.0, 1.0, 1.0, 1.0),
    strength: float = 1.0
) -> bpy.types.Material:
    """
    Create an emission material.

    Args:
        name: Material name
        color: Emission color (RGBA)
        strength: Emission strength

    Returns:
        The created material
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    nodes.clear()

    # Create emission shader
    emission = nodes.new(type='ShaderNodeEmission')
    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = strength

    # Create output
    output = nodes.new(type='ShaderNodeOutputMaterial')

    links.new(emission.outputs["Emission"], output.inputs["Surface"])

    return mat


def create_glass(
    name: str,
    color: Color4 = (1.0, 1.0, 1.0, 1.0),
    roughness: float = 0.0,
    ior: float = 1.45
) -> bpy.types.Material:
    """
    Create a glass/transparent material.

    Args:
        name: Material name
        color: Glass tint color
        roughness: Surface roughness
        ior: Index of refraction

    Returns:
        The created material
    """
    mat = create_principled(
        name=name,
        color=color,
        roughness=roughness,
        transmission=1.0,
        ior=ior
    )
    mat.blend_method = 'BLEND'
    return mat


def create_metal(
    name: str,
    color: Color4 = (0.8, 0.8, 0.8, 1.0),
    roughness: float = 0.3
) -> bpy.types.Material:
    """
    Create a metallic material.

    Args:
        name: Material name
        color: Metal color
        roughness: Surface roughness

    Returns:
        The created material
    """
    return create_principled(
        name=name,
        color=color,
        metallic=1.0,
        roughness=roughness
    )


def create_toon(
    name: str,
    color: Color4 = (0.8, 0.8, 0.8, 1.0),
    smooth: float = 0.0,
    size: float = 0.5
) -> bpy.types.Material:
    """
    Create a toon/cel-shaded material.

    Args:
        name: Material name
        color: Base color
        smooth: Smooth factor (0 for sharp edges)
        size: Diffuse toon size

    Returns:
        The created material
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    # Create shader nodes
    diffuse = nodes.new(type='ShaderNodeBsdfDiffuse')
    diffuse.inputs["Color"].default_value = color

    shader_to_rgb = nodes.new(type='ShaderNodeShaderToRGB')
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    output = nodes.new(type='ShaderNodeOutputMaterial')

    # Configure color ramp for toon look
    color_ramp.color_ramp.interpolation = 'CONSTANT'
    color_ramp.color_ramp.elements[0].position = 0.0
    color_ramp.color_ramp.elements[1].position = 0.5

    # Link nodes
    links.new(diffuse.outputs["BSDF"], shader_to_rgb.inputs["Shader"])
    links.new(shader_to_rgb.outputs["Color"], color_ramp.inputs["Fac"])
    links.new(color_ramp.outputs["Color"], output.inputs["Surface"])

    return mat


def assign(
    obj: Union[bpy.types.Object, str],
    material: Union[bpy.types.Material, str],
    slot: int = 0
) -> None:
    """
    Assign a material to an object.

    Args:
        obj: Object or object name
        material: Material or material name
        slot: Material slot index (0 = first slot)
    """
    if isinstance(obj, str):
        obj = bpy.data.objects.get(obj)

    if isinstance(material, str):
        material = bpy.data.materials.get(material)

    if obj.data.materials:
        if slot < len(obj.data.materials):
            obj.data.materials[slot] = material
        else:
            obj.data.materials.append(material)
    else:
        obj.data.materials.append(material)


def get_material(name: str) -> Optional[bpy.types.Material]:
    """
    Get a material by name.

    Args:
        name: Material name

    Returns:
        The material or None if not found
    """
    return bpy.data.materials.get(name)


def copy_material(
    material: Union[bpy.types.Material, str],
    new_name: str
) -> bpy.types.Material:
    """
    Create a copy of a material.

    Args:
        material: Material or material name to copy
        new_name: Name for the new material

    Returns:
        The copied material
    """
    if isinstance(material, str):
        material = bpy.data.materials.get(material)

    new_mat = material.copy()
    new_mat.name = new_name
    return new_mat


def add_texture_node(
    material: Union[bpy.types.Material, str],
    texture_path: str,
    input_name: str = "Base Color",
    colorspace: str = "sRGB"
) -> bpy.types.ShaderNodeTexImage:
    """
    Add an image texture to a material.

    Args:
        material: Material or material name
        texture_path: Path to the image file
        input_name: Which input to connect to
        colorspace: Color space ('sRGB', 'Non-Color', etc.)

    Returns:
        The texture node
    """
    if isinstance(material, str):
        material = bpy.data.materials.get(material)

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Find the principled BSDF or output
    bsdf = None
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            bsdf = node
            break

    if not bsdf:
        return None

    # Create texture node
    tex_node = nodes.new(type='ShaderNodeTexImage')
    tex_node.image = bpy.data.images.load(texture_path)
    tex_node.image.colorspace_settings.name = colorspace

    # Position node
    tex_node.location = (bsdf.location.x - 300, bsdf.location.y)

    # Connect to input
    if input_name in bsdf.inputs:
        links.new(tex_node.outputs["Color"], bsdf.inputs[input_name])

    return tex_node


def add_normal_map(
    material: Union[bpy.types.Material, str],
    normal_path: str,
    strength: float = 1.0
) -> bpy.types.ShaderNodeNormalMap:
    """
    Add a normal map to a material.

    Args:
        material: Material or material name
        normal_path: Path to the normal map image
        strength: Normal map strength

    Returns:
        The normal map node
    """
    if isinstance(material, str):
        material = bpy.data.materials.get(material)

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    bsdf = None
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            bsdf = node
            break

    if not bsdf:
        return None

    # Create image texture
    tex_node = nodes.new(type='ShaderNodeTexImage')
    tex_node.image = bpy.data.images.load(normal_path)
    tex_node.image.colorspace_settings.name = 'Non-Color'

    # Create normal map node
    normal_node = nodes.new(type='ShaderNodeNormalMap')
    normal_node.inputs["Strength"].default_value = strength

    # Position nodes
    tex_node.location = (bsdf.location.x - 500, bsdf.location.y - 200)
    normal_node.location = (bsdf.location.x - 200, bsdf.location.y - 200)

    # Connect
    links.new(tex_node.outputs["Color"], normal_node.inputs["Color"])
    links.new(normal_node.outputs["Normal"], bsdf.inputs["Normal"])

    return normal_node


def list_materials() -> list:
    """
    List all materials in the blend file.

    Returns:
        List of material names
    """
    return [mat.name for mat in bpy.data.materials]
