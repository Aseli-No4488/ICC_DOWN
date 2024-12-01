import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import datetime

import re
from tqdm import tqdm
from pathlib import Path
from PIL import Image

from .utils import string_to_path, version, convert_to, lbp_anime_face_detect
from .ICC_UP import icc_up
from time import sleep

class Logger:
    def __init__(self, folder_name, null_logger = False):
        if null_logger:
            self.writeline = lambda x: None
            return
        
        self.path = folder_name + '/log.txt'

        # Create the folder if it doesn't exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
    
        if not os.path.exists(self.path):
            with open(self.path, 'w') as f:
                f.write(f'Version:{version}\n')
                f.write(f"Created:{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    def writeline(self, text):
        # Wait for the file to be available
        for i in range(10):
            try:
                with open(self.path, 'a') as f:
                    f.write(text + '\n')
                break
            except:
                sleep(0.1)
                continue
    
    def read(self):
        # Wait for the file to be available
        for i in range(10):
            try:
                with open(self.path, 'r') as f:
                    return f.read()
            except:
                sleep(0.1)
                continue

def download_html(url, folder_name, logger:Logger):
    src_folder = folder_name + '/src'
    
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    if not os.path.exists(src_folder):
        os.makedirs(src_folder)
    
    # Add log file
    logger.writeline(f"URL:{url}")
    logger.writeline(f"Folder:{folder_name}")

    # Download the main HTML file
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to download {url}")
        logger.writeline(f"Error:Failed to download html {response.status_code}")
        return
    
    logger.writeline(f"log:{url}")
    soup = BeautifulSoup(response.content.decode('utf-8','ignore'), 'html.parser')
    
    # Find and download all linked files (CSS and JS)
    for tag, attribute in [('link', 'href'), ('script', 'src')]:
        for element in soup.find_all(tag):
            file_url = element.get(attribute)
            if file_url:
                # Resolve the full URL
                full_url = urljoin(url, file_url)

                # Get the filename from the URL
                filename = os.path.basename(urlparse(full_url).path)

                # Define the local path
                local_path = os.path.join(src_folder, filename)

                try:
                    # Download the linked file
                    file_response = requests.get(full_url)
                    if file_response.status_code == 200:
                        with open(local_path, 'wb') as f:
                            f.write(file_response.content)
                        print(f"Downloaded {filename}")
                        logger.writeline(f"Downloaded:{filename}")
                        
                        # Update the link in the HTML
                        element[attribute] = f'src/{filename}'
                    else:
                        print(f"Failed to download {full_url}")
                        logger.writeline(f"Error:Failed to download {full_url}")
                except Exception as e:
                    print(f"Error downloading {file_url}: {e}")
                    logger.writeline(f"Error:Failed to download {file_url}")
    
    # Find all external fonts
    for element in soup.find_all('style'):
        for font in re.findall(r'url\(([^)]+)\)', element.text):
            font = font.strip().strip('"').strip("'")
            # Get the filename from the URL
            filename = os.path.basename(urlparse(font).path)

            # Define the local path
            local_path = os.path.join(src_folder, filename)

            download_url = font
            # Check if the font is local
            if not font.startswith('http'):
                download_url = urljoin(url, font)

            try:
                # Download the font file
                file_response = requests.get(download_url)
                if file_response.status_code == 200:
                    with open(local_path, 'wb') as f:
                        f.write(file_response.content)
                    print(f"Downloaded {filename}")
                    logger.writeline(f"Downloaded:{filename}")
                    
                    # print("test", element.text, font, f'src/{filename}')
                    # Update the link in the HTML
                    # element.text = element.text.replace(font, f'src/{filename}') # This doesn't work
                    element.string = element.string.replace(font, f'src/{filename}').replace('src/src/', 'src/')

                else:
                    print(f"Failed to download {font}")
                    logger.writeline(f"Error:Failed to download {font}")
            except Exception as e:
                print(f"Error downloading {font}: {e}")
                logger.writeline(f"Error:Failed to download {font}")
    
    # Save the modified HTML
    html_path = os.path.join(folder_name, 'index.html')
    with open(html_path, 'w', encoding='UTF-8') as f:
        f.write(str(soup))

    logger.writeline(f"HTML:{html_path}")
    print(f"HTML and assets saved in {folder_name}")




def download_project(url, folder_name, logger:Logger, run_ICC_UP = False):
    
    logger.writeline(f"ProjectType:ICC")
    logger.writeline(f"RunICC_UP:{run_ICC_UP}")
    logger.writeline(f"Folder:{folder_name}")

    if (url.startswith('http')):
        if(url.endswith("/")):
            url = url[:-1]

        if(not url.endswith("project.json")):
            url += "/project.json"

    

    # Fetch project.json
    print("\nfetching project.json from: ", url)
    res = requests.get(url)
    
    if(not res.status_code == 200):
        print("Failed to fetch project.json")
        logger.writeline(f"Error:Failed to fetch project.json {res.status_code}")
        # input("Press any key to exit")
        # exit()
        return

    # Save project.json
    os.makedirs(folder_name, exist_ok=True)
    file_path = f'{folder_name}/project.json'
    
    with open(file_path, 'w', encoding='utf8') as f:
        f.write(res.text)

    res_text = res.text
    
    l = re.findall(r'mage":"[^(data:)].*"', res_text.replace(",", "\n"))
    
    if len(l) > 0:
        print("*** The project.json has images that are not in the project folder. ***")
        logger.writeline(f"log:*** The project.json has images that are not in the project folder. ***")
        logger.writeline(f"Images:{len(l)}")
        
        l = [i.split("\"")[2] for i in l]
        
        # Download images
        print(f"Downloading {len(l)} images...")

        for img in tqdm(l):
            img_url = f"{url.replace('project.json', '')}{img}"
            path = f"{folder_name}/{img}"
            
            # Check if the image already exists 
            if os.path.exists(path) or any([os.path.exists(path.replace(i, ".webp")) for i in [".jpg", ".jpeg", ".png", ".gif"]]):
                continue
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb', ) as f:
                f.write(requests.get(img_url).content)
        
        # Convert to webp
        print("Converting images to webp...")
        for img in tqdm(l):
            path = f"{folder_name}/{img}"
            
            if path.endswith(".webp"):
                continue
            
            try: convert_to(Path(path))
            except: 
                logger.writeline(f"Error:Failed to convert {path}")
                print(f"Not found during converting", path)

        for img in l:
            path = f"{folder_name}/{img}"
            
            if path.endswith(".webp"):
                continue
            
            try: os.remove(path)
            except: 
                logger.writeline(f"Error:Failed to remove {path}")
                print(f"Not found?", path)
        
    # Run ICC_UP
    if run_ICC_UP:
        print("Running ICC_UP...")
        try: icc_up(os.path.dirname(file_path), file_path)
        except: 
            logger.writeline(f"Error:Failed to run ICC_UP")
            print("Failed to run ICC_UP")
        print("ICC_UP done!")

def find_thumbnails(folder_name, logger:Logger, save_thumbnail = True):
    print("Finding thumbnails...")
    logger.writeline(f"Finding thumbnails...")

    data = []
    img_folder = folder_name + '/img'
    try:
        for file_name in tqdm(os.listdir(img_folder)):
            faces = lbp_anime_face_detect(img_folder + '/' + file_name)

            # Just dealing with one face for now
            if len(faces[0]) >= 1:# and faces[2][0] > 1.0:
                data.append((file_name, faces))
    except:
        print("Error:Failed to find images")
        logger.writeline(f"Error:Failed to find images")
        return

    # Sort by score (face[2][0])
    # data.sort(key=lambda x: x[1][2][0], reverse=True)

    if len(data) == 0:
        print("No faces found.")
        logger.writeline(f"No faces found.")
        return
    
    count = 0
    for i, (file_name, faces) in enumerate(data):        
        if count > 5:
            break
            
        if faces[2][0] < 1.5:
            continue
        
        x, y, w, h = faces[0][0]

        # If the face is too small, skip
        if w*h < 30000:
            continue

        # Save as thumbnail
        thumbnail_path = folder_name + '/img/thumbnail_' + file_name
        with Image.open(img_folder + '/' + file_name) as img:
            img.crop((x, y, x+w, y+h)).save(thumbnail_path, 'webp')

        print(f"Thumbnail saved as {thumbnail_path}")
        logger.writeline(f"Thumbnail saved as {thumbnail_path}")
        count += 1
    
    if count < 5:
        print("Not enough faces found.")
        logger.writeline(f"Not enough faces found.")

        data.sort(key=lambda x: x[1][2][0], reverse=True)
        for i, (file_name, faces) in enumerate(data):
            if count > 5:
                break

            x, y, w, h = faces[0][0]

            if w*h < 15000:
                continue

            # Save as thumbnail
            thumbnail_path = folder_name + '/img/thumbnail_' + file_name
            with Image.open(img_folder + '/' + file_name) as img:
                img.crop((x, y, x+w, y+h)).save(thumbnail_path, 'webp')

            print(f"Thumbnail saved as {thumbnail_path}")
            logger.writeline(f"Thumbnail saved as {thumbnail_path}")
            count += 1




def main(url):
    folder_name = 'downloads/' + string_to_path(url)

    logger = Logger(folder_name)

    download_html(url, folder_name, logger)
    download_project(url, folder_name, logger, True)

    find_thumbnails(folder_name, logger)





if __name__ == '__main__':
    # url = 'https://witchwitch.neocities.org/WizardingWorld/'
    # url = input("Enter the URL of cyoa or path(folder): ")
    # main(url)
    
    pass
