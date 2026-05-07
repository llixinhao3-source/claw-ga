#!/Users/sevik/Desktop/pet_venv/bin/python3
import sys, os, random, threading, re
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QTextEdit, QPushButton, QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter

PET_ROOT = Path.home() / "Desktop" / "ip" / "sprites_yoffset3"
GA_DIR = Path.home() / "Desktop" / "ip" / "GenericAgent"
FRAME_SIZE = 100

STATE_CONFIG = {
    "idle_front": {"dir": "idle_front", "fps": 8, "loop": True},
    "walk_right": {"dir": "walk_right", "fps": 10, "loop": True},
    "walk_left": {"dir": "walk_left", "fps": 10, "loop": True},
    "walk_front": {"dir": "walk_front", "fps": 10, "loop": True},
    "slide": {"dir": "slide", "fps": 10, "loop": False},
    "run": {"dir": "run", "fps": 12, "loop": True},
    "work_sleep": {"dir": "work_sleep", "fps": 6, "loop": True},
}

class BrainThread(QThread):
    reply_ready = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.ga_dir = GA_DIR
        self.agent = None
        self.running = False

    def run(self):
        sys.path.insert(0, str(self.ga_dir))
        try:
            from agentmain import GeneraticAgent
            print("[Brain] Connecting...", flush=True)
            self.agent = GeneraticAgent()
            print("[Brain] Agent created!", flush=True)
            sys.stdout.flush()
            # Start agent.run() in a separate daemon thread
            import threading
            def run_agent():
                print("[Brain] Running agent.run()...", flush=True)
                try:
                    self.agent.run()
                    print("[Brain] agent.run() ended", flush=True)
                except Exception as e:
                    print(f"[Brain] agent.run() exception: {e}", flush=True)
            t = threading.Thread(target=run_agent, daemon=True)
            t.start()
            # Wait a moment for agent to initialize
            import time
            time.sleep(2)
            self.running = True
            print("[Brain] Agent ready, running=True", flush=True)
        except Exception as e:
            print(f"[Brain] Exception: {e}", flush=True)
            self.running = False
        pass

    def ask(self, text):
        print(f"[Brain] ask() called with: {text[:50]}, running={self.running}, agent={hasattr(self, 'agent')}", flush=True)
        if not self.running or not self.agent:
            print("[Brain] Not ready, emitting 未就绪", flush=True)
            self.reply_ready.emit("[未就绪]")
            return
        def bg():
            try:
                dq = self.agent.put_task(text)
                while True:
                    msg = dq.get(timeout=120)
                    if isinstance(msg, dict) and 'done' in msg:
                        content = msg['done']
                        content = re.sub(r'\*\*``.*?``\*\*', '', content, flags=re.DOTALL)
                        content = re.sub(r'\*\*LLM Running.*?\*\*', '', content, flags=re.DOTALL)
                        content = re.sub(r'<think>.*?', '', content, flags=re.DOTALL)
                        content = re.sub(r'\[Info\].*', '', content)
                        content = content.strip()
                        self.reply_ready.emit(content if content else "[无回复]")
                        break
                    elif isinstance(msg, dict) and 'next' in msg:
                        chunk = msg['next']
                        if chunk:
                            self.reply_ready.emit(chunk.strip())
            except Exception as e:
                self.reply_ready.emit(f"[错误]")
        threading.Thread(target=bg, daemon=True).start()

