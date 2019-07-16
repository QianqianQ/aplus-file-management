#!/bin/sh

echo "PWD"
echo $PWD
ls

curl -X PUT ${PLUGIN_API} -H "Authorization: bearer ${PLUGIN_TOKEN}" -H "Content-Type: application/json" -d '{"uploaded_folder": "'"$PWD"'"}' 
# curl -X PUT ${PLUGIN_API} -H "Authorization: bearer ${PLUGIN_TOKEN}" -H "Content-Type: application/json" -d '{"uploaded_folder": "/u/71/qinq1/unix/Desktop/my_new_course"}' 
    



