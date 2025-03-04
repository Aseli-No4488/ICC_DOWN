import os
from requests import get
from bs4 import BeautifulSoup
from datetime import datetime

from pywebcopy.configs import default_config
from pywebcopy.configs import get_config
default_config["encoding"] = "utf-8"

import gzip

import re
from tqdm import tqdm
from pathlib import Path
from PIL import Image

from .utils import string_to_path, version, convert_to, lbp_anime_face_detect, extract_json
from .ICC_UP import icc_up
from time import sleep

from pywebcopy.elements import JSResource
from pywebcopy.parsers import unquote_match

print = print

# Fixing not good JSResource repl method
def validate_url(url):
    if not url or not isinstance(url, str):  # Check if the input is a non-empty string
        return False

    # Regex patterns for valid URLs
    absolute_url_pattern = re.compile(
        r"^(https?://[^\s]+)$"  # Matches URLs starting with http or https
    )
    relative_url_pattern = re.compile(
        r"^(\./|\.\./).*"  # Matches relative paths like ./ or ../
    )
    domain_only_pattern = re.compile(
        r"^([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$"  # Matches domain-like URLs like newurl.com
    )

    # Check if the URL matches any valid pattern
    if (absolute_url_pattern.match(url) or 
        relative_url_pattern.match(url) or 
        domain_only_pattern.match(url)):
        return True

    return False

def repl(self, match, encoding=None, fmt=None):
        """
        Schedules the linked files for downloading then resolves their references.
        """
        fmt = fmt or '%s'

        url, _ = unquote_match(match.group(1).decode(encoding), match.start(1))
        self.logger.debug("Sub-JS resource found: [%s]" % url)
        
        # If the URL is invalid, return the original URL
        if not validate_url(url):
            print(f"Invalid URL by custom filter: {url} originally {match.group(0)}")
            
            # Return original string
            return match.group(0)

        if not self.scheduler.validate_url(url):
            print("Invalid URL by default:", url)
            return url.encode(encoding)

        print("Sub-JS resource found: [%s]" % url)
        
        sub_context = self.context.create_new_from_url(url)
        self.logger.debug('Creating context for url: %s as %s' % (url, sub_context))
        ans = self.__class__(
            self.session, self.config, self.scheduler, sub_context
        )
        # self.children.add(ans)
        self.logger.debug("Submitting resource: [%s] to the scheduler." % url)
        self.scheduler.handle_resource(ans)
        re_enc = (fmt % ans.resolve(self.filepath)).encode(encoding)
        self.logger.debug("Re-encoded the resource: [%s] as [%r]" % (url, re_enc))
        return re_enc

# Replace the repl method of JSResource
# JSResource.__dict__['repl'] = repl
setattr(JSResource, 'repl', repl)


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
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write(f'Version:{version}\n')
                f.write(f"Created:{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    def writeline(self, text):
        # Wait for the file to be available
        for i in range(10):
            try:
                with open(self.path, 'a', encoding='utf-8') as f:
                    f.write(text + '\n')
                break
            except:
                sleep(0.1)
                continue
    
    def read(self):
        # Wait for the file to be available
        for i in range(10):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                sleep(0.1)
                continue
    def readTag(self, tag):
        # Wait for the file to be available
        for i in range(10):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    for line in f.readlines():
                        if line.startswith(tag):
                            return ':'.join(line.split(':')[1:]).strip()
                return None
            except:
                sleep(0.1)
                continue

class NullLogger(Logger):
    def __init__(self):
        super().__init__("", null_logger=True)


def save_webpage(url,
        project_folder=None,
        project_name=None,
        bypass_robots=None,
        debug=False,
        open_in_browser=True,
        delay=None,
        threaded=None,
        logger=NullLogger(),
        html_path=None,
        ):
    
    url = url.replace('\\', '/').strip()
    
    config = get_config(url, project_folder, project_name, bypass_robots, debug, delay, threaded)
    config['encoding'] = 'utf-8'
    page = config.create_page()
    headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
        "Accept": "*/*",
        "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3",
        "Content-Type": "application/json+protobuf",
        "X-User-Agent": "grpc-web-javascript/0.1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site"
    }
    
    print(f"[save_webpage] url:{url} folder:{project_folder} name:{project_name}")
    page.get(url, headers=headers)
    page.retrieve()
    page.scheduler.handle_resource(page)

    
    # Check the download process is completed
    ## We cannot check the download process is completed by the page.save_complete() method
    sleep(3)
    
    print(f"[save_webpage] Downloaded {url}")
    
    # Fixing corrupted js files
    fixing_count = 0
    
    ## Get all js files tree
    js_path_list = []
    for root, dirs, files in os.walk(os.path.join(project_folder, project_name)):
        for file in files:
            if file.endswith('.js'):
                js_path_list.append(os.path.join(root, file))
                
    print(len(js_path_list), "js files found.")
    logger.writeline(f"JS:{len(js_path_list)}")
    for target in js_path_list:
        if not target.endswith('.js'): continue
        for type in ['ANSI', 'UTF-8', 'UTF-8-SIG', 'UTF-16', 'UTF-32']:
            try:
                try:
                    with open(target, 'r', encoding=type) as f: data = f.read()
                    break
                except:
                    # If error occurs,
                    # Read and decompress the corrupted Gzip file
                    print(f"Decompressing {target}...")
                    logger.writeline(f"Decompressing:{target}")
                    with open(target, "rb") as f:
                        with gzip.GzipFile(fileobj=f) as gz:
                            decompressed_data = gz.read()

                    # Save or process the decompressed data
                    data = decompressed_data.decode(type)
                    with open(target, 'w', encoding=type) as f:
                        f.write(data)
                    fixing_count += 1
                    break
            except:
                pass
    
    if fixing_count > 0:
        print(f"Fixed {fixing_count} corrupted js files by decompressing them.")

