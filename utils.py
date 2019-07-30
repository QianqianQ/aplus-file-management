import os
from io import BytesIO
import tarfile
import requests
from math import floor


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


def compress_files_upload(file_list, last_file, rel_path_start, buff_size_threshold, headers, data):
    """ Compress a list of files and upload.
        If the buffer of the compression file smaller than buff_size_threshold, uploaded.
        Otherwise the file list will be divided as two subsets.
        For each subset repeat the above process

    :param file_list: a list of tuples (file_path, file_size)
    :param last_file: tuples (file_path, file_size), the last file of the complete file list
    :param rel_path_start: str, the start path for relative path of files
    :param buff_size_threshold: float, the threshold of buffer size to determine division action
    :param headers: dict, headers of requests
    :param data: dict, data of requests
    """
    buffer = tar_filelist_buffer(file_list, rel_path_start)
    if len(buffer.getbuffer()) <= buff_size_threshold or len(file_list) == 1:
        files = {'file': buffer.getvalue()}
        if file_list[-1][0] == last_file:
            data['last_file'] = True
        response = requests.put(os.environ['PLUGIN_API'], headers=headers, data=data, files=files)
        buffer.close()
        print(response.text)
        if response.json().get('can_upload', ''):
            raise ValueError(response.json().get('error'))
    else:
        file_sublists = [file_list[0:floor(len(file_list) / 2)], file_list[floor(len(file_list) / 2):]]
        for l in file_sublists:
            compress_files_upload(l, last_file, rel_path_start, buff_size_threshold, headers, data)
