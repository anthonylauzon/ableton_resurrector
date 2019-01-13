# Ableton Resurrector

Ableton resurrector is a python project for Ableton Live on MacOS that will
search your filesystem for a project's missing files with mdfind and
then copy matches into the project's directory.  The project is then
"resurrected" by having all references to the copied files fixed.  The
resurrected project is placed next to the original, so you don't have to worry
about corrupting your projects.


## Installation & Usage

1. Install the module by using pip or running `python setup.py install`

2. On the command line, run `ableton_resurrector -f [YOUR_PROJECT_FILE]`

You can also pass the resurrector a file containing a list of .als file 
locations by using the `-l` flag instead of `-f`.  This is useful for bulk 
resurrections.

## Dependencies

mdfind
beautifulsoup4

## Notes

The algorithm for finding matches is a little rigid at the moment. Ableton
projects provide the byte sizes for the files that are missing and both the
sizes and names of the candidate replacements must match.  Since the project
also supplies a CRC value for the missing files, it is possible to do a search
based on the byte size and file type and then compare the crc values of the
found files.  The difficulty is determining what CRC Ableton is actually using,
since it's not a standard CRC16 or CRC32.  Feel free to fork and fix if you're
up to the task & I'll happily merge your PR.
