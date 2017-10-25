import os, sys, shutil
import py_compile
cur_dir_fullpath = os.path.dirname(os.path.abspath(__file__))
def WalkerCompile(dstDir):
    for filename in os.listdir(dstDir):
        if not filename.endswith('.py'):
            continue
        srcFile = os.path.join(dstDir, filename)
        if srcFile == os.path.abspath(__file__):
            continue
        dstFile = os.path.join(dstDir, filename + 'c')
        print(srcFile + ' --> ' + dstFile)
        py_compile.compile(srcFile, cfile=dstFile)

if __name__ == "__main__":
    files=os.listdir()
    for filename in files:
        if os.path.isdir(filename):
            if filename.startswith('.') or filename.startswith('doc') or filename.startswith('__'):
                continue
            else:
                WalkerCompile(filename)
    WalkerCompile(cur_dir_fullpath)
