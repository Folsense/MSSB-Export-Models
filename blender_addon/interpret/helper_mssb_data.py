# This is a stripped-down version of helper_mssb_data from the extractor
# We can't simply include the version of the file from the extractor directory
# because this directory must work independently from it

from __future__ import annotations
from typing import NamedTuple, Union
from struct import pack, unpack, calcsize
from os.path import dirname, exists
from os import makedirs

class DataBytesInterpreter:
    @classmethod
    @property
    def SIZE_OF_STRUCT(cls):
        return calcsize(cls.DATA_FORMAT)

    @classmethod
    def parse_bytes_static(cls, all_bytes:bytearray, offset:int, format_str:str):
        struct_size = calcsize(format_str)
        these_bytes = all_bytes[offset:offset+struct_size]

        if len(these_bytes) != struct_size:
            raise ValueError(f'Ran out of bytes to interpret in {cls.__name__}, needed {cls.SIZE_OF_STRUCT}, received {len(these_bytes)}')

        return unpack(format_str, these_bytes)

    def parse_bytes(self, all_bytes:bytearray, offset:int):
        return self.parse_bytes_static(all_bytes, offset, self.DATA_FORMAT)

def get_parts_of_file(file_bytes:bytearray):
    found_inds = []

    i = 0
    while True:
        new_ind = int.from_bytes(file_bytes[i:i+4], 'big')
        i += 4
        
        if new_ind == 0:
            break

        if len(found_inds) != 0 and new_ind <= found_inds[-1]:
            break

        found_inds.append(new_ind)

    return found_inds

def float_from_fixedpoint(a:int, shift:int):
    return a / (1 << shift)

def ensure_dir(path:str):
    if not (path == '' or path in "\\/" or exists(path)):
        makedirs(path)

def write_text(s:str, file_path:str):
    write_bytes(s.encode(), file_path)

def write_bytes(b:bytes, file_path:str):
    ensure_dir(dirname(file_path))
    with open(file_path, "wb") as f:
        f.write(b)

def get_c_str(b: bytes, offset: int, max_length: Union[int, None] = 100):
    s = ""
    n_offset = offset
    while b[n_offset] != 0:
        s += chr(b[n_offset])

        if max_length != None and len(s) >= max_length:
            break

        n_offset += 1

    return s
