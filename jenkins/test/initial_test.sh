#!/bin/bash

# *** Initial Test ***

echo """
# **************************
# ****** Initial Test ******
# **************************
"""

# Get the katana logs to check if the 
response=$(curl --write-out '%{http_code}' --silent --output /dev/null http://localhost:8000/api/slice)

if [[ $response != 200 ]]; then
echo "**** TEST FAILED ****"
echo "**** RESPONSE = $response *****"
exit 1
fi

echo "**** TEST PASSED ****"