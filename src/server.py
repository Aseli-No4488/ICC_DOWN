from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import json
import os
import re
from .download import main as download, Logger
from random import sample

class HTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        print(self.path)
        if self.path.startswith('/api/download'):
            try:
                url = self.path.split('/')[-1]

                # Decode URL
                url = url.replace('%3A', ':').replace('%2F', '/')

                download(url)
                self.send_response(201)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(get_download_list()).encode())
                return self
            except Exception as e:
                print(e)
                self.send_response(500)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'500 Internal Server Error')
                return self
        
        if self.path == "/api/close":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'OK'}).encode())
            os._exit(0)
            return self

        self.send_response(403)


    def do_DELETE(self):
        if self.path.startswith('/api/download'):
            folder = self.path.split('/')[-1]
            try:
                os.system(f'rm -rf downloads/{folder}')
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(get_download_list()).encode())
                return self
            except Exception as e:
                print(e)
                self.send_response(500)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'500 Internal Server Error')
                return self
        
        self.send_response(403)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'403 Forbidden')
        return self

    def do_GET(self):

        # Prevent directory traversal
        if self.path.startswith('..'):
            self.send_response(403)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'403 Forbidden')
            return self

        # Handle API
        if self.path.startswith('/api'):
            return self.handleAPI()

        # if self.path == "/" or self.path == "":
        #     # Redirect to src/main/index.html
        #     self.path = "/src/main/index.html"
        
        # Default to serving files
        return SimpleHTTPRequestHandler.do_GET(self)

    def handleAPI(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        if self.path == '/api/download':
            self.wfile.write(json.dumps(get_download_list()).encode())
        
        if self.path.startswith('api/log'):
            logger = Logger(self.path.split('/')[-1])
            self.wfile.write(logger.read().encode())
        return self

def parse_log(lines, text, undefined = ''):
    for line in lines:
        if line.startswith(text):
            return ":".join(line.split(':')[1:]).strip()
    return undefined

def get_download_list():
    try:
        folder_list = os.listdir('downloads')
    except:
        os.mkdir('downloads')
        folder_list = []
    result = []


    for folder in folder_list:
        try:
            with open(f'downloads/{folder}/log.txt', 'r') as f:
                lines = f.readlines()
        except: continue

        url = parse_log(lines, 'URL')
        created = parse_log(lines, 'Created')
        projectType = parse_log(lines, 'ProjectType', 'Unknown')

        result.append({
            'title': getTitle(folder),
            'url': f'/downloads/{folder}/index.html',
            'original_url': url,
            'downloaded_date': created,
            'projectType': projectType,
            'folder': folder,
            'thumbnail': getMainImage(folder)
        })
    
    return result

def getMainImage(folder):
    try:
        # Just grap first image
        listImage = os.listdir(f'downloads/{folder}/img')

        # If theres thumbnail_img, use that
        thumbnail_imgs = [i for i in listImage if i.startswith('thumbnail_')]
        if len(thumbnail_imgs) > 0:
            # Randomly select one
            return f'/downloads/{folder}/img/{sample(thumbnail_imgs, 1)[0]}'


        return f'/downloads/{folder}/img/{listImage[0]}' if len(listImage) > 0 else None
    except:
        return None


def getTitle(folder):

    # Get title from html
    ## Read index.html
    try:
        with open(f'downloads/{folder}/index.html', 'r') as f:
            html = f.read()
        start = html.find('<title>') + len('<title>')
        end = html.find('</title>')

        title = html[start:end]
        if not title in ['', 'CYOA Plus', 'CYOA', 'ICC']:
            return title
        
    except:
        pass
    
    # Get title from project.json
    try:
        with open(f'downloads/{folder}/project.json', 'r') as f:
            # data = json.load(f)
            data = f.read()
        
        title = re.findall(r'".{0,10}? CYOA.{0,10}?"', data)
        if len(title) > 0:
            # Return shortest title
            return ' '.join(min(title, key=len).split('"')[-2:-1]).strip()

    except:
        pass




    return folder

    
def main(port = 8012, open_browser = True):

    # Check if port is valid
    if not (1024 <= port <= 49151):
        print('Invalid port number. Please use a port between 1024 and 49151.')
        return

    if(open_browser): webbrowser.open(f'http://127.0.0.1:{port}', new=2)

    # Open server
    try:
        httpd = HTTPServer(('0.0.0.0', port), HTTPRequestHandler)
        print(f'Server running on port:{port}')
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Server stopped.')
        httpd.server_close()

    except Exception as e:
        print(f'Error: {e}')


if __name__ == '__main__':
    print("This script is not meant to be run directly.")
    main()