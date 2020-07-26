import sys
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from core import pathex
from core.cv2ex import *

from qtex import *
from IEShapes import *
import time

class ImagePreviewSequenceBar(QFrame):
    def __init__(self, preview_images_count, image_width):
        super().__init__()
        self.preview_images_count = preview_images_count = max(1, preview_images_count + (preview_images_count % 2 -1) )

        self.image_width = image_width

        black_img = QImage(np.zeros( (64,64,3) ).data, 64, 64, 3*64, QImage.Format_RGB888)

        self.setFrameShape(QFrame.StyledPanel)

        self.image_containers = [ QLabel() for i in range(preview_images_count)]


        main_frame_l_cont_hl = QGridLayout()

        for i in range(len(self.image_containers)):
            main_frame_l_cont_hl.addWidget (self.image_containers[i], 0, i)
            self.image_containers[i].setPixmap( QPixmap.fromImage(black_img) )

        self.prev_image_containers = self.image_containers[:preview_images_count//2]
        self.next_image_containers = self.image_containers[preview_images_count//2:]


        main_frame_l_cont = QWidget()
        main_frame_l_cont.setSizePolicy ( QSizePolicy.Fixed, QSizePolicy.Fixed )
        main_frame_l_cont.setLayout (main_frame_l_cont_hl)

        main_frame_l = QHBoxLayout()
        main_frame_l.addWidget(main_frame_l_cont, alignment=Qt.AlignCenter)

        self.setLayout(main_frame_l)#

    def update_images(self, prev_images, next_images):
        pass


class PolygonMode(IntEnum):
    EXCLUDE = 0
    INCLUDE = 1
    
class OpMode(IntEnum):
    NONE = 0
    POINTS = 1   
    
class Canvas(QWidget):
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qp = QPainter()
        self.initialized = False

    def initialize(self, qimg, lookat_p=None, view_scale=None, ie_shapes=None ):
        self.img_pixmap = QPixmap.fromImage(qimg)
        self.img_wh = QSize_to_np (self.img_pixmap.size())

        if lookat_p is None:
            lookat_p = self.img_wh / 2
        self.lookat_p = lookat_p

        if view_scale is None:
            view_scale = 1.0
        self.view_scale = view_scale
        
        if ie_shapes is None:
            ie_shapes = IEShapes()
        self.ie_shapes = ie_shapes
        
        self.scroll_start_p = None
        
        
        self.ie_shape_selected = None
        self.ie_shape_include_type = IEIncludeType.INCLUDE
        self.op_mode = OpMode.NONE

        
        self.setMouseTracking(True)        
        self.initialized = True
        self.update()

    def finalize(self):
        if self.initialized:
            self.img_pixmap = None
            self.setMouseTracking(False)
            self.setFocusPolicy(Qt.NoFocus)
            self.initialized = False
            self.update()
            
    def is_initialized(self):
        return self.initialized
        
    def undo(self):
        
        if self.op_mode == OpMode.POINTS:  
            
            if self.ie_shape_selected.undo() == 0:
                pass
            
            self.update()
    
    def redo(self):
        pass

    def set_op_mode(self, op_mode):
        
        self.op_mode = op_mode
        
    def keyPressEvent(self, ev):
        super().keyPressEvent(ev)

        if not self.initialized:
            return

        key = ev.key()
        mods = ev.modifiers()
        
        if key == Qt.Key_Z:
            if mods == Qt.ControlModifier:
                self.undo()
            elif mods == Qt.ControlModifier | Qt.ShiftModifier:                
                self.redo()   
            
                
        elif key == Qt.Key_1:
            if self.op_mode == OpMode.NONE:
                self.op_mode = OpMode.POINTS
                
                #if self.ie_shape_selected is None:
                #    self.ie_shape_selected = self.ie_shapes.add_polygon ( self.ie_shape_include_type )
        
        print( f"Canvas {key}")
        #Qt.Key_Return

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)

        if not self.initialized:
            return

        btn = ev.button()
        pos = QPoint_to_np(ev.pos())
        if btn == Qt.LeftButton:
            img_pos = self.cli_to_img_point(pos)
            
            if self.op_mode == OpMode.NONE:
                self.set_op_mode(OpMode.POINTS)
                
                if self.ie_shape_selected is None:
                    self.ie_shape_selected = self.ie_shapes.add_polygon ( self.ie_shape_include_type )
                 
            if self.op_mode == OpMode.POINTS:  
                img_pos = self.cli_to_img_point(pos)
                
                self.ie_shape_selected.add_point(*img_pos)
                
                self.update()
                
                    
        elif btn == Qt.MiddleButton:                  
            self.scroll_start_p = QPoint_to_np(ev.pos())
            self.scroll_lookat_p = self.lookat_p
        
        

    def mouseReleaseEvent(self, ev):
        super().mouseReleaseEvent(ev)

        if not self.initialized:
            return

        btn = ev.button()
        if btn == Qt.LeftButton:
            pass
        elif btn == Qt.MiddleButton:
            self.scroll_start_p = None

    def mouseMoveEvent(self, ev):
        super().mouseMoveEvent(ev)

        if not self.initialized:
            return
        
        if self.scroll_start_p is not None:
            delta_p = self.cli_to_img_point (QPoint_to_np(ev.pos())) - self.cli_to_img_point (self.scroll_start_p)            
            self.lookat_p = self.scroll_lookat_p - delta_p            
            self.update()


    def wheelEvent(self, ev):
        super().wheelEvent(ev)

        if not self.initialized:
            return

        mods = ev.modifiers()
        delta = ev.angleDelta()

        #if mods == Qt.ControlModifier:
        pos = QPoint_to_np(ev.pos())

        sign = np.sign( delta.y() )

        prev_img_pos = self.cli_to_img_point (pos)

        delta_scale = sign*0.2 + sign * self.view_scale / 10.0
        self.view_scale = np.clip(self.view_scale + delta_scale, 1.0, 20.0)# #, ev.pos())

        new_img_pos = self.cli_to_img_point (pos)

        if sign > 0:
            self.lookat_p += (prev_img_pos-new_img_pos)#*1.5
        else:
            QCursor.setPos ( self.mapToGlobal(QPoint_from_np(self.img_to_cli_point(prev_img_pos))) )

        self.update()


    def img_to_cli_point(self, p):
        return (p - self.lookat_p) * self.view_scale + QSize_to_np(self.size())/2

    def cli_to_img_point(self, p):
        return (p - QSize_to_np(self.size())/2 ) / self.view_scale + self.lookat_p

    def img_to_cli_rect(self, rect):
        tl = QPoint_to_np(rect.topLeft())
        xy = self.img_to_cli_point(tl)
        xy2 = self.img_to_cli_point(tl + QSize_to_np(rect.size()) ) - xy
        return QRect ( *xy.astype(np.int), *xy2.astype(np.int) )



    def paintEvent(self, event):
        super().paintEvent(event)


        if not self.initialized:
            return

        qp = self.qp

        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)
        qp.setRenderHint(QPainter.HighQualityAntialiasing)
        qp.setRenderHint(QPainter.SmoothPixmapTransform)

        if self.img_pixmap is not None:
            src_rect = QRect(0, 0, *self.img_wh)
            dst_rect = self.img_to_cli_rect( src_rect )
            qp.drawPixmap(dst_rect, self.img_pixmap, src_rect)
            
        qp.setBrush(Qt.green)
        for shape in self.ie_shapes:
            
            if shape.shape_type == IEShapeType.POLYGON:
                
                for xy in shape.get_points():
                    pos = self.img_to_cli_point(xy)
                    print(xy, pos)
                    qp.drawEllipse( QPoint_from_np(pos), 5,5 )

        
        qp.end()

    def drawText(self, event, qp):

        qp.setPen(QColor(168, 34, 3))
        qp.setFont(QFont('Decorative', 10))
        qp.drawText( QRect(0,0,100,100), 0, "123")


