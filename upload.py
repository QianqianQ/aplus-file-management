from utils import *


def upload_yaml_directory(directory):
    """ The files bigger than 4M is uploaded one by one, 
        and the smaller files are compressed to around 4M compression files to upload
    
    Arguments:
        directory {str} -- the path of the course directory
    """

    upload_url = os.environ['PLUGIN_API'] + os.environ['PLUGIN_COURSE'] + '/upload'

    # The path of the subdirectory that contains yaml files
    yaml_dir, index_yaml, index_mtime = check_directory(directory)

    files_and_sizes = files_sizes_list(yaml_dir)

    # sub listing the files by their size (threshold = 4 MB)
    big_files = list(filter(lambda x: x[1] > 4.0, files_and_sizes))
    small_files = list(filter(lambda x: x[1] <= 4.0, files_and_sizes))
    # small_files = [f for f in files_and_sizes if f not in big_files]

    init_headers = {
        'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
    }

    # Post big files one by one
    if big_files:
        for file_index, f in enumerate(big_files):

            headers = init_headers
            last_file = False
            if file_index == len(big_files)-1 and not small_files:
                last_file = True

            if f[1] <= 50.0:  # if the file <= 50MB, post the file object directly
                # the modification time of the index.yaml file
                data = {'index_yaml_mtime': index_mtime} 
                file_name = os.path.relpath(f[0], start=yaml_dir)
                data['file_name'] = file_name
                # flag of the last configuration file
                if last_file:
                    data['last_file'] = True
                try:
                    response = requests.post(upload_url, headers=headers, 
                                             data=data, files={'file': open(f[0], 'rb')})
                    if last_file:
                        print(response.text)
                except:
                    raise Exception('Error occurs when uploading a file with 4MB < size < 50MB!')

            else:  # if the file > 50MB, compress it and then post by chunks
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
                        response = requests.post(upload_url, headers=headers, data=chunk)
                        if last_file:
                            print(response.text)
                    except:
                        raise Exception('Error occurs when uploading a file bigger than 50 MB!')

                buffer.close()

    # Compress small files as one and post it
    if small_files:
        # Add the JWT token to the request headers for the authentication purpose
        headers = {
                    'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
                }
        data = {'index_yaml_mtime': index_mtime} 
        data['compression_file'] = True
        last_file = small_files[-1][0]  # Record the last file

        compress_files_upload(small_files, last_file, yaml_dir, 4*1024*1024, upload_url, headers, data)


def main():

    if 'PLUGIN_API' in os.environ and 'PLUGIN_TOKEN' in os.environ and 'PLUGIN_COURSE' in os.environ:
        upload_yaml_directory(os.getcwd())
    else:
        raise ValueError('No API or JWT token provided')
    

if __name__ == "__main__":
    main()
