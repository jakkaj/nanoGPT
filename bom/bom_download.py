import ftplib
import os
# connect to the FTP server
ftp = ftplib.FTP('ftp.bom.gov.au')
ftp.login()

# navigate to the directory you want to list
ftp.cwd('/anon/gen/radar')

locations = ["IDR664", "IDR713"]

# list the files in the directory
files = ftp.nlst()

for location in locations:
   

    for file in files:
        # does the file include the text IDR664 and end with .png?
        if location in file and file.endswith('.png'):
            print(file)
            date = file[9:17]
            year = date[0:4]
            month = date[4:6]
            day = date[6:8]
            folder_path = f"./data/bom_radar/{location}/{year}/{month}/{day}/"

            # create the directory if it doesn't exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)


            #check the file doesnt exist
            if os.path.exists(folder_path + file):
                print(f"File already exists: {folder_path + file}")
                continue


            # close the FTP connection
            #save the file
            with open(folder_path + file, 'wb') as f:
                ftp.retrbinary('RETR ' + file, f.write)
ftp.quit()