def download_html(url, folder_name, logger:Logger, skipDownload=False) -> bool:
    url = url.replace('\\', '/').strip()
    folder_name = folder_name.replace('\\', '/').strip()
    
    print(f"[Download HTML] url:{url} folder:{folder_name}")
    
    abs_path = os.path.abspath(folder_name)
    abs_folder_path = os.path.dirname(abs_path)
    abs_folder_name = os.path.basename(abs_path)
    
    
    if not os.path.exists(abs_folder_path):
        os.makedirs(abs_folder_path)
    
    # Add log file
    logger.writeline(f"URL:{url}")
    logger.writeline(f"Folder:{folder_name}")
    
    # Load the HTML file
    html_path = os.path.join(folder_name, url.replace('https://', '').replace('http://', '').replace('\\', '/').replace('/ ', '/').replace(' /', '/').replace(' ', "_"), 'index.html').replace('\\', '/')

    # Download the main HTML file
    try:
        if(not skipDownload):
            save_webpage(url, abs_folder_path, project_name=abs_folder_name, bypass_robots=True, open_in_browser=False, debug=False, threaded=False, html_path=html_path, logger=logger)
        
        with open(html_path, 'r', encoding='UTF-8') as f:
            html = f.read()
    except Exception as e:
        print("Failed to download the HTML file")
        logger.writeline(f"Error:Failed to download the HTML file")
        logger.writeline(f"FATAL:{url, html_path}")
        return False
    

    
    # Inject js to the end of the body
    from .utils import get_inject_script
    script = get_inject_script()
    
    ## Mapping
    script = script.replace('__target_url__', url.strip())
    script = script.replace('__version__', version)
        
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
    return True




