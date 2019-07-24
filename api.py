import os
import requests
from io import BytesIO
import tarfile
import zipfile
from datetime import datetime
import time

def read_in_chunks(buffer, chunk_size=1024*1024*4):
    while True:
        data = buffer.read1(chunk_size)
        if not data:
            break
        yield data

def iter_read_chunks(buffer, chunk_size=1024*1024*4):
    # Ensure it's an iterator and get the first field
    it = iter(read_in_chunks(buffer,chunk_size))
    prev = next(read_in_chunks(buffer,chunk_size))
    for item in it:
        # Lag by one item so I know I'm not at the end
        yield prev, False
        prev = item
    # Last item
    yield prev, True


def upload_yaml_direcotry_tar(directory):
    """ Compress the yaml files of a course (in a coures directory) in memory, 
        and upload the compressed file
    
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
                'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN']),
                # 'Content-Type': 'multipart/form-data'
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
            creation_time = tf.tarinfo.mtime
    except:
        raise Exception('Error occurs!')

    # Change the stream position to the start
    buffer.seek(0)

    # Upload the compressed file by chunks
    index = 0
    offset = 0
    chunk_size = 1024*1024*4
    for chunk, whether_last in iter_read_chunks(buffer,chunk_size=chunk_size):
        offset = index + len(chunk)
        headers['Content-Type'] = 'application/octet-stream'
        headers['Chunk-Size'] = str(chunk_size)
        headers['Chunk-Index'] = str(index)
        headers['Chunk-Offset'] = str(offset)
        if whether_last == True:
            headers['Last-Chunk'] = 'True'
        index = offset
        try:
            r = requests.put(os.environ['PLUGIN_API'], headers=headers, data=chunk)
            print(r.text)
        except:
            raise Exception('Error occurs!')


def main():

    if 'PLUGIN_API' in os.environ and 'PLUGIN_TOKEN' in os.environ:
        upload_yaml_direcotry_tar(os.getcwd())
    else:
        raise ValueError('No API or JWT token provided')
    

if __name__ == "__main__":
    main()
