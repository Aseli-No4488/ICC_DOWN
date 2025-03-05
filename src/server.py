import os
import urllib.parse, urllib.robotparser
from shutil import rmtree

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from fastapi import WebSocket, WebSocketDisconnect
from typing import List

from webbrowser import open as webbrowser_open
from .download import main as download, Logger

import os
from random import sample
import re
import sys
import asyncio

# # Change working directory
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()


def parse_log(lines, text, undefined=''):
    for line in lines:
        if line.startswith(text):
            return ":".join(line.split(':')[1:]).strip()
    return undefined

def parse_log_all(lines, text, undefined=''):
    result = []
    for line in lines:
        if line.startswith(text):
            result.append(":".join(line.split(':')[1:]).strip())

    if len(result) == 0:
        return undefined

    return result

def get_download_list():
    try:
        folder_list = os.listdir('downloads')
    except:
        os.mkdir('downloads')
        folder_list = []
    result = []

    for folder in folder_list:
        try:
            with open(os.path.join('downloads', folder, 'log.txt'), 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except:
            continue

        original_url = parse_log(lines, 'URL')
        html_url = parse_log(lines, 'HTML').replace('\\', '/')
        project_folder = os.path.dirname(html_url).replace('\\', '/')

        created = parse_log(lines, 'Created')
        projectType = parse_log(lines, 'ProjectType', 'Unknown')
        fatal = parse_log(lines, 'FATAL', 'False')


        title = getTitle(project_folder)

        result.append({
            'title': title,
            'url': html_url,
            'original_url': original_url,
            'downloaded_date': created,
            'projectType': projectType,
            'folder': folder,
            'thumbnail': getMainImage(project_folder),
            'fatal': not (fatal == 'False'),
            'tag': parse_log_all(lines, 'TAG', 'None')
        })

    return result

def getMainImage(folder):
    try:
        path1 = os.path.join(folder, 'images')
        path2 = os.path.join(folder, 'img')
        path = None

        if (os.path.exists(path1) and len(os.listdir(path1)) > 0):
            path = path1
        elif (os.path.exists(path2) and len(os.listdir(path2)) > 0):
            path = path2
        else:
            return None

        listImage = os.listdir(path)

        # If there's thumbnail_img, use that
        thumbnail_imgs = [i for i in listImage if i.startswith('thumbnail_')]
        if len(thumbnail_imgs) > 0:
            return os.path.join(path, sample(thumbnail_imgs, 1)[0]).replace('\\', '/')

        return os.path.join(path, listImage[0]).replace('\\', '/') if len(listImage) > 0 else None
    except Exception as e:
        print(e)
        return None

import json
def getTitle(project_folder):
    # Find the title in the title.json
    title_json_path = 'src/title.json'
    
    ## Check if the title.json exists
    if not os.path.exists(title_json_path):
        with open(title_json_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    
    with open(title_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if project_folder in data:
        return data[project_folder]
    
    print(f"Newly generate the title for {project_folder}")
        
    
    title = generateTitle(project_folder)
    
    if title is not None:
        data[project_folder] = title
        with open(title_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    return title
        

def generateTitle(project_folder):
    # Get title from html
    try:
        with open(os.path.join(project_folder, 'index.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        start = html.find('<title>') + len('<title>')
        end = html.find('</title>')
        title = html[start:end]
        if len(title) > 50:
            return None

        if title not in ['', 'CYOA Plus', 'CYOA', 'ICC']:
            return title
    except:
        pass

    # Get title from project.json
    try:
        with open(os.path.join(project_folder, 'project.json'), 'r', encoding='utf-8') as f:
            data = f.read()
        titles = re.findall(r'".{0,10}? CYOA.{0,10}?"', data)
        if len(titles) > 0:
            # Return shortest title
            return ' '.join(min(titles, key=len).split('"')[-2:-1]).strip()
    except:
        pass
    
    # # Get title from interactive.json
    # with open("../neocities/cyoa-boat-1/interactive.json", 'r', encoding='utf-8') as f:
    #     data = json.load(f)
    
    # # Find most similar url
    # project_url = "/".join(project_folder.split('/')[2:]).replace("https://", "").replace("http://", "").replace("/", "")
    # for d in data:
    #     url = d['url'].replace("https://", "").replace("http://", "").replace("/", "")

    #     # Compare the url
    #     if url == project_url:
    #         return d['title']
        
    
    return project_folder


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep the connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def print(*args):
    message = ' > '+' '.join(map(str, args))
    sys.stdout.write(f"\r{message}\n")
    asyncio.run(manager.send_message(message))
    

@app.post("/api/download/{url_path:path}")
def api_download(url_path: str):
    try:
        # Decode URL
        url = urllib.parse.unquote(url_path)

        if not url.endswith('/'):
            url += '/'

        if url.endswith('.html/'):
            url = '/'.join(url.split('/')[:-2])

        if not url.endswith('/'):
            url += '/'

        print(f"[Server] Downloading {url}")
        res = download(url, print)
        if not res:
            raise Exception('Download failed.')

        return JSONResponse(status_code=201, content=get_download_list())
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/api/hide/{folder}")
def api_hide(folder: str):
    folder = urllib.parse.unquote(folder)
    folder_path = os.path.join('downloads', folder)

    logger = Logger(folder_path)
    logger.writeline('TAG:HIDDEN')

    return JSONResponse(status_code=201, content=get_download_list())

@app.post("/api/close")
def api_close():
    # Close server gracefully
    # Since uvicorn doesn't provide direct os._exit(0), 
    # you can handle shutdown in other ways. For a direct exit:
    import sys
    def shutdown():
        sys.exit(0)
    # Schedule a shutdown (or use a background task)
    # Direct immediate exit:
    shutdown()
    return JSONResponse(status_code=200, content={'status': 'OK'})

@app.delete("/api/download/{folder}")
def api_delete_download(folder: str):
    folder = urllib.parse.unquote(folder)
    try:
        rmtree(os.path.join('downloads', folder))
        return JSONResponse(status_code=200, content=get_download_list())
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/download")
def api_get_download_list():
    return get_download_list()

@app.get("/api/log/{folder}")
def api_get_log(folder: str):
    folder = urllib.parse.unquote(folder)
    logger = Logger(folder)
    return Response(content=logger.read(), media_type="text/plain")


# Serve static files
# If you want to serve the current directory as static, 
# adjust the directory as needed. 
app.mount("/", StaticFiles(directory=".", html=True), name="static")

def main(port=8012, open_browser=True):
    if not (1024 <= port <= 49151):
        print('Invalid port number. Please use a port between 1024 and 49151.')
        return

    if open_browser:
        webbrowser_open(f'http://127.0.0.1:{port}', new=2)

    import uvicorn
    print(f"Server running on port: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == '__main__':
    print("This script is not meant to be run directly.")
    main()
