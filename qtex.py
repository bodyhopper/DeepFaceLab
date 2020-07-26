import numpy as np
from qtpy.QtCore import *
from qtpy.QtGui import *

def QImage_from_np(img):
    if img.dtype != np.uint8:
        raise ValueError("img should be in np.uint8 format")
        
    h,w,c = img.shape
    if c == 3:
        fmt = QImage.Format_BGR888
    elif c == 4:
        fmt = QImage.Format_ARGB32
    else:
      raise ValueError("unsupported channel count")  
    
    return QImage(img.data, w, h, c*w, fmt )
        
def QPixmap_from_np(img):    
    return QPixmap.fromImage(QImage_from_np(img))
    
def QPoint_from_np(n):
    return QPoint(*n.astype(np.int))
    
def QPoint_to_np(q):
    return np.int32( [q.x(), q.y()] )
    
def QSize_to_np(q):
    return np.int32( [q.width(), q.height()] )