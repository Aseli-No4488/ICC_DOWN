import os
from requests import get
from pywebcopy import save_webpage
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

from pywebcopy.configs import default_config
from pywebcopy.configs import get_config
default_config["encoding"] = "utf-8"


import re
from tqdm import tqdm
from pathlib import Path
from PIL import Image

from .utils import string_to_path, version, convert_to, lbp_anime_face_detect
from .ICC_UP import icc_up
from time import sleep


# def save_webpage(url,
#               project_folder=None,
#               project_name=None,
#               bypass_robots=None,
#               debug=False,
#               delay=None,
#               threaded=None,):
    
    
#     config = get_config(url, project_folder, project_name, bypass_robots, debug, delay, threaded)
#     page = config.create_page()
#     page.get(url, headers={'User-Agent': 'Mozilla/5.0',}, encoding='utf-8')
#     if threaded:
#         warnings.warn(
#             "Opening in browser is not supported when threading is enabled!")
#         open_in_browser = False
#     page.save_complete(pop=False)
    

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
                f.write(f"Created:{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
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
    def readTag(self, tag):
        # Wait for the file to be available
        for i in range(10):
            try:
                with open(self.path, 'r') as f:
                    for line in f.readlines():
                        if line.startswith(tag):
                            return line.split(':')[1].strip()
                return None
            except:
                sleep(0.1)
                continue


def download_html(url, folder_name, logger:Logger):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    abs_path = os.path.abspath(folder_name)
    abs_folder_path = abs_path.split('/')[:-1]
    abs_folder_name = abs_path.split('/')[-1]
    
    # Add log file
    logger.writeline(f"URL:{url}")
    logger.writeline(f"Folder:{folder_name}")

    # Download the main HTML file
    save_webpage(url, abs_folder_path, project_name=abs_folder_name, bypass_robots=True, open_in_browser=False, debug=True)
    
    # Inject js to the end of the body
    from .utils import get_inject_script
    script = get_inject_script()
    
    ## Mapping
    script = script.replace('__target_url__', url.strip())
    script = script.replace('__version__', version)
    
    # Load the HTML file
    html_path = os.path.join(folder_name, url.replace('https://', '').replace('http://', ''), 'index.html')
    with open(html_path, 'r', encoding='UTF-8') as f:
        html = f.read()
        
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.find('body')
    if body:
        body.append(BeautifulSoup(script, 'html.parser'))
    
    
    # Save the modified HTML
    html_path = os.path.join(html_path)
    with open(html_path, 'w', encoding='UTF-8') as f:
        f.write(str(soup))

    logger.writeline(f"HTML:{html_path}")
    print(f"HTML and assets saved in {folder_name}")




def download_project(url, logger:Logger, run_ICC_UP = False):
    
    HTML = logger.readTag("HTML").replace("index.html", "")
    if HTML == None:
        print("HTML not found")
        logger.writeline(f"Error:HTML not found")
        return
    
    folder_name = os.path.dirname(HTML)
    
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
    res = get(url)
    
    if(not res.status_code == 200):
        print("Failed to fetch project.json")
        logger.writeline(f"Error:Failed to fetch project.json {res.status_code}")
        # input("Press any key to exit")
        # exit()
        return

    # Save project.json
    os.makedirs(folder_name, exist_ok=True)
    file_path = os.path.join(folder_name, 'project.json')
    
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
            img_url = os.path.join(os.path.dirname(url), img).replace("\\", "/")
            path = os.path.join(folder_name, img)
            
            # Check if the image already exists 
            if os.path.exists(path) or any([os.path.exists(path.replace(i, ".webp")) for i in [".jpg", ".jpeg", ".png", ".gif"]]):
                continue
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb', ) as f:
                print(img_url)
                f.write(get(img_url).content)
        
        # Convert to webp
        print("Converting images to webp...")
        for img in tqdm(l):
            path = os.path.join(folder_name, img)
            
            if path.endswith(".webp"):
                continue
            
            try: convert_to(Path(path))
            except: 
                logger.writeline(f"Error:Failed to convert {path}")
                print(f"Not found during converting", path)

        for img in l:
            path = os.path.join(folder_name, img)
            
            if path.endswith(".webp"):
                continue
            
            try: os.remove(path)
            except: 
                logger.writeline(f"Error:Failed to remove {path}")
                print(f"Not found?", path)
        
    # Run ICC_UP
    if run_ICC_UP:
        print("Running ICC_UP...")
        try: icc_up(folder_name, file_path)
        except: 
            logger.writeline(f"Error:Failed to run ICC_UP")
            print("Failed to run ICC_UP")
        print("ICC_UP done!")

def find_thumbnails(logger:Logger, save_thumbnail = True):
    print("Finding thumbnails...")
    logger.writeline(f"Finding thumbnails...")
    
    HTML = logger.readTag("HTML").replace("index.html", "")
    if HTML == None:
        print("HTML not found")
        logger.writeline(f"Error:HTML not found")
        return
    
    folder_name = os.path.dirname(HTML)

    data = []
    img_folder = os.path.join(folder_name, 'img')
    try:
        for file_name in tqdm(os.listdir(img_folder)):
            faces = lbp_anime_face_detect(os.path.join(img_folder, file_name))

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
        thumbnail_path = os.path.join(folder_name, 'img', 'thumbnail_' + file_name)
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
            thumbnail_path = os.path.join(folder_name, 'img', 'thumbnail_' + file_name)
            with Image.open(img_folder + '/' + file_name) as img:
                img.crop((x, y, x+w, y+h)).save(thumbnail_path, 'webp')

            print(f"Thumbnail saved as {thumbnail_path}")
            logger.writeline(f"Thumbnail saved as {thumbnail_path}")
            count += 1

    


def main(url):
    folder_name = os.path.join('downloads', string_to_path(url))

    logger = Logger(folder_name)    
    
    download_html(url, folder_name, logger)
    download_project(url, logger, True)
    find_thumbnails(logger)


if __name__ == '__main__':
    print("Please run this script as main.")
    pass
