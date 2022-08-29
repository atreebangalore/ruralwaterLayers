""" Recommended to use https://tabula.technology/ instead of this script,
both work on same tabula, the above software provides more functionality and
GUI for better interface. If your PDF is based on image then recommended to use
Microsoft Office Mobile app functionality (Image to Table).

This script extracts all tables in a pdf to seperate csv files

Usage:
python pdfTable2csv.py [path] [pages] [drop]

Args: 
path - The path of PDF file or Folder containing PDF files
pages - pages to scan through (seperated by comma)
drop - drop the 'Unnamed' column headings and make first row as column heading.

Raises:
subprocess.CalledProcessError - try uninstalling and reinstalling tabula-py
conda install -c conda-forge tabula-py
"""
import tabula
import os
import sys

def extraction(file):
    if pages:
        tables_orig = tabula.read_pdf(file, pages=pages)
    else:
        tables_orig = tabula.read_pdf(file, pages="all")
    filename = os.path.split(file)[1].split('.')[0]
    for num in range(len(tables_orig)):
        table = tables_orig[num]
        # for present_ele, new_ele in replaceDict.items():
        #     table = table.apply(lambda col: col.astype(
        #         str).str.replace(present_ele, new_ele))
        if drop_unnamed_head:
            table.rename(columns=table.iloc[0], inplace=True)
            table.drop(table.index[0], inplace=True)
        # for column_num, condition in splitDict.items():
        #     split_ele, position = condition
        #     table.iloc[:, column_num] = table.iloc[:, column_num].astype(
        #         str).str.split(split_ele).apply(lambda x: x[position])
        table.to_csv(os.path.join(outPath, f'{filename}_{num}.csv'))
    print(f'Completed: {file}')

if __name__=="__main__":
    # INPUT
    path = sys.argv[1]
    pages = sys.argv[2]
    pages = pages.split(',')
    drop_unnamed_head = sys.argv[3] # True or False
    # replaceDict = {'\r': ' ', '': ''}
    # splitDict = {2: (' ', -1)}
    outPath = os.path.join(os.path.expanduser("~"), 'Desktop', 'pdfTable2csv')
    os.makedirs(outPath, exist_ok=True)

    if os.path.splitext(path)[1]:
        extraction(path)
    else:
        for _, _, files in os.walk(path):
            for file in files:
                if os.path.splitext(file)[1] == '.pdf':
                    extraction(os.path.join(path, file))
