import datetime
from PIL import Image
from pathlib import Path
from requests import get
import urllib

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

removeAllURLTrash = lambda x: urllib.parse.unquote(x).replace('http://', '').replace('https://', '').replace('/', '')

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



def getDummyProject():
  return '''{"isEditModeOnAll":"!0","isStyleOpen":"!1","isPointsOpen":"!1","isChoicesOpen":"!1","isDesignOpen":"!1","isViewerVersion":"!1","backpack":[],"comp":{},"compR":{},"compG":{},"compODG":{},"compRDG":{},"tmpRequired":{},"pointTypeMap":{},"wordMap":{},"objectMap":{},"rowIdLength":4,"objectIdLength":4,"words":[],"wordChangeComplete":"!1","groups":[],"rowDesignGroups":[],"objectDesignGroups":[],"chapters":[],"activated":[],"rows":[],"pointTypes":[],"variables":[],"mdObjects":[],"printThis":"!1","autoSaveIsOn":"!1","autoSaveInterval":null,"checkDeleteRow":"!0","checkDeleteObject":"!1","defaultRowTitle":"Row","defaultRowText":"","defaultChoiceTitle":"Choice","defaultChoiceText":"","defaultBeforePoint":"Cost:","defaultAfterPoint":"points","defaultBeforeReq":"Required:","defaultAfterReq":"choice","defaultAddonTitle":"Addon","defaultAddonText":"","styling":{"rowTitle":"Times New Roman","rowText":"Times New Roman","objectTitle":"Times New Roman","objectText":"Times New Roman","addonTitle":"Times New Roman","addonText":"Times New Roman","scoreText":"Times New Roman","rowTitleTextSize":200,"rowTextTextSize":100,"objectTitleTextSize":200,"objectTextTextSize":100,"addonTitleTextSize":200,"addonTextTextSize":100,"scoreTextSize":75,"barTextColor":"#000000","barIconColor":"#0000008A","barBackgroundColor":"#FFFFFFFF","barTextPadding":17,"barTextMargin":0,"barTextFont":"Times New Roman","barTextSize":15,"barPadding":0,"barMargin":0,"rowTitleColor":"#000000","rowTextColor":"#000000","objectTitleColor":"#000000","objectTextColor":"#000000","addonTitleColor":"#000000","addonTextColor":"#000000","scoreTextColor":"#000000","objectHeight":"!0","rowTitleAlign":"center","rowTextAlign":"center","objectTitleAlign":"center","objectTextAlign":"center","addonTitleAlign":"center","addonTextAlign":"center","scoreTextAlign":"center","rowButtonXPadding":0,"rowButtonYPadding":0,"backgroundImage":"","rowBackgroundImage":"","objectBackgroundImage":"","rowBorderImage":"","rowBorderImageRepeat":"stretch","rowBorderImageWidth":5,"rowBorderImageSliceTop":5,"rowBorderImageSliceBottom":5,"rowBorderImageSliceLeft":5,"rowBorderImageSliceRight":5,"objectBorderImage":"","objectBorderImageRepeat":"stretch","objectBorderImageWidth":5,"objectBorderImageSliceTop":5,"objectBorderImageSliceBottom":5,"objectBorderImageSliceLeft":5,"objectBorderImageSliceRight":5,"backgroundColor":"#FFFFFFFF","objectBgColor":"#FFFFFFFF","rowBgColor":"#FFFFFFFF","rowBgColorIsOn":"!1","objectBgColorIsOn":"!1","objectImageWidth":100,"rowImageWidth":100,"objectImageMarginTop":0,"objectImageMarginBottom":0,"rowImageMarginTop":0,"objectMargin":10,"rowMargin":10,"rowTextPaddingY":5,"rowTextPaddingX":10,"objectTextPadding":10,"rowBodyMarginTop":25,"rowBodyMarginBottom":25,"rowBodyMarginSides":1,"objectDropShadowH":0,"objectDropShadowV":0,"objectDropShadowSpread":0,"objectDropShadowBlur":0,"objectDropShadowColor":"grey","objectDropShadowIsOn":"!1","rowDropShadowH":0,"rowDropShadowV":0,"rowDropShadowSpread":0,"rowDropShadowBlur":0,"rowDropShadowColor":"grey","rowDropShadowIsOn":"!1","selFilterBlurIsOn":"!1","selFilterBlur":0,"selFilterBrightIsOn":"!1","selFilterBright":100,"selFilterContIsOn":"!1","selFilterCont":100,"selFilterGrayIsOn":"!1","selFilterGray":0,"selFilterHueIsOn":"!1","selFilterHue":0,"selFilterInvertIsOn":"!1","selFilterInvert":0,"selFilterOpacIsOn":"!1","selFilterOpac":100,"selFilterSaturIsOn":"!1","selFilterSatur":1,"selFilterSepiaIsOn":"!1","selFilterSepia":0,"selBgColorIsOn":"!0","selOverlayOnImage":"!1","selFilterBgColor":"#70FF7EFF","selBorderColorIsOn":"!1","selFilterBorderColor":"#000000FF","selCTitleColorIsOn":"!1","selFilterCTitleColor":"#000000FF","selCTextColorIsOn":"!1","selFilterCTextColor":"#000000FF","selATitleColorIsOn":"!1","selFilterATitleColor":"#000000FF","selATextColorIsOn":"!1","selFilterATextColor":"#000000FF","reqFilterBlurIsOn":"!1","reqFilterBlur":0,"reqFilterBrightIsOn":"!1","reqFilterBright":100,"reqFilterContIsOn":"!1","reqFilterCont":100,"reqFilterGrayIsOn":"!1","reqFilterGray":0,"reqFilterHueIsOn":"!1","reqFilterHue":0,"reqFilterInvertIsOn":"!1","reqFilterInvert":0,"reqFilterOpacIsOn":"!0","reqFilterOpac":50,"reqFilterSaturIsOn":"!1","reqFilterSatur":1,"reqFilterSepiaIsOn":"!1","reqFilterSepia":0,"reqBgColorIsOn":"!1","reqOverlayOnImage":"!1","reqFilterBgColor":"#FFFFFFFF","reqBorderColorIsOn":"!1","reqFilterBorderColor":"#000000FF","reqCTitleColorIsOn":"!1","reqFilterCTitleColor":"#000000FF","reqCTextColorIsOn":"!1","reqFilterCTextColor":"#000000FF","reqATitleColorIsOn":"!1","reqFilterATitleColor":"#000000FF","reqATextColorIsOn":"!1","reqFilterATextColor":"#000000FF","reqFilterVisibleIsOn":"!1","rowBorderRadiusTopLeft":0,"rowBorderRadiusTopRight":0,"rowBorderRadiusBottomRight":0,"rowBorderRadiusBottomLeft":0,"rowBorderRadiusIsPixels":"!0","rowOverflowIsOn":"!0","rowBorderIsOn":"!1","rowBorderColor":"red","rowBorderStyle":"solid","rowBorderWidth":2,"objectBorderRadiusTopLeft":0,"objectBorderRadiusTopRight":0,"objectBorderRadiusBottomRight":0,"objectBorderRadiusBottomLeft":0,"objectBorderRadiusIsPixels":"!0","objectOverflowIsOn":"!0","objectBorderIsOn":"!1","objectBorderColor":"red","objectBorderStyle":"solid","objectBorderWidth":2,"objectImgBorderRadiusTopLeft":0,"objectImgBorderRadiusTopRight":0,"objectImgBorderRadiusBottomRight":0,"objectImgBorderRadiusBottomLeft":0,"objectImgBorderRadiusIsPixels":"!0","objectImgBorderIsOn":"!1","objectImgBorderColor":"red","objectImgBorderStyle":"solid","objectImgBorderWidth":2,"rowImgBorderRadiusTopLeft":0,"rowImgBorderRadiusTopRight":0,"rowImgBorderRadiusBottomRight":0,"rowImgBorderRadiusBottomLeft":0,"rowImgBorderRadiusIsPixels":"!0","rowImgBorderIsOn":"!1","rowImgBorderColor":"red","rowImgBorderStyle":"solid","rowImgBorderWidth":2,"backPackWidth":1200,"multiChoiceCounterPosition":0,"multiChoiceCounterSize":170}}'''