def download_project(url, logger:Logger, run_ICC_UP = True, skipDownload=False) -> bool:
    
    HTML = logger.readTag("HTML").replace("index.html", "")
    if HTML == None:
        print("HTML not found")
        logger.writeline(f"Error:HTML not found")
        return
    
    folder_name = os.path.dirname(HTML)
    
    logger.writeline(f"ProjectType:ICC")
    logger.writeline(f"RunICC_UP:{run_ICC_UP}")
    logger.writeline(f"Folder:{folder_name}")

    # if (url.startswith('http')):
    if(url.endswith("/")):
        url = url[:-1]
    
    if (url.endswith("index.html")):
        url = url.replace("index.html", "")

    if(not url.endswith("project.json")):
        url += "/project.json"

    
    os.makedirs(folder_name, exist_ok=True)
    file_path = os.path.join(folder_name, 'project.json')
    
    if not skipDownload:
        # Fetch project.json
        print("fetching project.json from: ", url)
        res = get(url)
        
        
        if(not res.status_code == 200):
            print("Failed to fetch project.json")
            logger.writeline(f"Error:Failed to fetch project.json {res.status_code}")
            # Is the project merged into app.js? idk
            
            # Check js/app.c533aa25.js
            ## If exists, extract project.json from it
            if not os.path.exists(os.path.join(folder_name, 'js/app.c533aa25.js')):
                print("Failed to get app.c533aa25.js")
                logger.writeline(f"Error:Failed to get app.c533aa25.js {res.status_code}")
                logger.writeline(f"FATAL:{url}")
                return False
                
            with open(os.path.join(folder_name, 'js/app.c533aa25.js'), 'r', encoding='utf8') as f:
                raw_js = f.read()
        
            res_text = extract_json(raw_js)
                

        else: res_text = res.text
        
        # Save project.json
        with open(file_path, 'w', encoding='utf8') as f:
            f.write(res_text)

    with open(file_path, 'r', encoding='utf8') as f:
        res_text = f.read()
    
    l = re.findall(r'mage":"[^(data:)].*"', res_text.replace(",", "\n").replace(' ', ''))
    
    if len(l) > 0:
        print("*** The project.json has images that are not in the project folder. ***")
        logger.writeline(f"log:*** The project.json has images that are not in the project folder. ***")
        logger.writeline(f"Images:{len(l)}")
        
        new_l = []
        for i in l:
            try:
                new_l.append(i.split("\"")[2])
            except:
                print("Error:", i)
                logger.writeline(f"Error:{i}")
                continue
        l = new_l
        
        # Download images
        print(f"Downloading {len(l)} images...")
        
        # define tqdm
        pbar = tqdm(l)

        for img in pbar:
            if not img.startswith('http'):
                img_url = os.path.join(os.path.dirname(url), img).replace("\\", "/")
            else:
                img_url = img
                img = 'img/' + img.split("/")[-1]
                                
            path = os.path.join(folder_name, img)
            
            # Check if the image already exists 
            if os.path.exists(path) or any([os.path.exists(path.replace(i, ".webp")) for i in [".jpg", ".jpeg", ".png", ".gif"]]):
                continue
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb', ) as f:
                pbar.set_description(f"Downloading {img}")
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
        try: icc_up(folder_name, file_path, print=print)
        except: 
            logger.writeline(f"Error:Failed to run ICC_UP")
            print("Failed to run ICC_UP")
            return False
        print("ICC_UP done!")
    
    return True

def find_thumbnails(logger:Logger, save_thumbnail = True) -> bool:
    print("Finding thumbnails...")
    logger.writeline(f"Finding thumbnails...")
    
    HTML = logger.readTag("HTML")
    if HTML == None:
        print("HTML not found")
        logger.writeline(f"Error:HTML not found")
        return False
    HTML = HTML.replace("index.html", "")
    
    folder_name = os.path.dirname(HTML)

    data = []
    if(os.path.exists(os.path.join(folder_name, 'images'))):
        img_folder = os.path.join(folder_name, 'images')
        
    elif(os.path.exists(os.path.join(folder_name, 'img'))):
        img_folder = os.path.join(folder_name, 'img')
        
    else:
        print("Error:Failed to find images")
        logger.writeline(f"Error:Failed to find images")
        return True
    
    print('[find_thumbnails] img_folder:', img_folder)
    try:
        for file_name in os.listdir(img_folder):
            if 'thumbnail_' in file_name:
                print(f"[find_thumbnails] Already thumbnail generated {file_name}")
                return True

        pbar = tqdm(os.listdir(img_folder))
        for file_name in pbar:
            pbar.set_description(f"Processing {file_name}")
            try:
                faces = lbp_anime_face_detect(os.path.join(img_folder, file_name))
                # Just dealing with one face for now
                if len(faces[0]) >= 1:# and faces[2][0] > 1.0:
                    data.append((file_name, faces))
            except:
                print(f"Error:Failed to detect faces {file_name}. Skipping...")
                continue

    except:
        print("Error:Failed to detect images")
        logger.writeline(f"Error:Failed to detect images")
        return True

    # Sort by score (face[2][0])
    # data.sort(key=lambda x: x[1][2][0], reverse=True)

    if len(data) == 0:
        print("No faces found.")
        logger.writeline(f"No faces found.")
        return True
    
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
        thumbnail_path = os.path.join(img_folder, 'thumbnail_' + file_name)
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
            thumbnail_path = os.path.join(img_folder, 'thumbnail_' + file_name)
            with Image.open(img_folder + '/' + file_name) as img:
                img.crop((x, y, x+w, y+h)).save(thumbnail_path, 'webp')

            print(f"Thumbnail saved as {thumbnail_path}")
            logger.writeline(f"Thumbnail saved as {thumbnail_path}")
            count += 1
            
    return True
    


def main(url, _print=print) -> bool:
    global print
    print = _print
    
    folder_name = os.path.join('downloads', string_to_path(url))
    logger = Logger(folder_name)    
    
    res = True and download_html(url, folder_name, logger)
    res = res and download_project(url, logger, True)
    res = res and find_thumbnails(logger)
    return res


if __name__ == '__main__':
    print("Please run this script as main.")
    pass
