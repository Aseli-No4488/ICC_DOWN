import datetime
from PIL import Image
from pathlib import Path

version = '000a'

banwords = ['https', 'http', 'org', 'com', 'neocities', 'google', 'www', '//']
def string_to_path(string):
    clean_string = string.lower()

    # Remove banned words
    for word in banwords:
        if word in clean_string:
            clean_string = clean_string.replace(word, '')

    clean_string = clean_string.replace('/', '_')

    # Only allow letters, numbers, and underscores
    valid_chars = [c for c in clean_string if c.isalnum() or c == '_']
    clean_string = ''.join(valid_chars)

    # Remove leading digits
    for i, c in enumerate(clean_string):
        if not c.isdigit():
            break

    return clean_string[i:] + f"_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"




def convert_to(source, file_format = 'webp'):
    """Convert image to WebP.

    Args:
        source (pathlib.Path): Path to source image

    Returns:
        pathlib.Path: path to new image
    """
    
    destination = source.with_suffix(f".{file_format}")

    image = Image.open(source)  # Open image
    image.save(destination, format=file_format)  # Convert image to webp
    
    return destination



import cv2
face_cascade = cv2.CascadeClassifier('src/model/lbp_anime_face_detect.xml')

def lbp_anime_face_detect(file_name):
    img = cv2.imread(file_name)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_gray = cv2.equalizeHist(img_gray) 
    
    faces = face_cascade.detectMultiScale3(img_gray, outputRejectLevels=True)
    
    return faces