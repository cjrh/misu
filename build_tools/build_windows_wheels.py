"""
Build all the Windows wheels!

USAGE

    python build_tools/build_windows_wheels.py

DESCRIPTION

Run this from the repo root. It will expect that you have ALREADY
created the following virtual environment directories in the same
location:

- ./venv27
- ./venv36
- ./venv37

Make each of them like this, e.g.,:

C:\misu\python3.7 -m venv venv37

Then you also have to add the requirements to EACH env:

.. code-block: cmd

    pip install Cython numpy
    pip install -r requirements-test.txt

"""
import subprocess as sp

venv_folders = ['venv27', 'venv36', 'venv37']


def build_for_venv(venv):
    print('Building for venv: {venv}'.format(venv=venv))
    build_cmd = '{venv}/Scripts/python setup.py bdist_wheel'.format(venv=venv)
    sp.check_call(build_cmd.split())


def main():
    for v in venv_folders:
        build_for_venv(v)


if __name__ == '__main__':
    main()
