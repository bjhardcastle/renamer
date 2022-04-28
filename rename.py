import argparse
import os
import re
import shutil
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter.filedialog import askdirectory
from typing import Tuple

# define some globals here for visibility:

# starting dir in case folder select gui is opened - need not exist
initial_gui_dir = r"\\W10DTSM112719\neuropixels_data"

# path substrings to exclude from contents renaming - need not be exhaustive, can just save time instead of trying to open large non-text file
skip_content_edit_list = [".mp4", ".png", "motor-locs.csv", ".pkl"]

def parse_args() -> Tuple[str,str,str]:
    # parse input arguments and add helpful info
    parser = argparse.ArgumentParser(
        description="Find and replace in the names and content of files and their folders non-destructively: new folder is created with renamed contents, original folder is preserved. Intended for changing mouseID or sessionID in \\neuropixels_data. "
    )
    parser.add_argument("-folder", type=str, help="path to folder with files for renaming")
    parser.add_argument(
        "-old_string", type=str, help="replace all instances of this string in paths and within file contents"
    )
    parser.add_argument("-new_string", type=str, help="replace instances of old-string with this string ")
    args = parser.parse_args()

    # globals().update(vars(args))
    return args.folder, args.old_string, args.new_string


def main(rename_folder=None, old_str=None, new_str=None):

    # open folder selection
    root = tk.Tk()  # don't call more than one instance! use Toplevel for each window
    root.withdraw()

    if not rename_folder:

        # win1 = tk.Toplevel()
        # win1.withdraw()
        rename_folder = askdirectory(initialdir=initial_gui_dir, title="Choose folder to rename",)
        # win1.quit()
        # root.destroy()
        if not rename_folder:
            print("Folder selection cancelled: quitting...")
            quit()

    # suggest session number / mouse id substrings as a starting point for renaming
    try_str = re.search("[0-9]{10}_[0-9]{6}_[0-9]{8}", rename_folder)
    try_str = try_str[0] if try_str is not None else ""

    if not old_str or not new_str:
        old_str, new_str = replace_substr_dialog(try_str)

    destination_path = rename_folder.replace(old_str, new_str)
    if Path(destination_path).exists():
        check_before_overwrite_dialog(destination_path)  # quits if exists and user decides not to overwrite
    new_dir = rename_by_copy(old_str, new_str, rename_folder, recursive=True, copy_nontext_files=True)

    # if any parts of newstring and oldstring are the same, extract out the substring(s) which changed and run again to replace isolated instanced
    # this implementation assumes that the number of seperators in the string is consistent between new and old: should make sure this is the case,
    # else bad things could happen
    seperators_exp = "_+|-+|\s+|\.+"
    old_substr = re.split(seperators_exp, old_str)
    new_substr = re.split(seperators_exp, new_str)
    for idx, substr in enumerate(new_substr):
        if substr != old_substr[idx]:
            _ = rename_by_copy(old_substr[idx], substr, new_dir, recursive=True, copy_nontext_files=True)
    # TODO delete partially-renamed directories in destination folder after this last step: can't just compare subfolders in rename_folder and new_dir and delete exact matches, since they may be subfolders which weren't renamed at all

    # open new folder
    print(
        f"\nNew, renamed files are at {destination_path}. \nOriginal folder should be deleted manually after checking."
    )
    os.startfile(rename_folder)
    os.startfile(destination_path)


def rename_by_copy(old_str, new_str, old_dir, recursive=True, copy_nontext_files=True) -> str:

    strexp = "**/*" if recursive is True else "/*"

    rename_paths = Path(old_dir).glob(strexp)
    # for old_path in rename_paths:
    for old_path in progressbar(list(rename_paths), "Copying to new folder(s): ", 40):

        new_path = str(old_path).replace(old_str, new_str)
        if Path(new_path).suffix:
            Path(new_path).parents[0].mkdir(parents=True, exist_ok=True)
            try:
                already_copied = False
                if not any([sub in new_path for sub in skip_content_edit_list]):
                    # skip some large files
                    with open(old_path, "rt") as file:
                        x = file.read()
                    with open(new_path, "wt") as file:
                        x = x.replace(old_str, new_str)
                        file.write(x)
                        skip = True
            except UnicodeDecodeError:
                continue
            finally:
                if copy_nontext_files and not already_copied:
                    try:
                        shutil.copy2(old_path, new_path)  # copy with created/modified times preserved
                    except shutil.SameFileError:
                        continue
                    except PermissionError:
                        continue

        elif not Path(new_path).suffix:
            Path(new_path).mkdir(parents=True, exist_ok=True)

    return old_dir.replace(old_str, new_str)


def check_before_overwrite_dialog(path):
    import tkinter as tk

    def b1_callback():
        quit()  # exit program

    def b2_callback():
        win3.quit()  # exit gui and continue

    win3 = tk.Toplevel()
    label = tk.Label(win3, text="Contents may be overwritten:").grid(row=0, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)
    button_1 = tk.Button(win3, text="Cancel", command=b1_callback).grid(row=1, column=0, sticky=tk.EW, padx=5, pady=5)
    button_2 = tk.Button(win3, text="Continue", command=b2_callback).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
    # button_2.pack()
    win3.title("Folder exists")
    win3.mainloop()
    return None


def replace_substr_dialog(suggest_old="", suggest_new="") -> Tuple[str, str]:
    """ open dialog box, ask user old string to find in filepaths and replace with new string """

    if suggest_old + suggest_new == suggest_old:  # old str suggested, but not new
        suggest_new = "".join(suggest_old)  # ...so repeat old str in new box for easier editing

    # root = tk.Tk()  # don't call more than one instance! use Toplevel for each window
    # root.withdraw()
    win2 = tk.Toplevel()
    old_str = tk.StringVar()
    old_str.set(suggest_old)
    new_str = tk.StringVar()
    new_str.set(suggest_new)
    old_label = tk.Label(win2, text="old string").grid(row=0, column=0, sticky=tk.EW, padx=5, pady=5)
    new_label = tk.Label(win2, text="new string").grid(row=1, column=0, sticky=tk.EW, padx=5, pady=5)
    old_entry = tk.Entry(win2, textvariable=old_str, width=30).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
    new_entry = tk.Entry(win2, textvariable=new_str, width=30).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
    done_button = tk.Button(win2, text="Replace", command=win2.quit).grid(row=1, column=2, sticky=tk.EW, padx=5, pady=5)
    win2.bind("<Return>", lambda event: win2.quit())
    win2.title("Enter substring in path to replace")
    win2.mainloop()
    old_str, new_str = old_str.get(), new_str.get()
    return old_str, new_str


def progressbar(it, prefix="", size=60, file=sys.stdout):
    # from https://stackoverflow.com/a/34482761
    count = len(it)

    def show(j):
        x = int(size * j / count)
        file.write("%s[%s%s] %i/%i\r" % (prefix, "#" * x, "." * (size - x), j, count))
        file.flush()

    show(0)
    for i, item in enumerate(it):
        yield item
        show(i + 1)
    file.write("\n")
    file.flush()


if __name__ == "__main__":
    args = parse_args()
    main(*args)
    sys.exit()

