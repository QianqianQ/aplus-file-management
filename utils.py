import os
import sys
from io import BytesIO
import tarfile
import requests
from math import floor
from operator import itemgetter


def check_directory(directory):
    """ Check whether the yaml direcotry and index.yaml file exist
    :param directory: str, the path of a course directory
    :return: the path of the yaml directory, the path of the index.yaml file
             and the modification time of the index.yaml
    """

    # The path of the subdirectory that contains yaml files
    yaml_dir = os.path.join(directory, '_build', 'yaml')
    index_yaml = os.path.join(yaml_dir, 'index.yaml')
    if not os.path.exists(yaml_dir):
        raise FileNotFoundError("No '_build/yaml' directory")
    elif not os.path.isdir(yaml_dir):
        raise NotADirectoryError("'_build/yaml' is not a directory")
    elif not os.path.exists(index_yaml):
        raise FileNotFoundError("No '_build/yaml/index.yaml' file")

    index_mtime = os.path.getmtime(index_yaml)

    return yaml_dir, index_yaml, index_mtime


def files_sizes_list(directory):
    """ Get a list of tuples of file path and size in a directory, sorted by the file size (largest to smallest)
    """
    all_files = [os.path.join(basedir, filename) for basedir, dirs, files in os.walk(directory) for filename in files]
    # list of tuples of file path and size (MB), e.g., ('/Path/to/the.file', 1.0)
    files_and_sizes = [(path, os.path.getsize(path) / (1024 * 1024.0)) for path in all_files]
    files_and_sizes.sort(key=itemgetter(1), reverse=True)

    return files_and_sizes


def read_in_chunks(buffer, chunk_size=1024*1024.0*4):
    """Read a buffer in chunks
    
    Arguments:
        buffer -- a BytesIO object
    
    Keyword Arguments:
        chunk_size {float} -- the chunk size of each read (default: {1024*1024*4})
    """
    while True:
        data = buffer.read1(chunk_size)
        if not data:
            break
        yield data


def iter_read_chunks(buffer, chunk_size=1024*1024*4):
    """a iterator of read_in_chunks function
    
    Arguments:
        buffer -- a BytesIO object
    
    Keyword Arguments:
         chunk_size {float} -- the chunk size of each read (default: {1024*1024*4})
    """
    # Ensure it's an iterator and get the first field
    it = iter(read_in_chunks(buffer, chunk_size))
    prev = next(read_in_chunks(buffer, chunk_size))
    for item in it:
        # Lag by one item so I know I'm not at the end
        yield prev, False
        prev = item
    # Last item
    yield prev, True


def tar_filelist_buffer(files, rel_path_start):
    """generate a buffer of a compression file

    :param files: a list of tuples (file_path, file_size)
    :param rel_path_start: str, the start path for relative path of files
    :return: a BytesIO object
    """
    # Create the in-memory file-like object
    buffer = BytesIO()
    
    # Create the in-memory file-like object
    with tarfile.open(fileobj=buffer, mode='w:gz') as tf:
        for index, f in enumerate(files):
            file_name = os.path.relpath(f[0], start=rel_path_start)
            # Add the file to the tar file
            # 1. 'add' method
            tf.add(f[0], file_name)
            # 2. 'addfile' method
            # tf.addfile(tarfile.TarInfo(file_name),open(f[0],'rb'))

    # Change the stream position to the start
    buffer.seek(0)
    return buffer


def compress_files_upload(file_list, last_file, rel_path_start, buff_size_threshold, upload_url, headers, data):
    """ Compress a list of files and upload.
        If the buffer of the compression file smaller than buff_size_threshold, uploaded.
        Otherwise the file list will be divided as two subsets.
        For each subset repeat the above process

    :param file_list: a list of tuples (file_path, file_size)
    :param last_file: tuples (file_path, file_size), the last file of the complete file list
    :param rel_path_start: str, the start path for relative path of files
    :param buff_size_threshold: float, the threshold of buffer size to determine division action
    :param upload_url: api url for uploading files
    :param headers: dict, headers of requests
    :param data: dict, data of requests
    """
    # Generate the buffer of the compression file that contains the files in the file_list
    buffer = tar_filelist_buffer(file_list, rel_path_start)

    if len(buffer.getbuffer()) <= buff_size_threshold or len(file_list) == 1:  # post the buffer
        files = {'file': buffer.getvalue()}
        if file_list[-1][0] == last_file:
            data['last_file'] = True
        try:
            response = requests.post(upload_url, headers=headers, data=data, files=files)
            if 'last_file' in data:
                print(response.text)
        except Exception as e:
            print('Error occurs when uploading a compression file!')
            raise Exception('Error occurs when uploading a compression file!')
        buffer.close()

    else:  # Divide the file_list as two subsets and call the function for each subset
        file_sublists = [file_list[0:floor(len(file_list)/2)], file_list[floor(len(file_list)/2):]]
        for l in file_sublists:
            compress_files_upload(l, last_file, rel_path_start, buff_size_threshold, headers, data)


def error_print():
    return '{}. {}, line: {}'.format(sys.exc_info()[0],
                                     sys.exc_info()[1],
                                     sys.exc_info()[2].tb_lineno)
