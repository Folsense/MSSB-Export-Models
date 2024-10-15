# THIS CLASS (SECTION_TYPES) IS DUPLICATED IN blender_addon/helper_c3.py
# ANY CHANGES SHOULD BE MADE IN BOTH LOCATIONS
class SECTION_TYPES():
    ACT = 0
    GEO = 1
    texture = 2
    collision = 3
    type_count = 4

SECTION_TEMPLATES:dict[str, dict[int, int]] = {
    'Stadium': {
        'stadium': {
            SECTION_TYPES.ACT: 0,
            SECTION_TYPES.GEO: 3,
            SECTION_TYPES.texture: 5,
            SECTION_TYPES.collision: 2
        },
        'backdrop': {
            SECTION_TYPES.ACT: 1,
            SECTION_TYPES.GEO: 4
        },
        'other': {
            SECTION_TYPES.ACT: 6,
            SECTION_TYPES.ACT: 7,
            SECTION_TYPES.GEO: 8,
            SECTION_TYPES.GEO: 9,
            SECTION_TYPES.texture: 10,
            SECTION_TYPES.collision: 11
        }
    }
}