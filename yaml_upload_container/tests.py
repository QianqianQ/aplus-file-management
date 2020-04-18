import unittest
import subprocess
from operator import itemgetter
from utils import *


COURSEFOLDER = "/u/71/qinq1/unix/Desktop/my_new_course"  # FIXME: the path to a course directory


def test_upload_gt_50(directory):

    yaml_dir, index_yaml, index_mtime = check_directory(directory)

    files_and_sizes = files_sizes_list(yaml_dir)

    upload_url = os.environ['PLUGIN_API'] + os.environ['PLUGIN_COURSE'] + '/upload'
    init_headers = {
        'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
    }

    for file_index, f in enumerate(files_and_sizes):

        headers = init_headers
        last_file = False
        if file_index == len(files_and_sizes) - 1:
            last_file = True

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


def test_upload_le_50(directory):

    yaml_dir, index_yaml, index_mtime = check_directory(directory)

    files_and_sizes = files_sizes_list(yaml_dir)

    upload_url = os.environ['PLUGIN_API'] + os.environ['PLUGIN_COURSE'] + '/upload'
    init_headers = {
                'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
                }

    for file_index, f in enumerate(files_and_sizes):

        headers = init_headers
        last_file = False
        if file_index == len(files_and_sizes) - 1:
            last_file = True

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


def test_upload_lt_4(directory):

    yaml_dir, index_yaml, index_mtime = check_directory(directory)

    files_and_sizes = files_sizes_list(yaml_dir)

    upload_url = os.environ['PLUGIN_API'] + os.environ['PLUGIN_COURSE'] + '/upload'
    init_headers = {
        'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
    }

    data = {'index_yaml_mtime': index_mtime}
    data['compression_file'] = True

    last_file = files_and_sizes[-1][0]  # Record the last file

    compress_files_upload(files_and_sizes, last_file, yaml_dir, 4 * 1024 * 1024, upload_url, init_headers, data)


def test_delete_course():
    delete_url = os.environ['PLUGIN_API'] + os.environ['PLUGIN_COURSE'] + '/delete'
    headers = {
        'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
    }
    try:
        response = requests.delete(delete_url, headers=headers)
        print(response.text)
    except:
        raise Exception('Error occurs when uploading a file with 4MB < size < 50MB!')


def test_delete_file(file_path):
    delete_url = os.environ['PLUGIN_API'] + os.environ['PLUGIN_COURSE'] + '/files/'+ file_path
    headers = {
        'Authorization': 'Bearer {}'.format(os.environ['PLUGIN_TOKEN'])
    }
    try:
        response = requests.delete(delete_url, headers=headers)
        print(response.text)
    except:
        raise Exception('Error occurs when uploading a file with 4MB < size < 50MB!')

def main():

    os.environ['PLUGIN_API'] = 'http://0.0.0.0:8080/api/v1/'
    os.environ['PLUGIN_TOKEN'] = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJkZWZfY291cnNlIiwiaWF0IjoxNTYyODI4MzA0L' \
                                 'CJpc3MiOiJzaGVwaGVyZCJ9.MUkoD27P6qZKKMM5juL0e0pZl8OVH6S17N_ZFzC7D0cwOgbcDaAO3S1BauXzhQ' \
                                 'OneChPs1KEzUxI2dVF-Od_gpN8_IJEnQnk25XmZYecfdoJ5ST-6YonVmUMzKP7UAcvzCFye7mkX7zJ1ADYtda5' \
                                 '7IUdyaLSPOWnFBSHX5B4XTzzPdVZu1xkRtb17nhA20SUg9gwCOPD6uLU4ml1aOPHBdiMLKz66inI8txPrRK57G' \
                                 'n33m8lVp0WTOOgLV5MkCIpkgVHBl50EHcQFA5KfPet3FBLjpp2I1yThQe_n1Zc6GdnR0v_nqX0JhmmDMOvJ5rh' \
                                 'IHZ7B0hEtFy9rKUWOWfcug'
    os.environ['PLUGIN_COURSE'] = "def_course"

    course_directory = COURSEFOLDER

    print('Test the method for uploading files greater than 50MB')
    subprocess.run(['./docker-compile.sh'], cwd=course_directory, shell=False)
    test_upload_gt_50(course_directory)

    print('Test the delete course method')
    test_delete_course()

    print('Test the method for uploading files with 4MB < size < 50MB')
    subprocess.run(['./docker-compile.sh'], cwd=course_directory, shell=False)
    test_upload_le_50(course_directory)

    print('Test the delete file method')
    test_delete_file('index.yaml')

    print('Test the method for uploading files less than 4MB')
    subprocess.run(['./docker-compile.sh'], cwd=course_directory, shell=False)
    test_upload_lt_4(course_directory)


main()
