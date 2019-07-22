import os
import requests
import subprocess
from io import BytesIO
import zipfile
import tarfile
from requests_toolbelt import MultipartEncoder

def upload_directory_one_by_one(directory):

    headers = {
                'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
              }

    try:
        for root, dirs, files in os.walk(directory):
            for name in dirs:
                # The relative path of the subdir (start from the uploaded_directory)
                rel_dir = os.path.relpath(os.path.join(root, name), start=directory)

            for name in files:
                # Get the relative path of the file
                rel_file_name = os.path.relpath(os.path.join(root, name), start=directory)

                with open(os.path.join(root, name), 'rb') as f:
                    encoder = MultipartEncoder(fields={'file_name': rel_file_name, 'file': f})
                    headers['Content-Type'] = encoder.content_type
                    requests.post(os.environ['PLUGIN_API'], data=encoder, headers=headers)
        print('success!')
    except Exception as e:
        # If an error occurs, delete the whole new_directory from mooc-grader
        encoder = MultipartEncoder({'error': repr(e)})
        headers['Content-Type'] = encoder.content_type
        response = requests.post(os.environ['PLUGIN_API'], headers=headers, data=encoder)


def upload_direcotry_zipped(directory):

    headers = {
                'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
              }

    buffer = BytesIO()

    try:
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(directory):
                for name in files:
                    dest_file_name = os.path.relpath(os.path.join(root, name), start=directory)
                    zf.write(os.path.join(root, name), dest_file_name)
    except Exception as e:
        raise repr(e)

    buffer.seek(0)

    # Check the content of the zip file
    # with open("../test.zip",'wb') as f:
    #     f.write(buffer.getvalue())

    files = {'file': buffer.getvalue()}
    response = requests.put(os.environ['PLUGIN_API'], headers=headers, files=files)
    buffer.close()
    print(response.text)


def upload_yaml_direcotry_zipped_old(directory):

    if '_build' not in os.listdir(directory):
        raise FileNotFoundError("No '_build' directory")
    elif not os.path.isdir(os.path.join(directory, '_build')):
        raise NotADirectoryError("'_build' is not a directory")

    if 'apps.meta' not in os.listdir(directory):
        raise FileNotFoundError("No 'apps.meta' file")
    elif not os.path.isfile(os.path.join(directory, 'apps.meta')):
        raise FileNotFoundError("'apps.meta is not a file")

    build_dir = os.path.join(directory, '_build')

    if 'yaml' not in os.listdir(build_dir):
        raise FileNotFoundError("No 'yaml' directory")
    elif not os.path.isdir(os.path.join(build_dir, 'yaml')):
        raise NotADirectoryError("'yaml' is not a directory")

    yaml_dir = os.path.join(build_dir, 'yaml')

    headers = {
                'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
              }

    buffer = BytesIO()

    try:
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Upload apps.meta file
            zf.write(os.path.join(directory, 'apps.meta'),
                     os.path.relpath(os.path.join(directory, 'apps.meta'), start=directory))

            # Upload 'yaml' dir
            for root, dirs, files in os.walk(yaml_dir):
                for name in files:
                    dest_file_name = os.path.relpath(os.path.join(root, name), start=directory)
                    zf.write(os.path.join(root, name), dest_file_name)
    except Exception as e:
        raise repr(e)

    buffer.seek(0)

    # Check the content of the zip file
    # with open("../test.zip",'wb') as f:
    #     f.write(buffer.getvalue())

    files = {'file': buffer.getvalue()}
    response = requests.put(os.environ['PLUGIN_API'], headers=headers, files=files)
    buffer.close()
    print(response.text)


def upload_yaml_direcotry_zipped(directory):

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
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:

            # Upload 'yaml' dir
            for root, dirs, files in os.walk(yaml_dir):
                for name in files:
                    dest_file_name = os.path.relpath(os.path.join(root, name), start=yaml_dir)
                    zf.write(os.path.join(root, name), dest_file_name)
    except Exception as e:
        raise repr(e)

    buffer.seek(0)

    # Check the content of the zip file
    # with open("../test.zip",'wb') as f:
    #     f.write(buffer.getvalue())

    files = {'file': buffer.getvalue()}
    response = requests.put(os.environ['PLUGIN_API'], headers=headers, files=files)
    buffer.close()
    print(response.text)


def tar_add_bytes(tf, filename, bytestring):
    """ Add a file to a tar archive
    Args:
        tf (tarfile.TarFile): tarfile to add the file to
        filename (str): path within the tar file
        bytestring (bytes or str): file contents. Must be :class:`bytes` or
            ascii-encodable :class:`str`
    
    https://github.com/Autodesk/pyccc/blob/master/pyccc/docker_utils.py
    """
    if not isinstance(bytestring, bytes):  # it hasn't been encoded yet
        bytestring = bytestring.encode('ascii')
    buff = BytesIO(bytestring)
    tarinfo = tarfile.TarInfo(filename)
    tarinfo.size = len(bytestring)
    tf.addfile(tarinfo, buff)


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
                    # tar_add_bytes(tf, dest_file_name, open(os.path.join(root, name),'rb').read())
                    tf.add(os.path.join(root, name), dest_file_name)
                
    except Exception as e:
        raise repr(e)

    buffer.seek(0)

    files = {'file': buffer.getvalue()}
    response = requests.put(os.environ['PLUGIN_API'], headers=headers, files=files)
    buffer.close()
    print(response.text)


def main():

    #os.environ['PLUGIN_API'] = 'http://0.0.0.0:8080/api/'
    #os.environ['PLUGIN_TOKEN'] = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJkZWZfY291cnNlIiwiaWF0IjoxNTYyODI4MzA0LCJpc3MiOiJzaGVwaGVyZCJ9.MUkoD27P6qZKKMM5juL0e0pZl8OVH6S17N_ZFzC7D0cwOgbcDaAO3S1BauXzhQOneChPs1KEzUxI2dVF-Od_gpN8_IJEnQnk25XmZYecfdoJ5ST-6YonVmUMzKP7UAcvzCFye7mkX7zJ1ADYtda57IUdyaLSPOWnFBSHX5B4XTzzPdVZu1xkRtb17nhA20SUg9gwCOPD6uLU4ml1aOPHBdiMLKz66inI8txPrRK57Gn33m8lVp0WTOOgLV5MkCIpkgVHBl50EHcQFA5KfPet3FBLjpp2I1yThQe_n1Zc6GdnR0v_nqX0JhmmDMOvJ5rhIHZ7B0hEtFy9rKUWOWfcug'

    if 'PLUGIN_API' in os.environ and 'PLUGIN_TOKEN' in os.environ:
        print(os.environ['PLUGIN_API'])
        print(os.environ['PLUGIN_TOKEN'])

    # upload_yaml_direcotry_zipped(os.getcwd())
    upload_yaml_direcotry_tar(os.getcwd())
    # upload_yaml_direcotry_zipped_old(os.getcwd())
    # upload_direcotry_zipped(os.getcwd())
    

if __name__ == "__main__":
	main()