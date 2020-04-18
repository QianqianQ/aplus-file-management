**Docker Container for course uploading in [mooc-grader](https://github.com/Aalto-LeTech/mooc-grader)**
----
A Docker container that upload / update configuration files of a course to mooc-grader. 
The mooc-grader is required to run as a prerequisite.


**Usage**

This container calls the API of mooc-grader, 
sending the configuration files of a course to the grader. 

The API url and a JWT token need to be provided as environment variables when starting the container. 
The JWT token of a course is provided by [shepherd](https://github.com/apluslms/shepherd).
It is sent to the API in the headers for authentication 
and contains the name of the course folder in the `sub` field.

The course directory which is built by [roman](https://github.com/apluslms/roman) is mounted
to the `$WORKDIR` in the container, and the configuration files of the course is under `$WORKDIR/_build/yaml`.

The configuration files are sent using different strategies based on their size:

files larger than 4 MB: 
1. If the size of a file is equal to or smaller than 50 MB, uploaded the file directly
2. Otherwise the file is compressed and sent by chunks

files smaller than 4MB: 
1. Compressed all the files in memory 
2. If the buffer of the compression file is equal to or smaller than 4 MB, will be sent to the mooc-grader
3. Otherwise the small files will be divided as two sublists 
4. For each sublist continue the above process. 

Providing the correct API url and a valid JWT token, 
the configuration files is uploaded/updated to `/srv/courses/{course_name}` in the mooc-grader container, 
where `{course_name}` is provided by the `sub` field of the JWT token.

Example of using the container
```bash
docker run --rm -it --network="host" \
  -w /data/ \
  -v "$(pwd):/data/:ro" \
  -e PLUGIN_API=http://0.0.0.0:8080/api/ \
  -e PLUGIN_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJkZWZfY291cnNlIiwiaWF0IjoxNTYyODI4MzA0LCJpc3MiOiJzaGVw \
  -e PLUGIN_COURSE=def_course \
  api 
```
