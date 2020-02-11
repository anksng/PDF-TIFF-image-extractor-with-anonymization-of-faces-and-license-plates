# PDF-TIFF-image-extractor-with-anonymization-of-faces-and-license-plates
This CLI-tool extracts images from PDF and TIFF files. Faces and license plates if found are anonymized with a mask.



# Usage instructions

## Requirements:
Mac OS or Linux 

# Mac OS
## Steps :
### To use the anonymization tool :

1. Download `'anonymization_pdf/'` and save to any location.
2. If saved in `'Downloads/'` then run the following commands :
    * `cd Downloads/anonymization_pdf`
    *  `./script.sh` (do not create or activate any virtual env before!)
3. Paste the path of root dir where files are stored when prompted.
4. When prompted `Would you like to use the same directory to store masked images? RECOMMENDED- YES!` - 
    * Type 'y' if you have write access to root dir (where files are stored). In this case, anonymized images are stored in the same root dir.
    * If 'no' then provide a path to dir where anonymized images can be stored.
    <br>
This should start processing and saving the anonymized images extracted from pdf and tiff files. 
<br>
To `stop` the process at any time - press `control(^) + z`. 
<br>
Note that, all files with extension `.pdf` and `.tiff` within the root dir will be processed.<br>


# Ubuntu 18+

## Steps :
### To use anonymization tool :
1. Download `'anonymization_pdf/'` and save to any location.
2. Install python - `sudo apt install python3`
3. Install venv - `sudo apt install python3-venv`
4. Now open the lcoation of anonimyzation_pdf dir. If saved in `'Downloads/'` then run the following commands :
    * `cd Downloads/anonymization_pdf`
    *  `./script_linux.sh` (do not create or activate any virtual env before!)
    <br>
5. When prompted `Would you like to use the same directory to store masked images? RECOMMENDED- YES!` 
    * Type 'y' if you have write access to root dir (where files are stored). In this case, anonymized images are stored in the same root dir.
    * If 'no' then provide a path to dir where anonymized images can be stored.
    <br> 
This should start processing and saving the anonymized images extracted from pdf and tiff files. 
<br>
To `stop` the process at any time - press `control(^) + z`. 
<br>
Note that, all files with extension `.pdf` and `.tiff` within the root dir will be processed.<br>

Also, note that running linux might have conflicts due to python version. <br>
Please follow the steps as above to make sure that `python --version` returns `python 3.6+`.
If `python --version` return `python 3.7`, do the following ->
* Replace the PyMuPDF.whl file with the correct version (`**cp37**_**manylinux**`) from https://pypi.org/project/PyMuPDF/#files .
* Change the corresponding filename in script_linux.sh. 