class MainWindow(QWidget):
    
    
    def __init__(self, input_dirpath):
        super().__init__()

        self.input_dirpath = input_dirpath

        self.initialize_ui()
        
        self.hot_key_prev = Qt.Key_A
        self.hot_key_next = Qt.Key_D
        
        self.images_paths = pathex.get_image_paths(input_dirpath)
        self.images_paths_done = []
        
        self.setFocusPolicy(Qt.WheelFocus)
        
        self.process_next_image()
    

    def process_prev_image(self):        
        if self.canvas.is_initialized():
            image_path = self.images_paths[0]            
            
            self.canvas.finalize()
            
            if len(self.images_paths_done) != 0:
                self.images_paths.insert (0, self.images_paths_done.pop(-1) )
            
        if len(self.images_paths) != 0:
            image_path = self.images_paths[0]
            
            img = cv2_imread(image_path)
            
            self.canvas.initialize ( QImage_from_np(img) )   
            
    def process_next_image(self):
        
        if self.canvas.is_initialized():            
            image_path = self.images_paths[0]            
            
            self.canvas.finalize()
            
            self.images_paths_done.append(image_path)
            self.images_paths.pop(0)
                        
        if len(self.images_paths) != 0:
            image_path = self.images_paths[0]
            
            img = cv2_imread(image_path)
            
            self.canvas.initialize ( QImage_from_np(img) )   
            
        
    def keyPressEvent(self, ev):
        super().keyPressEvent(ev)

        # Force redirect key events to canvas
        self.canvas.keyPressEvent(ev)
        
        key = ev.key()
        
        if key == self.hot_key_prev:
            self.process_prev_image()
        elif key == self.hot_key_next:
            
            self.process_next_image()

    def initialize_ui(self):
        
        self.canvas_holder = QFrame()
        self.canvas_holder.setFrameShape(QFrame.StyledPanel)
        self.canvas_holder_l = QHBoxLayout()
        self.canvas_holder.setLayout(self.canvas_holder_l)
        self.canvas = Canvas()

        
        self.canvas_holder_l.addWidget(self.canvas)

        left_bar = QFrame()
        left_bar.setFrameShape(QFrame.StyledPanel)
        left_bar.setSizePolicy ( QSizePolicy.Fixed, QSizePolicy.Minimum )


        left_bar_list = QPushButton()
        left_bar_list.setText('asd')

        left_bar_l = QVBoxLayout()
        left_bar_l.addWidget ( left_bar_list )

        left_bar.setLayout(left_bar_l)
        center_l = QVBoxLayout()

        image_bar = self.image_bar = ImagePreviewSequenceBar(preview_images_count=9, image_width=64)
        image_bar.setSizePolicy ( QSizePolicy.Expanding, QSizePolicy.Fixed )

        center_l.addWidget(image_bar)
        center_l.addWidget(self.canvas_holder)


        main_l = QHBoxLayout()
        main_l.addWidget (left_bar)
        main_l.addLayout (center_l)

        self.setLayout(main_l)
        self.resize( QSize(600, 500) )

    def load_image(self):
        pass

def start(input_dirpath):
    app = QApplication([])
    app.setApplicationName("XSegEditor")
    app.setStyle('Fusion')

    # Now use a palette to switch to dark colors:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    #app.setWindowIcon(newIcon('icon'))

    win = MainWindow( input_dirpath=input_dirpath)
    win.show()
    win.raise_()
    app.exec_()

if __name__ == "__main__":

    start ( input_dirpath=Path(r'F:\DeepFaceLabCUDA9.2SSE\workspace CAGE 1\data_src\aligned') )