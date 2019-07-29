import os
import sys
import requests
from io import BytesIO
import tarfile
from datetime import datetime
import time
from operator import itemgetter
from pprint import pprint
from json import loads
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
    it = iter(read_in_chunks(buffer,chunk_size))
    prev = next(read_in_chunks(buffer,chunk_size))
    for item in it:
        # Lag by one item so I know I'm not at the end
        yield prev, False
        prev = item
    # Last item
    yield prev, True


def compression_buffer(files, rel_path_start):
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tf:
        for index, f in enumerate(files):
            file_name = os.path.relpath(f[0], start=rel_path_start)

            # 1. add method
            tf.add(f[0], file_name)
            # 2. addfile method
            # tf.addfile(tarfile.TarInfo(file_name),open(f[0],'rb'))
    
    buffer.seek(0)
    return buffer    


def upload_yaml_directory_tar_1(directory):
    """ Compress the yaml files of a course (in a coures directory) in memory, 
        and upload the compressed file by chunks
    
    Arguments:
        directory {str} -- the path of the course directory
    """
    # The path of the subdirectory that contains yaml files
    yaml_dir = os.path.join(directory, '_build', 'yaml')

    if not os.path.exists(yaml_dir):
        raise FileNotFoundError("No '_build/yaml' directory")
    elif not os.path.isdir(yaml_dir):
        raise NotADirectoryError("'_build/yaml' is not a directory")

    # Add the JWT token to the request headers for the authentication purpose
    headers = {
                'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
              }

    # Create the in-memory file-like object
    buffer = BytesIO()

    # Compress 'yaml' files
    try:
        with tarfile.open(fileobj=buffer, mode='w:gz') as tf:
            for root, dirs, files in os.walk(yaml_dir):
                for name in files:
                    dest_file_name = os.path.relpath(os.path.join(root, name), start=yaml_dir)
                    # Write the file to the in-memory tar
                    tf.add(os.path.join(root, name), dest_file_name)
    except:
        raise Exception('Error occurs!')

    # Change the stream position to the start
    buffer.seek(0)

    # Upload the compressed file by chunks
    chunk_size = 1024 * 1024 * 4
    index = 0
    for chunk, whether_last in iter_read_chunks(buffer, chunk_size=chunk_size):
        offset = index + len(chunk)
        headers['Content-Type'] = 'application/octet-stream'
        headers['Chunk-Size'] = str(chunk_size)
        headers['Chunk-Index'] = str(index)
        headers['Chunk-Offset'] = str(offset)
        if whether_last:
            headers['Last-Chunk'] = 'True'
        index = offset
        try:
            r = requests.put(os.environ['PLUGIN_API'], headers=headers, data=chunk)
            print(r.text)
        except:
            raise Exception('Error occurs!')


