import argparse
import binascii
import gzip
import logging
import os
import mdfind
import multiprocessing
import pickle
import shutil
import traceback
import uuid
import zlib

from bs4 import BeautifulSoup

SIZE_QUERY='kMDItemFSSize'
NAME_QUERY='kMDItemDisplayName'

PICKLE_FILENAME = "project_db.pickle"
FILE_LIST='ableton_files_100.txt'
SUFFIX='🐰'
RESURRECTED_DIR='Resurrected Files'

PATH_TYPE_MISSING = 0
PATH_TYPE_EXTERNAL = 1
PATH_TYPE_LIBRARY = 2
PATH_TYPE_CURRENT_PROJECT = 3
SAFE_PATH_ID = 1000

def flag_check(flag):
    return flag in ['1', 1, 'True', 'TRUE', 'true']

DEBUG=flag_check(os.environ.get('DEBUG'))

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def is_gz_file(filepath):
    with open(filepath, 'rb') as test_f:
        return binascii.hexlify(test_f.read(2)) == b'1f8b'

def run(args):
    ableton_project_path, symlink = args
    try:
        xml_path = decompress_ableton_als(ableton_project_path)
    except:
        logging.error("ERROR_DECOMPRESSING: {}".format(ableton_project_path))
        if DEBUG:
            traceback.print_exc()
        return 1
    try:
        resurrected_xml_path = resurrect_ableton_xml(xml_path, symlink)
    except:
        logging.error("ERROR_RESURRECTING: {}".format(ableton_project_path))
        if DEBUG:
            traceback.print_exc()
        return 1

    return 0

def decompress_ableton_als(als_path):
    print("RESURRECTING: {}".format(als_path))
    
    filename = '.'.join(os.path.basename(als_path).split('.')[:-1])
    dirname = os.path.dirname(als_path)
    xml_path = "{}/{}-{}.xml".format(dirname, filename, SUFFIX)

    if is_gz_file(als_path):
        tmp_gz = "/tmp/{}.gz".format(str(uuid.uuid4()))
        shutil.copy(als_path, tmp_gz)
        with open(xml_path, 'wb') as xml_file:
            xml_file.write(gzip.decompress(open(tmp_gz, 'rb').read()))
    else:
        shutil.copy(als_path, xml_path)

    return xml_path

def resurrect_ableton_xml(xml_path, symlink):
    soup = BeautifulSoup(open(xml_path).read(), "xml")
    project_dir = os.path.dirname(xml_path)
    resurrected_dir = "{}/{}".format(project_dir, RESURRECTED_DIR)

    os.makedirs(resurrected_dir, exist_ok=True)

    max_relative_path_id = 0
    for relative_path_element in soup.find_all('RelativePathElement'):
        if relative_path_element.get('Id') and \
            int(relative_path_element['Id']) > max_relative_path_id:
            max_relative_path_id = int(relative_path_element['Id'])


    new_relative_path_id = max_relative_path_id +  1

    for sample_ref in soup.find_all('SampleRef'):
        relative_path_type = sample_ref.find('RelativePathType')
        relative_path_type_value = int(relative_path_type['Value'])

        name = sample_ref.find('Name')['Value']
        search_hint = sample_ref.find("SearchHint")
        file_size = int(search_hint.find('FileSize')['Value'])
        crc = search_hint.find('Crc')['Value']
        crc_max_size = search_hint.find('MaxCrcSize')['Value']
        relative_path = sample_ref.find('RelativePath')
        has_relative_path = sample_ref.find('HasRelativePath')

        path = None
        if relative_path_type_value == PATH_TYPE_EXTERNAL:
            dirs = \
                [e['Dir'] for e in search_hint.find_all('RelativePathElement')]
            path = "/{}/{}".format('/'.join(dirs), name)
        elif relative_path_type_value == PATH_TYPE_CURRENT_PROJECT:
            path_elements = relative_path.find_all('RelativePathElement')
            dirs = [e['Dir'] for e in path_elements]
            path = "{}/{}".format('/'.join(dirs), name)

        if path and not os.path.exists(path) or \
            relative_path_type_value == PATH_TYPE_MISSING:
            name_matches = mdfind.query("kMDItemDisplayName='{}'".format(name))
            for match_path in name_matches:
                match_file_stat = os.stat(match_path)
                match_size = match_file_stat.st_size

                if file_size == match_size or file_size == 0:
                    if symlink:
                        try:
                            os.symlink(match_path, 
                                       "{}/{}".format(resurrected_dir, name))
                        except FileExistsError:
                            pass
                    else:
                        try:
                            shutil.copy(match_path, resurrected_dir)
                        except shutil.SameFileError:
                            pass

                    relative_path.clear()
                    new_relative_path_element = \
                        soup.new_tag('RelativePathElement',
                                     Id=str(new_relative_path_id),
                                     Dir=RESURRECTED_DIR)
                    relative_path.append(new_relative_path_element)

                    relative_path_type['Value'] = PATH_TYPE_CURRENT_PROJECT
                    has_relative_path['Value'] = 'true'

                    break

    os.remove(xml_path)

    if DEBUG:
        with open(xml_path, 'w') as als_file_xml:
            als_file_xml.write(soup.prettify())

    with gzip.open(xml_path.replace('.xml', '.als'), 'wb') as als_file:
        als_file.write(soup.prettify().encode('utf-8'))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file')
    parser.add_argument('-l', '--list')
    parser.add_argument('-s', '--symlink')
    args = parser.parse_args()

    symlink = flag_check(args.symlink)

    if args.file:
        run((args.file, args.symlink))
    elif args.list:
        with multiprocessing.Pool(processes=12) as pool:
            paths = [f.strip() for f in open(args.list).readlines()]
            pool.map(run, [(path, symlink) for path in paths])

if __name__ == "__main__":
    main()
