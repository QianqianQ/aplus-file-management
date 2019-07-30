import os
from io import BytesIO
import tarfile


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


def tar_filelist_buffer(files, rel_path_start):
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