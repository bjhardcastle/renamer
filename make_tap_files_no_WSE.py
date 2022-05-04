import json
import os
import shutil
import time
import tkinter as tk
from pathlib import Path
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import askdirectory
import logging

LOG_FILENAME = 'filecopy.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',)

session_id = "0000000000"  # use dummy id to distinguish from actual exps
detination_img_name = "surface-image3"  # additional substrings added later

root_path_list = ["C:", "//W10DTSM112722/C"]
stereoviewer_output_dir = "users/svc_neuropix/cv3dImages"
motor_locs_filepath = "//W10DTSM112722/MPM_data/log.csv"

destination_dir = Path("//W10DTSM112719/neuropixels_data")  # == Z:\


def main():
    for root_path in root_path_list:
        root_path_obj = Path(root_path)

        folder_path_obj = None
        if root_path_obj.exists():
            folder_path_obj = root_path_obj / stereoviewer_output_dir  # concatenate paths

    if folder_path_obj is None:
        raise FileNotFoundError(
            f"network drive is not available or we're on the wrong computer")

    if not folder_path_obj.exists():
        raise FileNotFoundError(
            f"cannot access {folder_path_obj}: may be a permissions issue")

    # open file browser, get first img filename
    root = tk.Tk()  # don't call more than one instance! use Toplevel for each window
    root.withdraw()
    win1 = tk.Toplevel()
    win1.withdraw()
    filename_first = askopenfilename(
        filetypes=(("image file", "*.png"), ("All files", "*.*")),
        initialdir=folder_path_obj,
        title="Choose first image",
    )
    win1.quit()

    # open dialog box, ask user for mouse id number
    win2 = tk.Toplevel()
    mouse_str = tk.StringVar()
    label = tk.Label(win2, text="mouse_id").grid(row=0, column=0)
    entry = tk.Entry(win2, textvariable=mouse_str).grid(row=0, column=1)
    button = tk.Button(win2, text="Accept",
                       command=win2.quit).grid(row=0, column=2)
    win2.bind("<Return>", lambda event: win2.quit())
    win2.mainloop()
    mouse_id = mouse_str.get()

    # in case nothing was entered
    if mouse_id == "":
        mouse_id = None

    ## back to dealing with opening images:
    # in case two imgs were captured, re-create the second filename
    if "_left" in str(filename_first):
        filename_second = filename_first.replace("_left", "_right")
        leftright_first = "left"
        leftright_second = "right"
    elif "_right" in str(filename_first):
        filename_second = filename_first.replace("_right", "_left")
        leftright_first = "right"
        leftright_second = "left"

    # make dummy folder for this mouse/exp
    date_str = get_created_date_from_file(filename_first)
    dummy_str = get_dummy_str(
        exp_date=date_str, session_id=session_id, mouse_id=mouse_id)
    dummy_path_obj = Path(destination_dir, dummy_str)
    if not dummy_path_obj.exists():
        os.mkdir(dummy_path_obj)

    # create right img filename
    filenames = {leftright_first: filename_first,
                 leftright_second: filename_second}

    # copy img files to new directory
    for leftright, src_filename in filenames.items():

        new_file_obj = dummy_path_obj / \
            (dummy_str + "_" + detination_img_name + "_" + leftright + ".png")
        if Path(src_filename).exists():
            shutil.copy2(src_filename, new_file_obj)
            print("Copied : " + src_filename)
            print("To     : " + str(new_file_obj))
            logging.info(f"{src_filename} copied to {new_file_obj}")

    # copy newscale motor coords
    if Path(motor_locs_filepath).exists():
        new_path = dummy_path_obj / (dummy_str + ".motor-locs.csv")
        shutil.copy2(motor_locs_filepath, new_path)
        logging.info(f"{motor_locs_filepath} copied to {new_path}")
    # TODO copy only recent csv entries

    # make a dummy platform json
    json_data = {"rig_id": "NP.0",
                 "note": "dummy file for habs which ran without WSE"}
    json_path = Path(dummy_path_obj / (dummy_str + "_platformD1.json"))
    with open(json_path, "w") as f:
        json.dump(json_data, f, sort_keys=True, indent=4)

    # finish, open folder with copied/dummy files
    print("\nFile transfer complete. Check log for files copied.\n")
    os.startfile(dummy_path_obj)


def get_dummy_str(session_id=None, mouse_id=None, exp_date=None) -> str:
    """ spoofed folder or file name root """
    if session_id is None:
        session_id = "xxxxxxxxxx"
    if mouse_id is None:
        mouse_id = "xxxxxx"
    if exp_date is None:
        time_now = time.localtime()
        exp_date = time.strftime("%Y%m%d", time_now)  # yyyymmdd
    return "_".join([session_id, mouse_id, exp_date])


def get_created_date_from_file(file: str, date_format="%Y%m%d") -> str:
    """ from ecephys_probe_alignment_ccb/data_io.py """

    t = os.path.getctime(file)  # creation time on Win only
    # t = os.path.getmtime(file) # modified time
    time_created = time.localtime(t)
    return time.strftime(date_format, time_created)


if __name__ == "__main__":
    main()

# TODO package for deployment
