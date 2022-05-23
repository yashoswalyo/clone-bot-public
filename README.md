## This is a Telegram Bot written in Python for mirroring files on the Internet to your Google Drive or Telegram. 

### This repo is the lite version mirror leech bot to run on Heroku (No Ban)
### This bot does not support aria2c and qbittorrent.

## Modified By: @yashoswalyo (https://github.com/yashoswalyo)

# Features:
- Leech (splitting, thumbnail for each user, setting as document or as media for each user)
- Stop duplicates for all tasks except yt-dlp tasks
- Zip/Unzip G-Drive links
- Counting files/folders from Google Drive link
- View Link button, extra button to open file index link in broswer instead of direct download
- Status Pages for unlimited tasks
- Clone status
- Search in multiple Drive folder/TeamDrive
- Recursive Search (only with `root` or TeamDrive ID, folder ids will be listed with non-recursive method)
- Multi-TD list by token.pickle if exists
- Extract rar, zip and 7z splits with or without password
- Zip file/folder with or without password
- Use Token.pickle if file not found with Service Account for all Gdrive functions
- Random Service Account at startup
- Mirror/Leech/Watch/Clone/Count/Del by reply
- YT-DLP quality buttons
- Extenstion Filter for uploading/cloning files
- Incomplete task notifier to get incomplete task messages after restart, works with database.
- Mirror Telegram files to Google Drive
- Copy files from someone's Drive to your Drive (Using Autorclone) 
- Download/Upload progress, Speeds and ETAs
- Mirror all yt-dlp supported links
- Uploading to Team Drive
- Index Link support
- Service Account support
- Delete files from Drive
- Add sudo users
- Custom Filename* (Only for Telegram files and yt-dlp)
- Extract password protected files
- Extract these filetypes and uploads to Google Drive
  > ZIP, RAR, TAR, 7z, ISO, WIM, CAB, GZIP, BZIP2, APM, ARJ, CHM, CPIO, CramFS, DEB, DMG, FAT, HFS, LZH, LZMA, LZMA2, MBR, MSI, MSLZ, NSIS, NTFS, RPM, SquashFS, UDF, VHD, XAR, Z, TAR.XZ


## Deploy With Github Workflow

1. Go to Repository Settings -> Secrets

2. Add the below Required Variables one by one by clicking New Repository Secret every time.

   - HEROKU_EMAIL: Heroku Account Email Id in which the above app will be deployed
   - HEROKU_API_KEY: Your Heroku API key, get it from https://dashboard.heroku.com/account
   - HEROKU_APP_NAME: Your Heroku app name, Name Must be unique
   - CONFIG_FILE_URL: Copy [This](https://raw.githubusercontent.com/yashoswalyo/clone-bot-public/master/config_sample.env) in any text editor.Remove the _____REMOVE_THIS_LINE_____=True line and fill the variables. For details about config you can see Here. Go to https://gist.github.com and paste your config data. Rename the file to config.env then create secret gist. Click on Raw, copy the link. This will be your CONFIG_FILE_URL. Refer to below images for clarity.

3. Remove commit id from raw link to be able to change variables without updating the CONFIG_FILE_URL in secrets. Should be in this form: https://gist.githubusercontent.com/username/gist-id/raw/config.env
   - Before: https://gist.githubusercontent.com/yashoswalyo/8cce4a4b4e7f4ea47e948b2d058e52ac/raw/19ba5ab5eb43016422193319f28bc3c7dfb60f25/config.env
   - After: https://gist.githubusercontent.com/yashoswalyo/8cce4a4b4e7f4ea47e948b2d058e52ac/raw/config.env

   - You only need to restart your bot after editing config.env Gist secret.

4. After adding all the above Required Variables go to Github Actions tab in your repository.
   - Select Manually Deploy to Heroku workflow as shown below:

5. Then click on Run workflow

# Modified By:
@yashoswalyo (https://github.com/yashoswalyo)
