import argparse
import os
import re
import shutil
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter.filedialog import askdirectory


def main(args=[]):

    if args:
        # parse input arguments
        parser = argparse.ArgumentParser(
            description="Find and replace in the names and content of files and their folders non-destructively: new folder is created with renamed contents, original folder is preserved. Intended for changing mouseID or sessionID in \\neuropixels_data. "
        )
        parser.add_argument("-folder", type=str, help="path to folder with files for renaming")
        parser.add_argument(
            "-old_string", type=str, help="replace all instances of this string in paths and within file contents"
        )
        parser.add_argument("-new_string", type=str, help="replace instances of old-string with this string ")
        args = parser.parse_args(args)
        rename_folder, old_str, new_str = args.folder, args.old_string, args.new_string
        # globals().update(vars(args))

    # if args == []:
    else:
        # open folder selection
        root = tk.Tk()  # don't call more than one instance! use Toplevel for each window
        root.withdraw()
        win1 = tk.Toplevel()
        win1.withdraw()
        rename_folder = askdirectory(initialdir=r"\\W10DTSM112719\neuropixels_data", title="Choose folder to rename",)
        win1.quit()
        if not rename_folder:
            print("Folder selection cancelled: quitting...")
            quit()

        # suggest session number / mouse id substrings as a starting point for renaming
        try_str = re.search("[0-9]{10}_[0-9]{6}_[0-9]{8}", rename_folder)
        try_str = try_str[0] if try_str is not None else ""

        old_str, new_str = replace_substr_dialog(try_str)

    destination_path = rename_folder.replace(old_str, new_str)
    new_dir = rename_by_copy(old_str, new_str, rename_folder, recursive=True, copy_nontext_files=True)

    # if any parts of newstring and oldstring are the same, extract out the substring(s) which changed and run again to replace isolated instanced
    seperators_exp = "_+|-+|\s+|\.+"
    old_substr = re.split(seperators_exp, old_str)
    new_substr = re.split(seperators_exp, new_str)
    for idx, substr in enumerate(new_substr):
        if substr != old_substr[idx]:
            _ = rename_by_copy(old_substr[idx], substr, new_dir, recursive=True, copy_nontext_files=True)

    # open new folder
    os.startfile(destination_path)
    print(f"Finished. New, renamed files are at {destination_path}. \nOriginal folder can be deleted manually.")


def rename_by_copy(old_str, new_str, old_dir, recursive=True, copy_nontext_files=True) -> str:

    strexp = "**/*" if recursive is True else "/*"

    rename_paths = Path(old_dir).glob(strexp)
    # for old_path in rename_paths:
    for old_path in progressbar(list(rename_paths), "Copying to new folder(s): ", 40):
        time.sleep(0.1)  # any code you need

        new_path = str(old_path).replace(old_str, new_str)
        if Path(new_path).suffix:
            Path(new_path).parents[0].mkdir(parents=True, exist_ok=True)
            try:
                skip = False
                if not any([sub in new_path for sub in [".mp4", ".png", "motor-locs.csv", ".pkl"]]):
                    # skip some large files
                    with open(old_path, "rt") as file:
                        x = file.read()
                    with open(new_path, "wt") as file:
                        x = x.replace(old_str, new_str)
                        file.write(x)
                        skip = True
            finally:
                if copy_nontext_files and not skip:
                    try:
                        shutil.copy2(old_path, new_path)  # copy with created/modified times preserved
                    except shutil.SameFileError:
                        continue
                    except PermissionError:
                        continue

        elif not Path(new_path).suffix:
            Path(new_path).mkdir(parents=True, exist_ok=True)

    return old_dir.replace(old_str, new_str)


def replace_substr_dialog(suggest_old="", suggest_new="") -> (str, str):
    """ open dialog box, ask user old string to find in filepaths and replace with new string """

    if suggest_old + suggest_new == suggest_old:  # old str suggested, but not new
        suggest_new = "".join(suggest_old)  # ...so repeat old str in new box for easier editing

    root = tk.Tk()  # don't call more than one instance! use Toplevel for each window
    root.withdraw()
    win2 = tk.Toplevel()
    old_str = tk.StringVar()
    old_str.set(suggest_old)
    new_str = tk.StringVar()
    new_str.set(suggest_new)
    old_label = tk.Label(win2, text="old string").grid(row=0, column=0)
    new_label = tk.Label(win2, text="new string").grid(row=1, column=0)
    old_entry = tk.Entry(win2, textvariable=old_str, width=30).grid(row=0, column=1)
    new_entry = tk.Entry(win2, textvariable=new_str, width=30).grid(row=1, column=1)
    old_button = tk.Button(win2, text="Replace", command=win2.quit).grid(row=1, column=2)
    win2.bind("<Return>", lambda event: win2.quit())
    win2.title("Enter substring in path to replace")
    win2.mainloop()
    return old_str.get(), new_str.get()


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
    main(sys.argv[1:])
