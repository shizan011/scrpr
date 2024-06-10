#!/bin/bash
echo "BUILD START"
<<<<<<< HEAD
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear
=======
python3.11 -m pip install -r requirements.txt
python3.11 manage.py collectstatic --noinput --clear
>>>>>>> 36739ec598e5bbe178871a0d4bcf721e9a6f7b87
echo "BUILD END"
