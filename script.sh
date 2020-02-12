#!/bin/sh
echo Installing virtual environment package
echo "Creating virtual environment"
python3 -m venv ENV
echo "Activating environment"
source  ENV/bin/activate
# detect os, linux vs mac, make requiremed changes
# create virtual env
# activate virtual env
tput setaf 2; echo "Installing dependencies"
pip install -r requirements.txt
tput setaf 2; echo "Please enter the path to main directory where pdfs are stored!!"
tput setaf 2; echo "HINT - drag the folder to the terminal, then press enter"
read -p "Path to main directory : " path_to_main_dir
tput setaf 1; echo "Would you like to use the same directory to store masked images? RECOMMENDED! - YES"
read -p "Yes or No? : " -n 1 response

if  [[ $response =~ ^[Yy]$ ]]
then 
	python main.py  --path_to_main_dir $path_to_main_dir --path_to_save_dir $path_to_main_dir --path_to_save_logs $path_to_main_dir --BATCH_SIZE 144 --PATH_TO_PLATE_DETECTION_MODEL models/license_plate_detection/plate_detection_model_1804.model --VERBOSE TRUE --SAVE_ANONYMIZED True
else 
	echo
	tput setaf 1; echo "Enter path to saving masked images!!"
	read -p "Path to save directory : " path_to_save_dir
	python main.py  --path_to_main_dir $path_to_main_dir --path_to_save_dir $path_to_save_dir --path_to_save_logs $path_to_save_dir --BATCH_SIZE 144 --PATH_TO_PLATE_DETECTION_MODEL models/license_plate_detection/plate_detection_model_1804.model --VERBOSE TRUE --SAVE_ANONYMIZED True
fi