class Pet(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")
        
        self.current_state = "idle_front"
        self.frame_index = 0
        self.frames = []
        self.is_thinking = False
        self.is_dragging = False
        self.drag_offset = QPoint(0, 0)
        self.last_pos = None
        self.collapsed = False
        
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout
        central = QWidget(self)
        self.setCentralWidget(central)
        self.layout = QVBoxLayout(central)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Reply bubble (above pet)
        self.bubble = QTextEdit(central)
        self.bubble.setReadOnly(True)
        self.bubble.setFixedSize(280, 50)
        self.bubble.setStyleSheet("background: rgba(255,255,255,240); border: 1px solid rgba(200,200,200,150); border-radius: 10px; font-size: 13px; color: #333; padding: 8px;")
        self.bubble.setVisible(False)
        
        # Pet sprite label
        self.label = QLabel(central)
        self.label.setFixedSize(FRAME_SIZE, FRAME_SIZE)
        self.label.setStyleSheet("background: transparent; padding: 0; margin: 0; border: none;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Input area (below pet)
        self.input_widget = QWidget(central)
        self.input_layout = QVBoxLayout(self.input_widget)
        self.input_layout.setContentsMargins(0, 0, 0, 0)
        self.input_layout.setSpacing(4)
        
        self.input_field = QTextEdit(self.input_widget)
        self.input_field.setFixedSize(280, 80)
        self.input_field.setPlaceholderText("输入消息...")
        self.input_field.setStyleSheet("background: rgba(255,255,255,240); border: 1px solid #ccc; border-radius: 10px; font-size: 13px; padding: 8px;")
        self.input_field.installEventFilter(self)
        
        self.send_btn = QPushButton("发送", self.input_widget)
        self.send_btn.setFixedSize(280, 36)
        self.send_btn.setStyleSheet("background: #4CAF50; color: white; border: none; border-radius: 8px; font-size: 13px;")
        self.send_btn.clicked.connect(self.on_send)
        
        self.input_layout.addWidget(self.input_field, 0, Qt.AlignmentFlag.AlignCenter)
        self.input_layout.addWidget(self.send_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.layout.addWidget(self.bubble, 0, Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label, 0, Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.input_widget, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.resize(FRAME_SIZE, FRAME_SIZE)
        
        self.load_frames("idle_front")
        self.update_frame()
        
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.next_frame)
        self.anim_timer.start(1000 // 12)
        
        self.behavior_timer = QTimer()
        self.behavior_timer.timeout.connect(self.random_behavior)
        self.behavior_timer.start(3000)
        
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.move_window)
        self.move_timer.start(100)
        
        screen = QApplication.primaryScreen().geometry()
        self.move(QPoint(screen.width() - FRAME_SIZE - 20, screen.height() // 2))
        
        self.brain = BrainThread()
        self.brain.reply_ready.connect(self.on_brain_reply)
        self.brain.start()
        
        self.show()
        
    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not event.modifiers():
                self.on_send()
                return True
        return super().eventFilter(obj, event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.last_pos = event.globalPosition().toPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            self.toggle_chat()
        
    def mouseDoubleClickEvent(self, event):
        """Double click to collapse/expand chat boxes"""
        self.toggle_collapse()
        
    def toggle_collapse(self):
        """Collapse or expand the chat boxes"""
        self.collapsed = not self.collapsed
        
        if self.collapsed:
            # Collapse: hide input and bubble, resize to just pet
            self.bubble.setVisible(False)
            self.input_widget.setVisible(False)
            self.resize(FRAME_SIZE, FRAME_SIZE)
        else:
            # Expand: show input and bubble
            self.bubble.setVisible(True)
            self.input_widget.setVisible(True)
            total_h = 60 + 4 + FRAME_SIZE + 4 + 80 + 4 + 36  # bubble + gap + pet + gap + input + gap + btn
            self.resize(280, total_h)
        
    def toggle_chat(self):
        """Right click - just toggle bubble visibility if there's a reply"""
        if self.bubble.toPlainText():
            self.bubble.setVisible(not self.bubble.isVisible())
        
    def on_send(self):
        text = self.input_field.toPlainText().strip()
        if text:
            self.is_thinking = True
            self.bubble.setPlainText("思考中...")
            self.bubble.setVisible(True)
            self.input_field.clear()
            self.brain.ask(text)
        
    def on_brain_reply(self, text):
        self.is_thinking = False
        self.bubble.setPlainText(text)
        self.bubble.setVisible(True)
        self.collapsed = False
        total_h = 60 + 4 + FRAME_SIZE + 4 + 80 + 4 + 36
        self.resize(280, total_h)
        
    def load_frames(self, state):
        config = STATE_CONFIG.get(state)
        if not config:
            return
        folder = PET_ROOT / config["dir"]
        if not folder.exists():
            return
        files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
        self.frames = [QPixmap(str(folder / f)) for f in files]
        self.current_state = state
        
    def update_frame(self):
        if self.frames:
            pixmap = self.frames[self.frame_index].scaled(FRAME_SIZE, FRAME_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.label.setPixmap(pixmap)
            self.label.resize(FRAME_SIZE, FRAME_SIZE)
            self.label.setFixedSize(FRAME_SIZE, FRAME_SIZE)
            
    def next_frame(self):
        if self.frames:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.update_frame()
            
    def random_behavior(self):
        if self.is_thinking:
            return
        states = list(STATE_CONFIG.keys())
        state = random.choice(states)
        self.load_frames(state)
        self.frame_index = 0
        
    def move_window(self):
        if self.is_thinking or self.collapsed:
            return
        if self.current_state == "walk_left":
            self.move(self.x() - 3, self.y())
        elif self.current_state == "walk_right":
            self.move(self.x() + 3, self.y())
        elif self.current_state == "walk_front":
            self.move(self.x(), self.y() + 2)
        elif self.current_state == "run":
            self.move(self.x() + 5, self.y())
        
        screen = QApplication.primaryScreen().geometry()
        if self.x() < 0: self.move(0, self.y())
        if self.x() > screen.width() - FRAME_SIZE: self.move(screen.width() - FRAME_SIZE, self.y())
        if self.y() < 0: self.move(self.x(), 0)
        if self.y() > screen.height() - FRAME_SIZE: self.move(self.x(), screen.height() - FRAME_SIZE)
        
    def mouseMoveEvent(self, event):
        if self.is_dragging and self.last_pos:
            delta = event.globalPosition().toPoint() - self.last_pos
            self.move(self.pos() + delta)
            self.last_pos = event.globalPosition().toPoint()
            
    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        self.last_pos = None

if __name__ == '__main__':
    app = QApplication([])
    pet = Pet()
    app.exec()
