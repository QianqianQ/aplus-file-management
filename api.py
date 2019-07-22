import os
import requests
from io import BytesIO
import tarfile
import zipfile


def upload_yaml_direcotry_zip(directory):

    yaml_dir = os.path.join(directory, '_build', 'yaml')

    if not os.path.exists(yaml_dir):
         raise FileNotFoundError("No '_build/yaml' directory")
    elif not os.path.isdir(yaml_dir):
        raise NotADirectoryError("'_build/yaml' is not a directory")

    headers = {
                'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
              }

    buffer = BytesIO()

    try:
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:

            # Upload 'yaml' dir
            for root, dirs, files in os.walk(yaml_dir):
                for name in files:
                    dest_file_name = os.path.relpath(os.path.join(root, name), start=yaml_dir)
                    zf.write(os.path.join(root, name), dest_file_name)
    except Exception as e:
        raise repr(e)

    buffer.seek(0)

    files = {'file': buffer.getvalue()}
    response = requests.put(os.environ['PLUGIN_API'], headers=headers, files=files)
    buffer.close()
    print(response.text)


def upload_yaml_direcotry_tar(directory):

    build_dir = os.path.join(directory, '_build')
    yaml_dir = os.path.join(build_dir, 'yaml')

    if not os.path.exists(yaml_dir):
         raise FileNotFoundError("No '_build/yaml' directory")
    elif not os.path.isdir(yaml_dir):
        raise NotADirectoryError("'_build/yaml' is not a directory")

    headers = {
                'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
              }

    buffer = BytesIO()

    try:
        with tarfile.open(fileobj=buffer, mode='w:gz') as tf:
            # Upload 'yaml' dir
            for root, dirs, files in os.walk(yaml_dir):
                for name in files:
                    dest_file_name = os.path.relpath(os.path.join(root, name), start=yaml_dir)
                    tf.add(os.path.join(root, name), dest_file_name)
                
    except Exception as e:
        raise repr(e)

    buffer.seek(0)

    files = {'file': buffer.getvalue()}
    response = requests.put(os.environ['PLUGIN_API'], headers=headers, files=files)
    buffer.close()
    print(response.text)


def main():

    if 'PLUGIN_API' in os.environ and 'PLUGIN_TOKEN' in os.environ:
        upload_yaml_direcotry_tar(os.getcwd())
    else:
        raise ValueError('No API and JWT token provided')
    

if __name__ == "__main__":
	main()