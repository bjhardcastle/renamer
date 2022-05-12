import json
import os
import sys
import shutil
import time
import re
import tkinter as tk
from pathlib import Path
from tkinter.filedialog import askopenfilenames, askdirectory
import logging

LOG_FILENAME = 'filecopy.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',)

# # NP1
# Sync: W10DTSM18306
# Z: \\W10DTSM18306\neuropixels_data
# Stim: W10DTSM118294
# Videomon: W10DTSM18278
# Acquisition: W10DT05501

exp_dir_root = Path("//W10DTSM18306/neuropixels_data")  # Z:\
detination_img_name = "surface-image"

root_path_list = ["C:", "//W10DTSM112722/C"]

img_output_dir = Path("//W10DTSM18278/c/ProgramData/AIBS_MPE/mvr/data")
pkl_output_dir = Path("//W10DTSM118294/c/ProgramData/AIBS_MPE/camstim/data")

copy_flag = True


def main(rename_folder=None, old_str=None, new_str=None):

    # open folder selection
    root = tk.Tk()  # don't call more than one instance! use Toplevel for each window
    root.withdraw()
    exp_folder_obj = Path(askdirectory(
        initialdir=exp_dir_root, title="Choose session folder"))

    # extract session / mouse id /date substrings
    str_match_obj = re.search(
        "[0-9]{10}_[0-9]{6}_[0-9]{8}", str(exp_folder_obj))
    exp_str = str_match_obj[0]
    session_str, mouse_str, date_str = exp_str.split('_')

    # extract start/end times
    platform_json = exp_folder_obj / (exp_str + '_platformD1.json')
    with open(str(platform_json)) as f:
        jdata = json.load(f)
    start_time = int(jdata['workflow_start_time'][:12])
    end_time = int(jdata['platform_json_save_time'][:12])  # ! correct?

    # auto find img and pkl files created during experiment
    pkl_path_list = get_files_created_between(
        pkl_output_dir, "*.pkl", start_time, end_time)
    # img_path_list = get_files_created_between(
    #     img_output_dir, "*", start_time, end_time)

    # manual choose img and pkl files
    # pkl_path_list = askopenfilenames(filetypes=(("pkl file", "*.pkl"), ("All files", "*.*")), initialdir=pkl_output_dir, title="Choose pkl files")
    img_path_list = askopenfilenames(filetypes=[
        ("image files", "*.png"),
        ("image files", "*.bmp"),
        ("image files", "*.jpg"),
        ("image files", "*.jpeg"),
        # ("All files", "*.*"),
    ], initialdir=img_output_dir, title="Choose experimet images (any order), or cancel if none taken")

    # copy over imgs
    def new_img_path(
        a): return f"{exp_folder_obj}\\{exp_str}_{detination_img_name}{a}"
    for idx, file_str in enumerate(progressbar(sorted(img_path_list), "copying image files", 40)):
        file_obj = Path(file_str)
        if copy_flag:
            orig_path = str(file_obj)
            new_path = new_img_path(
                str(idx+1) + file_obj.suffix)
            try:
                # copy with created/modified times preserved
                shutil.copy2(orig_path, new_path)
                logging.info(f"{orig_path} copied to {new_path}")
            except shutil.SameFileError as e:
                logging.info(e, exc_info=True)
                pass
        else:
            print(f"\n{Path(orig_path).name}\n->{new_path}")

    # copy over pkls
    for file_path in progressbar(pkl_path_list, "copying .pkl files", 40):

        file_strs = []

        if "opto" in file_path.name:
            file_strs = [f"{exp_str}.opto.pkl"]
        elif "mapping" in file_path.name:
            file_strs = [f"{exp_str}.mapping.pkl"]
        elif "behavior" in file_path.name:
            file_strs = [f"{exp_str}.behavior.pkl",
                         file_path.name]
        else:
            file_strs = [file_path.name]

        def new_pkl_path(a): return str(exp_folder_obj) + \
            "\\" + a

        for file_str in file_strs:
            orig_path = str(file_path)
            new_path = new_pkl_path(file_str)
            if copy_flag:
                try:
                    # copy with created/modified times preserved
                    shutil.copy2(orig_path, new_path)
                    logging.info(f"{orig_path} copied to {new_path}")
                except shutil.SameFileError:
                    logging.info(e, exc_info=True)
                    pass
            else:
                print(f"\n{Path(orig_path).name}\n->{new_path}")


def get_created_timestamp_from_file(file, date_format='%Y%m%d%H%M'):

    t = os.path.getctime(str(file))
    # t = os.path.getmtime(file)
    t = time.localtime(t)
    t = time.strftime(date_format, t)

    return t


def get_files_created_between(dir, strsearch, start, end):
    """"Returns a generator of Path objects"""
    path_select_list = []
    paths_all = Path(dir).glob(strsearch)
    for path in paths_all:
        time_created = int(get_created_timestamp_from_file(path))
        if time_created in range(start, end):
            path_select_list.append(path)

    return path_select_list


def progressbar(it, prefix="", size=60, file=sys.stdout):
    # from https://stackoverflow.com/a/34482761
    count = len(it)

    def show(j):
        x = int(size * j / (count if count != 0 else 1))
        file.write("%s[%s%s] %i/%i\r" %
                   (prefix, "#" * x, "." * (size - x), j, count))
        file.flush()

    show(0)
    for i, item in enumerate(it):
        yield item
        show(i + 1)
    file.write("\n")
    file.flush()


if __name__ == "__main__":
    args = []  # parse_args()
    main(*args)
    # sys.exit()
    print("Finished. Check log for files copied")
