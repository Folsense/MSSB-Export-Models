from helper_mssb_data import DataEntry, RollingDecompressor, ensure_dir, write_bytes, ArchiveDecompressor, get_parts_of_file, write_text
from helper_c3 import SECTION_TEMPLATES
from os.path import join, exists
from run_file_discovery import discover_US_files, discover_beta_files, discover_JP_files, discover_EU_files, discover_family_files
import json, progressbar
from run_draw_pic import draw_pic
from helper_file_system import *

def mean(x):
    return sum(x) // len(x) 

def interpret_US():
    print('Looking at US files...')
    return interpret_version(US_OUTPUT_FOLDER, US_RESULTS_FILE, US_ZZZZ_FILE, discover_US_files, US_CUSTOM_FILENAMES)
def interpret_JP():
    print('Looking at JP files...')
    return interpret_version(JP_OUTPUT_FOLDER, JP_RESULTS_FILE, JP_ZZZZ_FILE, discover_JP_files, JP_CUSTOM_FILENAMES)
def interpret_EU():
    print('Looking at EU files...')
    return interpret_version(EU_OUTPUT_FOLDER, EU_RESULTS_FILE, EU_ZZZZ_FILE, discover_EU_files, EU_CUSTOM_FILENAMES)
def interpret_BETA():
    print('Looking at Beta files...')
    return interpret_version(BETA_OUTPUT_FOLDER, BETA_RESULTS_FILE, BETA_ZZZZ_FILE, discover_beta_files, BETA_CUSTOM_FILENAMES)
def interpret_family():
    print('Looking at family files...')
    return interpret_version(FAMILY_OUTPUT_FOLDER, FAMILY_RESULTS_FILE, FAMILY_ZZZZ_FILE, discover_family_files, FAMILY_CUSTOM_FILENAMES)

def main():
    interpret_US()
    interpret_JP()
    interpret_EU()
    interpret_BETA()
    interpret_family()
    
def interpret_version(output_folder:str, results_path:str, zzzz_file:str, discovery_method, file_name_path:str):
    REFERENCED_FOLDER = join(output_folder, 'Referenced files')
    UNREFERENCED_FOLDER = join(output_folder, 'Unreferenced files')
    RAW_FOLDER = join(output_folder, 'Raw files')
    ADGCFORMS_FOLDER = join(output_folder, 'AdGCForms')

    if not exists(zzzz_file):
        return

    ensure_dir(output_folder)

    with open(zzzz_file, 'rb') as f:
        ZZZZ_DAT = f.read()
 
    if exists(results_path): 
        with open(results_path, 'r') as f:
            found_files = json.load(f)
    else:
        found_files = discovery_method()
        draw_pic(zzzz_file, results_path, join(output_folder, "results.png"))
        
    if exists(file_name_path):
        with open(file_name_path, 'r') as f:
            file_names = json.load(f)
        offset_to_name = {int(x['Location'], 16): x['Name'] for x in file_names}
        offset_to_format = {int(x['Location'], 16): x['Format'] for x in file_names if 'Format' in x}
    else:
        offset_to_name = {}
        offset_to_format = {}

    def process_files(files, folder):
        for json_entry in progressbar.progressbar(files):
            entry = DataEntry.from_dict(json_entry)
            if entry.file != zzzz_file:
                continue

            location = f"{entry.disk_location:08X}"
            default_folder_name = location
            renamed_folder = offset_to_name.get(entry.disk_location, default_folder_name)

            this_folder = join(folder, renamed_folder)
            ensure_dir(this_folder)
            output_file_name = join(this_folder, f"{location}.dat")

            # If we know the format of this file, export a .fmt file alongside it
            # the name of this file is arbitrary, meant for human readability
            this_format = offset_to_format.get(entry.disk_location, None)
            output_format_file_name = None
            if this_format:
                output_format_file_name = join(this_folder, f"{this_format.lower()}.fmt")
                format_data = SECTION_TEMPLATES.get(this_format, None)

            if folder == REFERENCED_FOLDER:
                if not exists(output_file_name):
                    this_data = ZZZZ_DAT[entry.disk_location : entry.disk_location + entry.compressed_size]
                    if len(this_data) == entry.compressed_size:
                        decompressed_bytes = ArchiveDecompressor(ZZZZ_DAT[entry.disk_location:], entry.lookback_bit_size, entry.repetition_bit_size, entry.original_size).decompress()

                        write_bytes(decompressed_bytes, output_file_name)
                        if this_format:
                            write_text(json.dumps(format_data), output_format_file_name)

            elif folder == UNREFERENCED_FOLDER:
                mean = lambda x : sum(x) // len(x) 
                if not exists(output_file_name):
                    decompressor = RollingDecompressor(ZZZZ_DAT[entry.disk_location:], entry.lookback_bit_size, entry.repetition_bit_size)
                    parts_of_file = get_parts_of_file(decompressor)
                    
                    if len(parts_of_file) > 1:
                        if len(parts_of_file) > 0 and parts_of_file[0] == 80_92_000: # base address is a c3 file
                            parts_of_file = []
                        else:
                            # calculate the average size of a section, and decompress that much past the last part start
                            # hopefully should allow for faster decompressing
                            average_size = mean([parts_of_file[x+1] - parts_of_file[x] for x in range(len(parts_of_file) - 1)])
                            try:
                                decompressed_bytes = decompressor[0:parts_of_file[-1] + average_size]
                            except:
                                decompressed_bytes = decompressor
                    else:
                        decompressed_bytes = decompressor

                    write_bytes(decompressor.outputdata, output_file_name)
                    if this_format:
                            write_text(json.dumps(format_data), output_format_file_name)

            elif ADGCFORMS_FOLDER:
                if not exists(output_file_name):

                    if entry.compression_flag == 0:
                        these_bytes = ZZZZ_DAT[entry.disk_location : entry.disk_location + entry.original_size]
                    else:
                        these_bytes = ArchiveDecompressor(ZZZZ_DAT[entry.disk_location:], entry.lookback_bit_size, entry.repetition_bit_size, entry.original_size).decompress()

                    write_bytes(these_bytes, output_file_name)
                    if this_format:
                            write_text(json.dumps(format_data), output_format_file_name)

            elif folder == RAW_FOLDER:
                if not exists(output_file_name):
                    these_bytes = ZZZZ_DAT[entry.disk_location:entry.disk_location+entry.compressed_size]

                    # interpret_bytes(these_bytes, this_folder, this_format)

                    write_bytes(these_bytes, output_file_name)
                    if this_format:
                            write_text(json.dumps(format_data), output_format_file_name)

    print("Interpreting referenced compressed files... (should take about 10 minutes)")
    process_files(found_files['GameReferencedCompressedFiles'], REFERENCED_FOLDER)

    print("Interpreting unreferenced compressed files... (this will take 30-45 minutes)")
    process_files(found_files['UnreferencedCompressedFiles'], UNREFERENCED_FOLDER)

    print("Interpreting AdGCForms files...")
    process_files(found_files['AdGCForms'], ADGCFORMS_FOLDER)

    print("Interpreting referenced raw files...")
    process_files(found_files['GameReferencedRawFiles'], RAW_FOLDER)

if __name__ == "__main__": main()