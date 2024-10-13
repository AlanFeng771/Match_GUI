import numpy as np
import cv2
DEFAULT_WINDOW_LEVEL = -300
DEFAULT_WINDOW_WIDTH = 1400

CATEGORIES = {  
                'Incomplete':[],
                'Negative (0)':['No lung nodules', 'complete nodule', 'central nodule', 'popcorn nodule', 'fat containing nodule'], 
                'Benign (1)':['Perifissural nodule', 'Solid nodule', 'Part solid nodule', 'Non solid nodule (GGN)'],
                'Probably Benign (2)':['Solid nodule', 'Part solid nodule', 'Non solid nodule'], 
                'Suspicious (3)':['Solid nodule', 'Part solid nodule', 'Endobronchial nodule'], 
                'Very Suspicious (4)':['Solid nodule', 'Part solid nodule'],
                'Confuse':[]
            }

def get_HU_MIN_MAX(window_level: int, window_width: int):
        hu_min = window_level - window_width // 2
        hu_max = window_level + window_width // 2
        return hu_min, hu_max

def normalize_raw_image(image: np.ndarray, window_level: int = DEFAULT_WINDOW_LEVEL, window_width: int = DEFAULT_WINDOW_WIDTH) -> np.ndarray:
    hu_min, hu_max = get_HU_MIN_MAX(window_level, window_width)    
    image = np.clip(image, hu_min, hu_max)
    image = image - hu_min
    image = image.astype(np.float32) / (hu_max - hu_min)
    image = image * 255
    image = image.astype(np.uint8)
    # print('max:', np.max(image))
    # print('min:', np.min(image))
    return image

def get_contour_from_mask(mask: np.ndarray) -> np.ndarray:
    mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)[1]  # Ensure binary mask
    contour = cv2.Canny(mask, 100, 200)
    return contour