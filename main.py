import os
from utils import check_yaml_directory, upload_directory


def main():

    if 'PLUGIN_API' in os.environ and 'PLUGIN_TOKEN' in os.environ and 'PLUGIN_COURSE' in os.environ:
        upload_url = os.environ['PLUGIN_API'] + os.environ['PLUGIN_COURSE'] + '/upload'

        yaml_dir, index_yaml, index_mtime = check_yaml_directory(os.getcwd())

        upload_directory(yaml_dir, upload_url, index_mtime)
    else:
        raise ValueError('No API or JWT token provided')
    

if __name__ == "__main__":
    main()