def upload_yaml_direcotry_tar_2(directory):
    """ The files bigger than 4M is uploaded one by one, 
        and the smaller files are compressed to around 4M compression files to upload
    
    Arguments:
        directory {str} -- the path of the course directory
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


    # # Add the JWT token to the request headers for the authentication purpose
    headers = {
                'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
              }

    all_files = [os.path.join(basedir, filename) for basedir, dirs, files in os.walk(yaml_dir) for filename in files]
    # list of tuples of file path and size (MB), e.g., ('/Path/to/the.file', 1.0)
    files_and_sizes = [(path, os.path.getsize(path)/(1024*1024.0)) for path in all_files]
    files_and_sizes.sort(key=itemgetter(1), reverse=True)

    # the modification time of the index.yaml file
    data = {'index_yaml_mtime': os.path.getmtime(index_yaml)} 

    # sublisting the files by their size (threshold = 4 MB)    
    big_files = list(filter(lambda x: x[1] >= 4.0, files_and_sizes))
    small_files = list(filter(lambda x: x[1] < 4.0, files_and_sizes))
    # small_files = [f for f in files_and_sizes if f not in big_files]

    # Post big files one by one
    if big_files:
        for index, f in enumerate(big_files):

            # flag of the last configuration file
            if index == len(big_files)-1 and not small_files:
                last_file = True
                data['last_file'] = True
            file_name = os.path.relpath(f[0], start=yaml_dir)
            data['file_name'] = file_name
    
            r = requests.put(os.environ['PLUGIN_API'], headers=headers, 
                             data=data, files={'file': open(f[0], 'rb')})
            if last_file:
                print(r.text)
    
    # Compress small files as one and post it
    if small_files:

        # Update 'data' param in the request
        data.pop('file_name', None)
        data['compression_file'] = True

        # Create the in-memory file-like object
        buffer = BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:gz') as tf:
            for index, f in enumerate(small_files):
                file_name = os.path.relpath(f[0], start=yaml_dir)
                
                # Add the file to the tar file
                # 1. 'add' method
                tf.add(f[0], file_name)
                # 2. 'addfile' method
                # tf.addfile(tarfile.TarInfo(file_name),open(f[0],'rb'))

        # Change the stream position to the start
        buffer.seek(0)
        print(buffer.getbuffer().nbytes)

        files = {'file': buffer.getvalue()}
        data['last_file'] = True
        response = requests.put(os.environ['PLUGIN_API'], headers=headers, data=data, files=files)
        buffer.close()
        print(response.text)


def upload_yaml_direcotry_tar_3(directory):
    """ The files bigger than 4M is uploaded one by one, 
        and the smaller files are compressed to around 4M compression files to upload
    
    Arguments:
        directory {str} -- the path of the course directory
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

    all_files = [os.path.join(basedir, filename) for basedir, dirs, files in os.walk(yaml_dir) for filename in files]
    # list of tuples of file path and size (MB), e.g., ('/Path/to/the.file', 1.0)
    files_and_sizes = [(path, os.path.getsize(path)/(1024*1024.0)) for path in all_files]
    files_and_sizes.sort(key=itemgetter(1), reverse=True)

    # sublisting the files by their size (threshold = 4 MB)    
    big_files = list(filter(lambda x: x[1] > 4.0, files_and_sizes))
    small_files = list(filter(lambda x: x[1] <= 4.0, files_and_sizes))
    # small_files = [f for f in files_and_sizes if f not in big_files]

    index_mtime = os.path.getmtime(index_yaml)

    # Post big files one by one
    if big_files:
        for file_index, f in enumerate(big_files):

            headers = {
                'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
              }
            last_file = False
            if file_index == len(big_files)-1 and not small_files:
                last_file = True

            if f[1] < 50.0:
                # the modification time of the index.yaml file
                data = {'index_yaml_mtime': index_mtime} 
                file_name = os.path.relpath(f[0], start=yaml_dir)
                data['file_name'] = file_name
                # flag of the last configuration file
                if last_file:
                    data['last_file'] = True

                response = requests.put(os.environ['PLUGIN_API'], headers=headers, 
                                 data=data, files={'file': open(f[0], 'rb')})
                if response.json().get('can_upload', ''):
                            raise ValueError(response.json().get('error')) 
                if last_file:
                    print(response.text)
            else:
                # Create the in-memory file-like object
                buffer = BytesIO()
                # Compress 'yaml' files
                try:
                    with tarfile.open(fileobj=buffer, mode='w:gz') as tf:
                        # Write the file to the in-memory tar
                        file_name = os.path.relpath(f[0], start=yaml_dir)
                        tf.add(f[0], file_name)
                except:
                    raise Exception('Error occurs!')

                # Change the stream position to the start
                buffer.seek(0)

                # Upload the compressed file by chunks
                chunk_size = 1024 * 1024 * 4
                index = 0
                for chunk, whether_last in iter_read_chunks(buffer, chunk_size=chunk_size):
                    offset = index + len(chunk)
                    headers['Content-Type'] = 'application/octet-stream'
                    headers['Chunk-Size'] = str(chunk_size)
                    headers['Chunk-Index'] = str(index)
                    headers['Chunk-Offset'] = str(offset)
                    headers['File-Index'] = str(file_index)
                    headers['Index-Mtime'] = str(index_mtime)
                    if whether_last:
                        headers['Last-Chunk'] = 'True'
                    if last_file:
                        headers['Last-File'] = 'True'
                    index = offset
                    try:
                        response = requests.put(os.environ['PLUGIN_API'], headers=headers, data=chunk)
                        if response.json().get('can_upload', ''):
                            raise ValueError(response.json().get('error')) 
                        if last_file:
                            print(response.text)
                    except:
                        raise Exception('Error occurs!')

                buffer.close()
    
    # Compress small files as one and post it
    if small_files:
        # Add the JWT token to the request headers for the authentication purpose
        headers = {
                    'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
                }

        # Update 'data' param in the request
        data = {'index_yaml_mtime': index_mtime} 
        data['compression_file'] = True

        # Create the in-memory file-like object
        buffer = BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:gz') as tf:
            for index, f in enumerate(small_files):
                file_name = os.path.relpath(f[0], start=yaml_dir)
                
                # Add the file to the tar file
                # 1. 'add' method
                tf.add(f[0], file_name)
                # 2. 'addfile' method
                # tf.addfile(tarfile.TarInfo(file_name),open(f[0],'rb'))

        # Change the stream position to the start
        buffer.seek(0)

        files = {'file': buffer.getvalue()}
        data['last_file'] = True
        response = requests.put(os.environ['PLUGIN_API'], headers=headers, data=data, files=files)
        buffer.close()
        print(response.text)
        if response.json().get('can_upload', ''):
            raise ValueError(response.json().get('error')) 


def main():

    # os.environ['PLUGIN_API'] = 'http://0.0.0.0:8080/api/'
    # os.environ['PLUGIN_TOKEN'] = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJkZWZfY291cnNlIiwiaWF0IjoxNTYyODI4MzA0LCJpc3MiOiJzaGVwaGVyZCJ9.MUkoD27P6qZKKMM5juL0e0pZl8OVH6S17N_ZFzC7D0cwOgbcDaAO3S1BauXzhQOneChPs1KEzUxI2dVF-Od_gpN8_IJEnQnk25XmZYecfdoJ5ST-6YonVmUMzKP7UAcvzCFye7mkX7zJ1ADYtda57IUdyaLSPOWnFBSHX5B4XTzzPdVZu1xkRtb17nhA20SUg9gwCOPD6uLU4ml1aOPHBdiMLKz66inI8txPrRK57Gn33m8lVp0WTOOgLV5MkCIpkgVHBl50EHcQFA5KfPet3FBLjpp2I1yThQe_n1Zc6GdnR0v_nqX0JhmmDMOvJ5rhIHZ7B0hEtFy9rKUWOWfcug'


    if 'PLUGIN_API' in os.environ and 'PLUGIN_TOKEN' in os.environ:
        # upload_yaml_direcotry_tar_1(os.getcwd())
        upload_yaml_direcotry_tar_3(os.getcwd())
    else:
        raise ValueError('No API or JWT token provided')
    

if __name__ == "__main__":
    main()
