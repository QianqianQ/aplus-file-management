import os
import requests
from io import BytesIO
import tarfile
import zipfile


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
    except Exception as e:
        raise repr(e)

    # Change the stream position to the start
    buffer.seek(0)

    # Upload the compressed file
    files = {'file': buffer.getvalue()}
    response = requests.put(os.environ['PLUGIN_API'], headers=headers, files=files)
    buffer.close()
    print(response.text)


def main():

    if 'PLUGIN_API' in os.environ and 'PLUGIN_TOKEN' in os.environ:
        upload_yaml_direcotry_tar(os.getcwd())
    else:
        raise ValueError('No API or JWT token provided')
    

if __name__ == "__main__":
    main()
