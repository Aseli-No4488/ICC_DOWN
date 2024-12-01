import datetime
from PIL import Image
from pathlib import Path
from requests import get

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

# if file not exist, download the model
if not Path('src/model/lbp_anime_face_detect.xml').is_file():

    url = "https://cdn.jsdelivr.net/gh/XavierJiezou/anime-face-detection@master/model/lbp_anime_face_detect.xml"
    
    # Create directory if not exist
    Path('src/model').mkdir(parents=True, exist_ok=True)
    
    # Download the model
    with open('src/model/lbp_anime_face_detect.xml', 'wb') as f:
        f.write(get(url).content)
    
face_cascade = cv2.CascadeClassifier('src/model/lbp_anime_face_detect.xml')

def lbp_anime_face_detect(file_name):
    img = cv2.imread(file_name)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_gray = cv2.equalizeHist(img_gray) 
    
    faces = face_cascade.detectMultiScale3(img_gray, outputRejectLevels=True)
    
    return faces



def get_inject_script():
    return """
<script
  async
  src="https://www.googletagmanager.com/gtag/js?id=G-V18BB36XSC"
></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag() {
    dataLayer.push(arguments);
  }
  gtag("js", new Date());

  gtag("config", "G-V18BB36XSC", { debug_mode: false });

  const sendActivated = () => {
    const button = document.querySelector(".v-btn"); // Kinda works with any vue button

    if (!button) {
      return;
    }

    const rows = button.__vue__.$store.state.app.rows;
    let activated = [];
    for (var t = [], e = 0; e < rows.length; e++) {
      for (var i = 0; i < rows[e].objects.length; i++) {
        const object = rows[e].objects[i];

        if (!object.isSelectableMultiple && object.isActive) {
          activated.push(object);
        }
      }
    }

    for (let i = 0; i < activated.length; i++) {
      gtag("event", "activate_before_unload", {
        target_url: "__target_url__",
        version: "__version__",
        activated_id: activated[i].id,
        activated_name: activated[i].name,
      });
    }
  };

  window.onunload = sendActivated;
  window.onclose = sendActivated;
</script>"""