import pytesseract
from PIL import Image

image_path = '/Users/lll/workspaces/videos-gen/33.png'
try:
    image = Image.open(image_path)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    text_eng = pytesseract.image_to_string(image, lang='eng')
    print('OCR识别结果:')
    print(repr(text_eng.strip()))
    
except Exception as e:
    print('OCR错误:', e)