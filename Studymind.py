from PyQt5.QtWidgets import QMainWindow ,QApplication ,QVBoxLayout ,QHBoxLayout ,QWidget ,QPushButton ,QFileDialog ,QFrame ,QLabel ,QStackedWidget ,QGroupBox ,QLineEdit ,QSpinBox ,QScrollArea ,QMessageBox ,QRadioButton ,QButtonGroup ,QTextEdit ,QListWidget ,QShortcut ,QListWidgetItem ,QInputDialog ,QDialogButtonBox ,QComboBox ,QDialog ,QFormLayout ,QFileSystemModel ,QTreeView ,QSplitter 
from PyQt5.QtWebEngineWidgets import QWebEngineView ,QWebEngineSettings 
from PyQt5.QtCore import QUrl ,QPropertyAnimation ,QEasingCurve ,Qt ,QTimer ,QUrl ,QDir ,Qt ,pyqtSignal , QThread
from google import genai 
from PyQt5.QtGui import QFont ,QKeySequence , QPixmap
import os ,json ,re ,sys , base64 , tempfile
from PyQt5.QtPrintSupport import QPrinter 


def get_data_file_path():
    if os.name == "nt" and os.getenv("APPDATA"):
        base_dir = os.path.join(os.getenv("APPDATA"), "StudyMind")
    else:
        base_dir = os.path.join(os.path.expanduser("~"), ".config", "StudyMind")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "studymind_data.json")

DATA_FILE = get_data_file_path()

MODERN_STUDY_THEME ="""
    QWidget {
        background-color: #0f172a; 
        color: #f8fafc;
        font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    }

    QFrame#Sidebar {
        background-color: #020617;
        border-right: 1px solid #1e293b;
    }
    
    QFrame#Sidebar QPushButton {
        background-color: transparent;
        text-align: left;
        padding: 14px 20px;
        border-radius: 8px;
        margin: 4px 8px;
        font-weight: 600;
        color: #94a3b8;
        border: none;
    }
    QFrame#Sidebar QPushButton:hover {
        background-color: #1e293b;
        color: #f8fafc;
    }

    QTreeView {
        background-color: #0f172a;
        border: none;
        padding: 5px;
        font-size: 20px;  
    }
    QTreeView::item {
        padding: 6px 4px;
    }
    QTreeView::item:hover {
        background-color: #1e293b;
        border-radius: 4px;
    }
    QTreeView::item:selected {
        background-color: #38bdf8;
        color: #020617;
        border-radius: 4px;
        font-weight: bold;
    }
"""

class StudyMind(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StudyMind")
        self.resize(1200 ,800)
        self.setStyleSheet(MODERN_STUDY_THEME)
        self.sidebar_fraction =7 
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0 ,0 ,0 ,0)
        self.main_layout.setSpacing(0)
        self.create_sidebar()
        self.content_container = QWidget()
        self.content_container_layout = QVBoxLayout(self.content_container)
        self.content_container_layout.setContentsMargins(0 ,0 ,0 ,0)
        self.content_container_layout.setSpacing(0)
        self.pages = QStackedWidget()
        self.pages.setObjectName("MainPagesStack")

        self.pdf_page =PDF_Reader()
        self.note_page =Note_taker()
        self.quiz_page = QuizApp()
        self.flashcard_page =FlashcardApp()
        self.ai_chat_page = Ask_Ai()
        self.settings_page = SettingsPage()

        self.pdf_page.on_generate_quiz = self.open_quiz_from_pdf 
        self.pdf_page.on_summarize_pdf = self.summarize_pdf_action
        self.pdf_page.on_generate_flashcards = self.generate_flashcards_action

        self.pages.addWidget(self.pdf_page)
        self.pages.addWidget(self.note_page)
        self.pages.addWidget(self.quiz_page)
        self.pages.addWidget(self.flashcard_page)
        self.pages.addWidget(self.ai_chat_page)
        self.pages.addWidget(self.settings_page)

        self.content_container_layout.addWidget(self.pages)
        self.main_layout.addWidget(self.content_container)


        self.global_toggle_btn = QPushButton("☰",self.content_container)
        self.global_toggle_btn.setToolTip("Toggle Menu Sidebar")
        self.global_toggle_btn.setFixedSize(40 ,40)
        self.global_toggle_btn.move(0 ,0)
        self.global_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                border: 1px solid #334155;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #f8fafc;
            }
        """)
        self.global_toggle_btn.raise_()

        self.sidebar_anim_min = QPropertyAnimation(self.sidebar ,b"minimumWidth")
        self.sidebar_anim_max = QPropertyAnimation(self.sidebar ,b"maximumWidth")

        self.global_toggle_btn.clicked.connect(self.toggle_navigation_sidebar)
        self.btn_pdf.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.btn_dashboard.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        self.btn_ai.clicked.connect(lambda: self.pages.setCurrentIndex(2))
        self.btn_flashcard.clicked.connect(lambda: self.pages.setCurrentIndex(3))
        self.ai_chat_btn.clicked.connect(lambda: self.pages.setCurrentIndex(4))
        self.Settings_btn.clicked.connect(lambda: self.pages.setCurrentIndex(5))
        
        QTimer.singleShot(200, self.check_api_key_on_launch)



    def create_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0 ,10 ,0 ,10)
        sidebar_layout.setSpacing(5)

        logo = QLabel("🧠 StudyMind")
        logo.setStyleSheet("font-size: 22px; font-weight: 800; color: #38bdf8; padding: 20px; padding-left: 25px;")
        sidebar_layout.addWidget(logo)

        self.btn_pdf = QPushButton("📖 PDF Reader")
        self.btn_dashboard = QPushButton("📝 Note Taker")
        self.btn_ai = QPushButton("🎲 Quiz Generator")
        self.btn_flashcard = QPushButton("🗂️ Flashcards")
        self.ai_chat_btn = QPushButton("Ai chat")
        self.Settings_btn = QPushButton("settings")

        for btn in [self.btn_pdf ,self.btn_dashboard ,self.btn_ai ,self.btn_flashcard, self.ai_chat_btn , self.Settings_btn]:
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        self.main_layout.addWidget(self.sidebar)


    def toggle_navigation_sidebar(self):
        current_width =self.sidebar.width()
        target_fractional_width =self.width()//self.sidebar_fraction 
        end_width =0 if current_width >0 else target_fractional_width 


        self.sidebar_anim_min.stop()
        self.sidebar_anim_max.stop()

        self.sidebar_anim_min.setDuration(250)
        self.sidebar_anim_min.setStartValue(current_width)
        self.sidebar_anim_min.setEndValue(end_width)
        self.sidebar_anim_min.setEasingCurve(QEasingCurve.InOutQuad)


        self.sidebar_anim_max.setDuration(250)
        self.sidebar_anim_max.setStartValue(current_width)
        self.sidebar_anim_max.setEndValue(end_width)
        self.sidebar_anim_max.setEasingCurve(QEasingCurve.InOutQuad)


        self.sidebar_anim_min.start()
        self.sidebar_anim_max.start()

    def resizeEvent(self ,event):
        super().resizeEvent(event)
        if self.sidebar.width()>0 and self.sidebar_anim_min.state()== QPropertyAnimation.Stopped :
            calculated_width =self.width()//self.sidebar_fraction 
            self.sidebar.setFixedWidth(calculated_width)

    def open_quiz_from_pdf(self ,pdf_path ,num_questions =None):
        if not pdf_path or not os.path.exists(pdf_path):
            QMessageBox.warning(self ,"No PDF Open","Please open a PDF in the PDF reader first.")
            return 
        self.quiz_page.load_pdf_for_quiz(pdf_path ,num_questions =num_questions)
        self.pages.setCurrentIndex(2)

    def summarize_pdf_action(self, pdf_path):
        if not hasattr(self, "ai_client"):
            from google import genai
            pdf_config = AppConfig.load_namespace("pdf_reader")
            user_key = pdf_config.get("api_key", API_KEY) 
            if not user_key:
                QMessageBox.warning(self, "API Key Missing", "Please add your Gemini API key in Settings first.")
                return
            self.ai_client = genai.Client(api_key=user_key)
        
        self.pdf_page.Summerize_Pdf_btn.setEnabled(False)
        self.pdf_page.Summerize_Pdf_btn.setText("Starting Process...")
        self.summary_thread = Summeriser(self.ai_client , pdf_path)
        self.summary_thread.progress_signal.connect(self.on_summary_progress)
        self.summary_thread.error_signal.connect(self.on_summary_error)
        self.summary_thread.success_signal.connect(self.on_summary_success)

        self.summary_thread.start()

    def generate_flashcards_action(self, pdf_path):
        started = self.flashcard_page.generate_from_pdf(
            pdf_path,
            progress_slot=self.on_flashcard_progress,
            success_slot=self.on_flashcard_success,
            error_slot=self.on_flashcard_error
        )

        if started:
            self.pdf_page.generate_flashcards_btn.setEnabled(False)
            self.pdf_page.generate_flashcards_btn.setText("Generating...")

    def on_summary_progress(self , status_message):
        self.pdf_page.Summerize_Pdf_btn.setEnabled(False)
        self.pdf_page.Summerize_Pdf_btn.setText("Starting Process...")
        self.pdf_page.Summerize_Pdf_btn.setText(status_message)

    def on_summary_error(self , error_message):
        QMessageBox.critical(self , "Summary Error 67" , f"Something went wrong:\n{error_message}")
        self.pdf_page.Summerize_Pdf_btn.setEnabled(True)
        self.pdf_page.Summerize_Pdf_btn.setText("Summarize PDF")

    def on_summary_success(self , title , html_summary):
        self.pdf_page.Summerize_Pdf_btn.setEnabled(True)
        self.pdf_page.Summerize_Pdf_btn.setText("Summarize PDF")
        self.note_page.save_note()
        self.note_page.new_note()
        self.note_page.title_box.setText(title)
        current_font = self.note_page.text_box.font()
        current_font.setPointSize(14)
        self.note_page.text_box.setFont(current_font)
        self.note_page.text_box.setHtml(html_summary)
        self.note_page.text_box.zoomIn(3)

        self.pages.setCurrentWidget(self.note_page)
        QMessageBox.information(self , "Success" , "Summary successfully moved to your Note Taker dashboard!")

    def on_flashcard_progress(self, status_text):
        self.flashcard_page.card_display.setText(status_text)
        self.pdf_page.generate_flashcards_btn.setText("Generating...")
        self.pdf_page.generate_flashcards_btn.setEnabled(False)

    def on_flashcard_success(self, category_name, cards):
        unique_name = self.flashcard_page.make_unique_category_name(category_name)
        self.flashcard_page.flashcards[unique_name] = cards
        self.flashcard_page.refresh_categories()
        self.flashcard_page.current_category = unique_name
        self.flashcard_page.current_index = 0
        self.flashcard_page.load_deck()
        self.flashcard_page.stack.setCurrentWidget(self.flashcard_page.deck_page)
        self.flashcard_page.save_data()
        self.pdf_page.generate_flashcards_btn.setEnabled(True)
        self.pdf_page.generate_flashcards_btn.setText("Generate Flashcards")
        self.pages.setCurrentWidget(self.flashcard_page)
        QMessageBox.information(self, "Flashcards Generated", f"{len(cards)} flashcards were added to '{unique_name}'.")

    def on_flashcard_error(self, error_message):
        self.flashcard_page.card_display.setText("Flashcard generation failed")
        self.pdf_page.generate_flashcards_btn.setEnabled(True)
        self.pdf_page.generate_flashcards_btn.setText("Generate Flashcards")
        QMessageBox.critical(self, "Flashcard Error", f"Something went wrong while generating flashcards:\n{error_message}")

    def check_api_key_on_launch(self):
        pdf_config = AppConfig.load_namespace("pdf_reader")
        current_key = pdf_config.get("api_key", "").strip()

        if not current_key:
            QMessageBox.information(
                self,
                "API Configuration Required",
                "Welcome to StudyMind!\n\nTo unlock the integrated AI assistance tools, you must provide a Gemini API Key.\n\nClick OK to visit the configuration dashboard."
            )
            if hasattr(self, 'pages') and hasattr(self, 'settings_page'):
                self.pages.setCurrentWidget(self.settings_page)

CONFIG_FILE ="studymind_config.json"

class AppConfig:
    @staticmethod
    def _get_defaults():
        return {
            "pdf_reader": {
                "last_directory": "",
                "last_opened_pdf": "",
                "last_page": 0,
                "api_key": ""
            },
            "note_taker": {
                "notes": {}
            },
            "flashcards": {
                "decks": {}
            }
        }
    

    @staticmethod
    def load_namespace(namespace):
        defaults = AppConfig._get_defaults()
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    full_data = json.load(f)
                    if namespace in full_data:
                        defaults[namespace].update(full_data[namespace])
            except Exception as e:
                print(f"Error loading {namespace} data: {e}")
        return defaults[namespace]
    
    @staticmethod
    def save_namespace(namespace, namespace_data):
        try:
            full_data = AppConfig._get_defaults()
            if os.path.exists(DATA_FILE):
                try:
                    with open(DATA_FILE, "r", encoding="utf-8") as f:
                        full_data.update(json.load(f))
                except Exception:
                    pass
            
            full_data[namespace] = namespace_data
            base_dir = os.path.dirname(DATA_FILE)
            with tempfile.NamedTemporaryFile('w', dir=base_dir, delete=False, encoding='utf-8') as tf:
                json.dump(full_data, tf, indent=4, ensure_ascii=False)
                temp_name = tf.name
            os.replace(temp_name, DATA_FILE)
        except Exception as e:
            print(f"Error saving namespace {namespace}: {e}")
    


class PDF_Reader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = AppConfig.load_namespace("pdf_reader")
        self.PDF_reader = QWebEngineView()
        self.open_dir_btn = QPushButton("Open Workspace")
        self.toggle_sidebar_btn = QPushButton("📁 Toggle Workspace")
        self.dark_btn = QPushButton("Dark Mode")
        self.generate_quiz_btn = QPushButton("Generate Quiz")
        self.generate_flashcards_btn = QPushButton("Generate Flashcards")
        self.Summerize_Pdf_btn = QPushButton("Summarize PDF")
        self.sidebar_visible =True 
        self.dir_model = QFileSystemModel()
        self.dir_model.setFilter(QDir.NoDotAndDotDot |QDir.AllDirs |QDir.Files)
        self.dir_model.setNameFilters(["*.pdf"])
        self.dir_model.setNameFilterDisables(False)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.dir_model)
        self.tree_view.hideColumn(1)
        self.tree_view.hideColumn(2)
        self.tree_view.hideColumn(3)
        self.tree_view.setHeaderHidden(True)
        self.is_dark =False 

        self.InitUi()
        self.webview_config()
        self.Style()
        self.restore_previous_session()
        self.PDF_reader.loadFinished.connect(self.on_load_finished)

    def InitUi(self):
        self.setWindowTitle("StudyMind Dashboard")
        container = QWidget()
        main_layout = QVBoxLayout()


        menu_layout = QHBoxLayout()
        menu_layout.addStretch()
        menu_layout.addWidget(self.open_dir_btn)
        menu_layout.addWidget(self.toggle_sidebar_btn)
        menu_layout.addWidget(self.dark_btn)
        menu_layout.addWidget(self.generate_quiz_btn)
        menu_layout.addWidget(self.generate_flashcards_btn)
        menu_layout.addWidget(self.Summerize_Pdf_btn)
        menu_layout.addStretch()
        main_layout.addLayout(menu_layout)
        self.splitter = QSplitter(Qt.Horizontal)
        self.viewer_container = QWidget()
        viewer_layout = QVBoxLayout(self.viewer_container)
        viewer_layout.setContentsMargins(0 ,0 ,0 ,0)
        viewer_layout.addWidget(self.PDF_reader)

        self.sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(0 ,0 ,0 ,0)
        sidebar_layout.addWidget(self.tree_view)
        self.splitter.addWidget(self.viewer_container)
        self.splitter.addWidget(self.sidebar_widget)
        self.splitter.setSizes([980 ,220 ])

        main_layout.addWidget(self.splitter)
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.open_dir_btn.clicked.connect(self.load_directory)
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)
        self.dark_btn.clicked.connect(self.apply_dark_mode)
        self.generate_quiz_btn.clicked.connect(self.generate_quiz)
        self.generate_flashcards_btn.clicked.connect(self.generate_flashcards)
        self.tree_view.clicked.connect(self.on_file_selected)
        self.Summerize_Pdf_btn.clicked.connect(self.trigger_summary)


    def webview_config(self):
        self.PDF_reader.settings().setAttribute(QWebEngineSettings.PluginsEnabled ,True)
        self.PDF_reader.settings().setAttribute(QWebEngineSettings.PdfViewerEnabled ,True)

    def restore_previous_session(self):
        last_dir =self.config.get("last_directory","")
        if last_dir and os.path.exists(last_dir):
            self.dir_model.setRootPath(last_dir)
            self.tree_view.setRootIndex(self.dir_model.index(last_dir))

        last_file =self.config.get("last_opened_pdf","")
        if last_file and os.path.exists(last_file):
            self.PDF_Path =last_file 
            self.PDF_reader.setUrl(QUrl.fromLocalFile(last_file))

    def load_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self ,"Select Study Workspace Folder","")
        if dir_path :
            self.dir_model.setRootPath(dir_path)
            self.tree_view.setRootIndex(self.dir_model.index(dir_path))
            self.config ["last_directory"]=dir_path 
            AppConfig.save_namespace("pdf_reader", self.config)

    def on_file_selected(self ,index):
        file_path =self.dir_model.filePath(index)
        if os.path.isfile(file_path)and file_path.lower().endswith('.pdf'):
            self.config ["last_opened_pdf"]=file_path 
            self.config ["last_page"]=0 
            AppConfig.save_namespace("pdf_reader", self.config)
            self.PDF_reader.setUrl(QUrl.fromLocalFile(file_path))

        self.PDF_Path =file_path 

    def toggle_sidebar(self):
        if self.sidebar_visible :
            self.sidebar_widget.hide()
            self.sidebar_visible =False 
        else :
            self.sidebar_widget.show()
            self.sidebar_visible =True 
            self.splitter.setSizes([980 ,220 ])

    def on_load_finished(self):
        self.inject_dark_mode_css()
        saved_page =self.config.get("last_page",0)
        if saved_page >0 :
            jump_script =f"window.postMessage({{type: 'goToPage', page: {saved_page }}}, '*');"
            self.PDF_reader.page().runJavaScript(jump_script)
        self.track_page_index_changes()

    def load_file(self ,path):
        if not path or not os.path.exists(path):
            return 
        self.config ["last_opened_pdf"]=path 
        AppConfig.save_namespace("pdf_reader" , self.config)
        self.page_position_restored =False 

        url = QUrl.fromLocalFile(path)
        self.PDF_reader.load(url)

    def track_page_index_changes(self):
        poll_script ="document.querySelector('pdf-viewer') ? document.querySelector('pdf-viewer').shadowRoot.querySelector('viewer-pdf-toolbar').getAttribute('page-no') : '0';"
        def handle_result(result):
            if result and result.isdigit():
                page_num =int(result)
                if page_num >0 and page_num !=self.config.get("last_page",0):
                    self.config ["last_page"]=page_num 
                    AppConfig.save_namespace("pdf_reader", self.config)
        self.PDF_reader.page().runJavaScript(poll_script ,handle_result)

    def closeEvent(self ,event):
        poll_script ="document.querySelector('pdf-viewer') ? document.querySelector('pdf-viewer').shadowRoot.querySelector('viewer-pdf-toolbar').getAttribute('page-no') : '0';"
        def save_and_close(result):
            if result and result.isdigit():
                self.config ["last_page"]=int(result)
            AppConfig.save_namespace("pdf_reader", self.config)
            event.accept()
        self.PDF_reader.page().runJavaScript(poll_script ,save_and_close)

    def apply_dark_mode(self):
        self.is_dark =not self.is_dark 
        self.inject_dark_mode_css()

    def inject_dark_mode_css(self):
        if self.is_dark :
            dark_css ="""
            var style = document.getElementById('studymind-dark-style');
            if(!style) {
                style = document.createElement('style');
                style.id = 'studymind-dark-style';
                document.head.appendChild(style);
            }
            style.innerHTML = `
                html, body { background-color: #000000 !important; }
                embed { 
                    filter: invert(0.95) hue-rotate(180deg) !important; 
                    background-color: #000000 !important;
                }
            `;
            """
            self.PDF_reader.page().runJavaScript(dark_css)
        else :
            clear_css ="""
            var style = document.getElementById('studymind-dark-style');
            if(style) style.remove();
            """
            self.PDF_reader.page().runJavaScript(clear_css)


    def Style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QWidget { background-color: #121212; color: #FFFFFF; font-family: 'Segoe UI', Arial, sans-serif; }
            QPushButton { 
                background-color: #1F1F1F; border: 1px solid #333333; padding: 6px 14px; 
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2D2D2D; border: 1px solid #555555; }
            QTreeView { 
                background-color: #1A1A1A; border: none; padding: 5px;
            }
            QTreeView::item { padding: 8px 0px;}
            QTreeView::item:hover { background-color: #252526; border-radius: 3px; }
            QTreeView::item:selected { background-color: #37373D; color: white; border-radius: 3px; }
            QSplitter::handle { background-color: #252526; width: 3px; }
        """)
        self.PDF_reader.setStyleSheet("border: none;")

    def generate_quiz(self):
        pdf_path =getattr(self ,"PDF_Path","")
        if not pdf_path or not os.path.exists(pdf_path):
            QMessageBox.warning(self ,"No PDF Open","Please open a PDF in the PDF reader before generating a quiz.")
            return 

        if not hasattr(self ,"on_generate_quiz")or self.on_generate_quiz is None :
            QMessageBox.warning(self ,"Action Unavailable","Quiz generation is not connected to the main application.")
            return 

        self.on_generate_quiz(pdf_path)

    def generate_flashcards(self):
        pdf_path = getattr(self, "PDF_Path", "")
        if not pdf_path or not os.path.exists(pdf_path):
            QMessageBox.warning(self, "No PDF Open", "Please open a PDF in the reader first before generating flashcards.")
            return

        if hasattr(self, "on_generate_flashcards") and self.on_generate_flashcards is not None:
            self.on_generate_flashcards(pdf_path)
        else:
            QMessageBox.warning(self, "Action Unavailable", "Flashcard generation is not connected to the main application.")
    

    def trigger_summary(self):
        pdf_path = getattr(self, "PDF_Path", "")
        if not pdf_path or not os.path.exists(pdf_path):
            QMessageBox.warning(self,"No PDF Open" , "Please open a PDF in the reader first genius.")
            return
        
        if hasattr(self, "on_summarize_pdf") and self.on_summarize_pdf is not None:
            self.on_summarize_pdf(pdf_path)


API_KEY =""


class Summeriser(QThread):
    progress_signal = pyqtSignal(str)
    success_signal = pyqtSignal(str , str)
    error_signal = pyqtSignal(str)

    def __init__(self , client , pdf_path):
        super().__init__()
        self.client = client
        self.pdf_path = pdf_path
    
    def run(self):
        uploaded_file = None
        try:
            if not self.pdf_path or not os.path.exists(self.pdf_path):
                raise FileNotFoundError("The active PDF file could not be found.")
            self.progress_signal.emit("Uploading PDF to gemini...")
            uploaded_file = self.client.files.upload(file = self.pdf_path)


            prompt = """
            Analyze the attached document and provide a deep, structured summary formatted as a raw JSON object.
            Do not wrap the JSON in markdown code blocks like ```json ... ```. Output ONLY the raw JSON string.
            Try keeping the title under 25 characters, but you can use more if necessary.

            The JSON must match this structure exactly:
            {
                "title": "A concise, meaningful title for these study notes",
                "summary": "Write your detailed summary here. You MUST use clean, standard HTML tags with explicit inline CSS styles for text sizing. To make it comfortably readable on 1080p displays, use these exact large dimensions: Use <h2 style='font-size: 26px; color: #38bdf8; margin-top: 18px; margin-bottom: 8px;'> or <h3 style='font-size: 22px; color: #38bdf8; margin-top: 16px; margin-bottom: 6px;'> for section headlines. Use <p style='font-size: 18px; line-height: 1.6; color: #f8fafc; margin-bottom: 12px;'> for paragraphs. Use <ul style='margin-left: 15px;'> and <li style='font-size: 18px; color: #f8fafc; margin-bottom: 6px;'> for list items. Use <b> or <i> for emphasizing terms. Ensure all HTML quotes inside style attributes use single quotes (') to prevent breaking the outer JSON double-string format."
            }
            """

            response = self.client.models.generate_content(model = "gemini-2.5-flash", contents = [uploaded_file , prompt])
            
            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.IGNORECASE | re.MULTILINE).strip()

            parsed_data = json.loads(raw_text)
            title = parsed_data.get("title" , "Summarised PDF Notes")
            html_summary = parsed_data.get("summary" , "<p>No summary generated.</p>")
            
            self.success_signal.emit(title , html_summary)

        except Exception as e:
            self.error_signal.emit(str(e))
        
        finally:
            if uploaded_file:
                try:
                    self.client.files.delete(name = uploaded_file.name)
                except Exception:
                    pass
    

            
class QuizWorker(QThread):
    progress_signal = pyqtSignal(str)
    success_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, client, topic, pdf_paths, num_questions):
        super().__init__()
        self.client = client
        self.topic = topic
        self.pdf_paths = pdf_paths
        self.num_questions = num_questions

    def run(self):
        try:
            api_contents = []
            uploaded_files_cleanup = []

            if self.pdf_paths:
                for path in self.pdf_paths:
                    if os.path.exists(path):
                        self.progress_signal.emit(f"Uploading {os.path.basename(path)}...")
                        uploaded_file = self.client.files.upload(file=path)
                        api_contents.append(uploaded_file)
                        uploaded_files_cleanup.append(uploaded_file)
                
                prompt = f"Create exactly {self.num_questions} multiple-choice questions based on the attached PDF documents."
            else:
                prompt = f"Create exactly {self.num_questions} multiple-choice questions on the topic: {self.topic}."

            prompt += """
            Format each question exactly like this:

            Q1. Question text
            A) Option 1
            B) Option 2
            C) Option 3
            D) Option 4
            Answer: B

            Only use this format. Separate questions with a blank line. Do not output anything else.
            """
            api_contents.append(prompt)

            self.progress_signal.emit("Gemini is generating your quiz...")
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=api_contents)
            
            self.success_signal.emit(response.text)

            for token in uploaded_files_cleanup:
                try:
                    self.client.files.delete(name=token.name)
                except:
                    pass

        except Exception as e:
            self.error_signal.emit(str(e))


class AiChatWorker(QThread):
    progress_signal = pyqtSignal(str)
    success_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, client, prompt, chat_history=None):
        super().__init__()
        self.client = client
        self.prompt = prompt
        self.chat_history = chat_history if chat_history else []

    def run(self):
        try:
            self.progress_signal.emit("Gemini is thinking...")
            

            system_instruction = (
                "You are an expert academic tutor built into StudyMind. "
                "Always format your responses using clean Markdown. "
                "For math equations, formulas, or scientific notation, you MUST use standard LaTeX delimiters: "
                "Use inline single dollar signs like $e=mc^2$ for text formulas, and double dollar signs "
                "like $$\\frac{a}{b}$$ for isolated math blocks. Always maintain clear, helpful structural layout."
                "If the user asks for anythign non related to acadmics then you can simply say no and tell them not to divert from topic"
                "you will not answer for any non acadmic questions, thinks like sports and stuff, when it's not related to study."
            )

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=self.prompt,
                config={"system_instruction": system_instruction}
            )
            
            self.success_signal.emit(response.text)
        except Exception as e:
            self.error_signal.emit(str(e))



class FlashcardWorker(QThread):
    progress_signal = pyqtSignal(str)
    success_signal = pyqtSignal(str, list)
    error_signal = pyqtSignal(str)

    def __init__(self, client, pdf_path):
        super().__init__()
        self.client = client
        self.pdf_path = pdf_path

    def run(self):
        uploaded_file = None
        try:
            if not self.pdf_path or not os.path.exists(self.pdf_path):
                raise FileNotFoundError("The active PDF file could not be found.")

            file_size = os.path.getsize(self.pdf_path)
            self.progress_signal.emit("Uploading PDF to Gemini...")
            uploaded_file = self.client.files.upload(file=self.pdf_path)

            prompt = f"""
            You are creating a flashcard deck from a study PDF.
            Return ONLY valid JSON with this structure:
            {{
            "category": "Short descriptive title for the deck",
            "flashcards": [
                {{"question": "...", "answer": "...", "rating": "Easy|Medium|Hard"}}
            ]
            }}

            Instructions:
            - Create a good number of flashcards based on the PDF length and complexity.
            - Small PDFs: 6-8 cards. Medium PDFs: 8-12 cards. Large PDFs: 12-18 cards.
            - The file size is approximately {file_size} bytes.
            - Cover the most important concepts, definitions, formulas, processes, and key facts.
            - Questions should be concise and answerable from the document.
            - Answers should be accurate and self-contained.
            - Use only the three difficulty values: Easy, Medium, Hard.
            - Do not add any commentary outside the JSON.
            """

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[uploaded_file, prompt]
            )

            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.IGNORECASE | re.MULTILINE).strip()

            parsed_data = json.loads(raw_text)
            category_name = str(parsed_data.get("category") or parsed_data.get("Category") or "PDF Deck").strip() or "PDF Deck"
            flashcards = parsed_data.get("flashcards") or []

            if not isinstance(flashcards, list):
                raise ValueError("Gemini returned an invalid flashcard list.")

            normalized_cards = []
            for card in flashcards:
                if not isinstance(card, dict):
                    continue
                question = str(card.get("question", "")).strip()
                answer = str(card.get("answer", "")).strip()
                rating = str(card.get("rating") or "Medium").strip()
                if not question or not answer:
                    continue
                if rating not in {"Easy", "Medium", "Hard"}:
                    rating = "Medium"
                normalized_cards.append({
                    "question": question,
                    "answer": answer,
                    "rating": rating
                })

            if not normalized_cards:
                raise ValueError("Gemini did not return any valid flashcards.")

            self.success_signal.emit(category_name, normalized_cards)

        except Exception as e:
            self.error_signal.emit(str(e))

        finally:
            if uploaded_file:
                try:
                    self.client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass



class QuizApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.question_data =[]
        self.selected_pdf_paths =[]
        self.can_close =True 

        self.initUI()

    def initUI(self):
        self.setWindowTitle("AI Quiz Generator(Multi-PDF Support)")
        self.setGeometry(300 ,300 ,800 ,800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.top_bar = QHBoxLayout()

        self.topic_input = QLineEdit(self)
        self.topic_input.setAlignment(Qt.AlignCenter)
        self.topic_input.setPlaceholderText("Enter quiz topic OR upload multiple PDFs...")

        self.pdf_btn = QPushButton("📁 Choose PDFs",self)
        self.pdf_btn.setStyleSheet("background-color: #e67e22;")
        self.pdf_btn.clicked.connect(self.select_pdfs)

        self.num_spinbox = QSpinBox(self)
        self.num_spinbox.setRange(1 ,30)
        self.num_spinbox.setValue(5)
        self.num_spinbox.setPrefix("Questions: ")

        self.generate_btn = QPushButton("Generate Quiz",self)
        self.generate_btn.clicked.connect(self.generate_quiz)

        self.top_bar.addWidget(self.topic_input)
        self.top_bar.addWidget(self.pdf_btn)
        self.top_bar.addWidget(self.num_spinbox)
        self.top_bar.addWidget(self.generate_btn)

        self.main_layout.addLayout(self.top_bar)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)

        self.submit_btn = QPushButton("Submit Answers",self)
        self.submit_btn.setEnabled(False)
        self.submit_btn.clicked.connect(self.submit_quiz)
        self.main_layout.addWidget(self.submit_btn)

    def select_pdfs(self):
        file_paths ,_ = QFileDialog.getOpenFileNames(self ,"Select Reference PDFs","","PDF Files(*.pdf)")

        if file_paths :
            self.selected_pdf_paths =file_paths 
            num_files =len(file_paths)

            if num_files ==1 :
                self.topic_input.setText(f"Using 1 PDF: {os.path.basename(file_paths [0 ])}")
            else :
                self.topic_input.setText(f"Using {num_files } PDFs for the quiz source material.")

            self.topic_input.setEnabled(False)
            self.pdf_btn.setText("❌ Clear PDFs")
            self.pdf_btn.clicked.disconnect()
            self.pdf_btn.clicked.connect(self.clear_pdfs)

    def clear_pdfs(self):
        self.selected_pdf_paths =[]
        self.topic_input.clear()
        self.topic_input.setEnabled(True)
        self.topic_input.setPlaceholderText("Enter quiz topic OR upload multiple PDFs...")
        self.pdf_btn.setText("📁 Choose PDFs")
        self.pdf_btn.clicked.disconnect()
        self.pdf_btn.clicked.connect(self.select_pdfs)

    def load_pdf_for_quiz(self ,pdf_path ,num_questions =None):
        if not pdf_path or not os.path.exists(pdf_path):
            QMessageBox.warning(self ,"PDF Load Error","The selected PDF path is invalid.")
            return 

        self.selected_pdf_paths =[pdf_path ]
        self.topic_input.setText(f"Using PDF: {os.path.basename(pdf_path)}")
        self.topic_input.setEnabled(False)
        self.pdf_btn.setText("❌ Clear PDFs")
        self.pdf_btn.clicked.disconnect()
        self.pdf_btn.clicked.connect(self.clear_pdfs)

        if num_questions is not None :
            self.num_spinbox.setValue(num_questions)

        self.generate_quiz()

    def generate_quiz(self):
        pdf_config = AppConfig.load_namespace("pdf_reader")
        active_key = pdf_config.get("api_key", API_KEY)
        if not active_key:
            QMessageBox.warning(self, "API Key Missing", "Please add your Gemini API key in Settings first.")
            return
        self.client = genai.Client(api_key=active_key)
        topic = self.topic_input.text().strip()
        num_questions = self.num_spinbox.value()

        if not topic and not self.selected_pdf_paths:
            QMessageBox.warning(self, "Error", "Please enter a topic or upload some PDFs first!")
            return

        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("Initializing...")
        self.can_close = False

        self.quiz_thread = QuizWorker(
            client=self.client, 
            topic=topic, 
            pdf_paths=self.selected_pdf_paths, 
            num_questions=num_questions)

        self.quiz_thread.progress_signal.connect(self.on_quiz_progress)
        self.quiz_thread.success_signal.connect(self.on_quiz_success)
        self.quiz_thread.error_signal.connect(self.on_quiz_error)
        self.quiz_thread.start()

    def on_quiz_progress(self, status_text):
        self.generate_btn.setText("Generating quiz")


    def on_quiz_success(self, quiz_text):
        self.populate_quiz(quiz_text) 
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("Generate Quiz")
        self.submit_btn.setEnabled(True)
        self.can_close = True

    def on_quiz_error(self, error_message):
        QMessageBox.critical(self, "Generation Error", f"Something went wrong:\n{error_message}")
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("Generate Quiz")
        self.can_close = True

    def populate_quiz(self ,quiz_text):
        for i in reversed(range(self.scroll_layout.count())):
            widget =self.scroll_layout.itemAt(i).widget()
            if widget is not None :
                widget.deleteLater()
        self.question_data.clear()

        questions = quiz_text.strip().split("\n\n")

        for item in questions :
            lines =item.strip().split("\n")
            if len(lines)<6 :
                continue 

            q_text =lines [0 ]
            options =lines [1 :5 ]
            correct_line =lines [-1 ]

            match =re.search(r"Answer:\s*([ABCD])",correct_line)
            if not match :
                continue 

            correct_ans =match.group(1).upper()

            q_box = QGroupBox(q_text)
            q_box_layout = QVBoxLayout()

            btn_group = QButtonGroup(self)

            for opt in options :
                rb = QRadioButton(opt)
                btn_group.addButton(rb)
                q_box_layout.addWidget(rb)

            q_box.setLayout(q_box_layout)
            self.scroll_layout.addWidget(q_box)

            self.question_data.append({
            "group":btn_group ,
            "correct":correct_ans ,
            "box":q_box 
            })

    def submit_quiz(self):
        score =0 
        total =len(self.question_data)
        unanswered =0 

        for q in self.question_data :
            selected_btn =q ["group"].checkedButton()

            if selected_btn is None :
                unanswered +=1 
                continue 

            selected_letter =selected_btn.text().strip()[0 ].upper()
            if selected_letter == q ["correct"]:
                score +=1 

        percentage =(score /total)*100 if total >0 else 0 

        result_msg =f"Your Score: {score } / {total }\nPercentage: {percentage :.1f}%\n"
        if unanswered >0 :
            result_msg +=f"\nYou left {unanswered } question(s) blank."

        QMessageBox.information(self ,"Quiz Results",result_msg)
        self.can_close =True 

    def closeEvent(self ,event):
        if self.can_close :
            event.accept()
        else :
            event.ignore()


DARK_STYLE ="""
    QMainWindow { 
        background-color: #1e1e1e; 
    }
    
    QLabel { 
        color: #d4d4d4; 
        font-size: 16px; 
    }
    
    QTextEdit {
        background-color: #1e1e1e;
        border: 1px solid #3c3c3c;
        color: #d4d4d4;
        border-radius: 6px;
        font-family: 'Consolas', 'Fira Code', 'Courier New', monospace;
        font-size: 14px;
        padding: 12px;
    }
    QTextEdit:focus {
        border: 1px solid #007acc;
    }
    
    QLineEdit {
        background-color: #252526;
        border: 1px solid #3c3c3c;
        color: #cccccc;
        border-radius: 4px;
        padding: 6px;
        font-family: 'Segoe UI', sans-serif;
    }
    QLineEdit:focus {
        border: 1px solid #007acc;
    }

    QPushButton { 
        background-color: #0e639c; 
        color: #ffffff; 
        border: none;
        border-radius: 4px; 
        padding: 8px 14px; 
        font-family: 'Segoe UI', sans-serif;
        font-weight: 500;
    }
    QPushButton:hover { 
        background-color: #1177bb; 
    }
    QPushButton:pressed {
        background-color: #0c5282;
    }
    QPushButton:disabled {
        background-color: #2d2d2d;
        color: #777777;
    }

    QListWidget {
        background-color: #252526;
        color: #cccccc;
        border: 1px solid #3c3c3c;
        border-radius: 6px;
        padding: 6px;
    }
    
    QListWidget::item {
        background-color: transparent; 
        color: #cccccc;
        border-radius: 4px; 
        margin-bottom: 4px;      
        padding: 8px;
        font-family: 'Segoe UI', sans-serif;
    }
    QListWidget::item:hover {
        background-color: #2a2d2e;
        color: #ffffff;
    }
    QListWidget::item:selected {
        background-color: #37373d;
        color: #ffffff;
        border-left: 3px solid #007acc; 
    }

    QSpinBox {
        background-color: #252526;
        color: #cccccc;
        border: 1px solid #3c3c3c;
        border-radius: 4px;
        padding: 4px;
    }

    QPushButton#formatting_btn, QPushButton#theme_btn {
        background-color: #333333;
        color: #cccccc;
        border: 1px solid #444444;
    }
    QPushButton#formatting_btn:hover, QPushButton#theme_btn:hover {
        background-color: #444444;
        color: #ffffff;
        border: 1px solid #007acc;
    }
"""

LIGHT_STYLE ="""
    QMainWindow { background-color: #01b0aa; }  
    QLabel { color: #000000; font-size: 18px; }
    QPushButton { 
        background-color: #008CBA; 
        color: white;  
        border-radius: 16px;
        padding: 10px;
    }
    QPushButton:hover { background-color: #007ba7; }
    QTextEdit { background-color : #addee4;
                border: 2px solid teal;
                color: #d53939 ;
                border-bottom-left-radius:50px;
                border-top-right-radius:50px;}

    QListWidget {
        background-color: #083339 ;
        color : #3b05de ;
        border: 1px solid red;
        border-top-right-radius:20px;
        border-top-left-radius:20px;
        padding: 10px}

    QListWidget::item {
        background-color: #3BC1A8; 
        color: #005461;
        border: 2px solid #4CAF50;
        border-radius: 15px; 
        margin-bottom: 10px;      
        padding: 10px;
        font-family: 'Segoe UI', sans-serif;
        font-weight: bold;
        
    }

    QListWidget::item:selected {
        background-color: #0C7779;
        color: #ffffff;
        border: 2px solid #4CAF50;
    }

    QListWidget::item:hover {
        background-color: #42c8cd;
    }

    QPushButton#theme_btn {
        border-radius: 18px;
        background-color: grey;
        color:yellow;
        font-weight:bold;
    }

    QPushButton#formatting_btn {
        background-color: pink;
    }
"""


class howerbutton(QPushButton):
    def __init__(self ,text ,hower_text ,parent =None):
        super().__init__(text ,parent)
        self.original_text =text 
        self.hower_text =hower_text 

    def enterEvent(self ,event):
        self.setText(self.hower_text)
        super().enterEvent(event)

    def leaveEvent(self ,event):
        self.setText(self.original_text)
        super().leaveEvent(event)


class Note_taker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(600 ,600 ,1000 ,1000)
        self.is_dark =True 
        self.auto_save =True 
        self.justify_state =1 
        self.theme_btn = QPushButton("⏾",self)
        self.save_btn = QPushButton("Save",self)
        self.new_btn = QPushButton("New",self)
        self.text_box = QTextEdit(self)
        self.notes_list = QListWidget(self)
        self.notes ={}
        self.current_note =None 
        self.load_notes()
        self.title_box = QLineEdit(self)
        self.delete_btn = QPushButton("Delete",self)
        self.font_size = QSpinBox(self)
        self.search_box = QLineEdit(self)
        self.font_size.setRange(1 ,100)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.save_note)


        self.initUI()
        self.app_layout()
        self.keyboard_shortcuts()
        self.get_font_size()
        self.auto_save_function()


    def initUI(self):
        self.setWindowTitle("Dnotes")
        self.theme_btn.setObjectName("theme_btn")
        self.title_box.setPlaceholderText("TITLE")
        self.text_box.setPlaceholderText("Start writing your note from here ")
        self.search_box.setPlaceholderText("🔍 Search notes...")
        self.title_box.setAlignment(Qt.AlignCenter)
        self.search_box.setAlignment(Qt.AlignCenter)


        self.bold_btn =howerbutton("B","Bold",self)
        self.bold_btn.setObjectName("formatting_btn")
        self.italic_btn =howerbutton("I","Italic",self)
        self.italic_btn.setObjectName("formatting_btn")
        self.underline_btn =howerbutton("U","Underline",self)
        self.underline_btn.setObjectName("formatting_btn")
        self.autosave_btn =howerbutton("A","Auto Save",self)
        self.justify_btn =howerbutton("J","Justify",self)
        self.justify_btn.setObjectName("formatting_btn")
        self.export_txt_btn =howerbutton("Txt","Export as Text",self)
        self.export_txt_btn.setObjectName("formatting_btn")
        self.export_pdf_btn =howerbutton("PDF","Export as PDF",self)
        self.export_pdf_btn.setObjectName("formatting_btn")
        self.open_btn =howerbutton("Open","Open txt file",self)
        self.open_btn.setObjectName("formatting_btn")


        self.theme_btn.clicked.connect(self.toggle_theme)
        self.save_btn.clicked.connect(self.save_note)
        self.new_btn.clicked.connect(self.new_note)
        self.notes_list.itemClicked.connect(self.open_note)
        self.delete_btn.clicked.connect(self.delete_note)
        self.title_box.textChanged.connect(self.valid_title)
        self.bold_btn.clicked.connect(self.bold_text)
        self.italic_btn.clicked.connect(self.italic_text)
        self.underline_btn.clicked.connect(self.underline_text)
        self.font_size.valueChanged.connect(self.change_font_size)
        self.autosave_btn.clicked.connect(self.toggle_autosave)
        self.justify_btn.clicked.connect(self.justify_text)
        self.search_box.textChanged.connect(self.search_notes)
        self.export_txt_btn.clicked.connect(self.save_as_txt)
        self.export_pdf_btn.clicked.connect(self.save_as_pdf)
        self.open_btn.clicked.connect(self.open_external_file)


        self.setStyleSheet(DARK_STYLE)
        self.save_btn.setEnabled(False)
        self.valid_title()



    def app_layout(self):
        container = QWidget()
        hbox = QHBoxLayout()
        vbox1 = QVBoxLayout()
        vbox2 = QVBoxLayout()
        hbox2 = QHBoxLayout()

        hbox2.addWidget(self.bold_btn)
        hbox2.addWidget(self.italic_btn)
        hbox2.addWidget(self.underline_btn)
        hbox2.addWidget(self.justify_btn)
        hbox2.addWidget(self.autosave_btn)
        hbox2.addWidget(self.font_size)

        theme_hbox = QHBoxLayout()

        vbox1.addWidget(self.text_box)
        vbox1.addLayout(hbox2)

        theme_hbox.addWidget(self.export_txt_btn)
        theme_hbox.addWidget(self.export_pdf_btn)
        theme_hbox.addWidget(self.open_btn)
        theme_hbox.addStretch(1)
        theme_hbox.addWidget(self.theme_btn)
        vbox2.addLayout(theme_hbox)
        vbox2.addWidget(self.title_box)
        vbox2.addWidget(self.new_btn)
        vbox2.addWidget(self.save_btn)
        vbox2.addWidget(self.delete_btn)
        vbox2.addWidget(self.search_box)
        vbox2.addWidget(self.notes_list)


        hbox.addLayout(vbox1 ,4)
        hbox.addLayout(vbox2 ,1)

        container.setLayout(hbox)
        self.setCentralWidget(container)


    def keyboard_shortcuts(self):
        self.new_btn.setShortcut("Ctrl+N")
        self.save_btn.setShortcut("Ctrl+S")
        self.delete_btn.setShortcut("Ctrl+del")

        self.increase_font_size = QShortcut(QKeySequence("Ctrl++"),self)
        self.increase_font_size.activated.connect(lambda :self.font_size.setValue(self.font_size.value()+1))

        self.increase_font_size_2 = QShortcut(QKeySequence("Ctrl+="),self)
        self.increase_font_size_2.activated.connect(lambda :self.font_size.setValue(self.font_size.value()+1))

        self.decrease_font_size = QShortcut(QKeySequence("Ctrl+-"),self)
        self.decrease_font_size.activated.connect(lambda :self.font_size.setValue(self.font_size.value()-1))

        self.bold_shortcut = QShortcut(QKeySequence("Ctrl+B"),self)
        self.bold_shortcut.activated.connect(self.bold_text)

        self.italic_shortcut = QShortcut(QKeySequence("Ctrl+I"),self)
        self.italic_shortcut.activated.connect(self.italic_text)

        self.underline_shortcut = QShortcut(QKeySequence("Ctrl+U"),self)
        self.underline_shortcut.activated.connect(self.underline_text)

        self.justify_shortcut = QShortcut(QKeySequence("Ctrl+J"),self)
        self.justify_shortcut.activated.connect(self.justify_text)

        self.theme_shortcut = QShortcut(QKeySequence("Ctrl+T"),self)
        self.theme_shortcut.activated.connect(self.toggle_theme)


    def toggle_theme(self):
        if self.is_dark :
            self.setStyleSheet(LIGHT_STYLE)
            self.is_dark =False 
            self.theme_btn.setText("𖤓")

        else :
            self.setStyleSheet(DARK_STYLE)
            self.is_dark =True 
            self.theme_btn.setText("⏾")

        self.theme_bug_fix()
        self.theme_bug_fix()


    def theme_bug_fix(self):
        self.bold_text()
        self.italic_text()
        self.underline_text()


    def load_notes(self):
        note_config = AppConfig.load_namespace("note_taker")
        self.notes = note_config.get("notes", {})
        
        self.notes_list.clear()
        for title in self.notes.keys():
            self.notes_list.addItem(title)

    def refresh_list(self):
        self.notes_list.clear()
        for title in self.notes :
            item = QListWidgetItem(title)
            item.setTextAlignment(Qt.AlignCenter)
            self.notes_list.addItem(item)

    def save_note(self):
        title = self.title_box.text().strip()
        if not title:
            return

        content = self.text_box.toHtml()
        self.notes[title] = content

        note_config = {"notes": self.notes}
        AppConfig.save_namespace("note_taker", note_config)

        if not self.notes_list.findItems(title, Qt.MatchExactly):
            self.notes_list.addItem(title)
    

    def new_note(self):
        self.text_box.clear()
        self.title_box.clear()
        self.current_note =None 

    def open_note(self ,item):
        title =item.text()
        self.current_note =title 
        self.title_box.setText(title)
        self.text_box.setHtml(self.notes [title ])

    def delete_note(self):
        title =self.title_box.text()
        if title in self.notes :
            del self.notes [title ]
        with open(self.notes_file ,"w")as f :
            json.dump(self.notes ,f ,indent =4)
        self.title_box.clear()
        self.text_box.clear()
        self.current_note =None 
        self.refresh_list()

    def valid_title(self):
        title =self.title_box.text()
        if len(title)>20 :
            self.save_btn.setEnabled(False)
            self.save_btn.setStyleSheet("background-color: red;")
        elif len(title)!=0 :
            self.save_btn.setEnabled(True)
            self.save_btn.setStyleSheet("background-color: #008CBA;")
        else :
            self.save_btn.setEnabled(False)
            self.save_btn.setStyleSheet("background-color: red;")

    def bold_text(self):
        current_weight =self.text_box.fontWeight()

        if current_weight == QFont.Bold :
            self.text_box.setFontWeight(QFont.Normal)
            if self.is_dark :
                self.bold_btn.setStyleSheet("background-color:grey;")
            else :
                self.bold_btn.setStyleSheet("background-color: pink;")
        else :
            self.text_box.setFontWeight(QFont.Bold)
            if self.is_dark :
                self.bold_btn.setStyleSheet("background-color:teal;")
            else :
                self.bold_btn.setStyleSheet("background-color: lime;")

    def italic_text(self):
        is_currently_italic =self.text_box.fontItalic()
        self.text_box.setFontItalic(not is_currently_italic)
        if not is_currently_italic :
            if self.is_dark :
                self.italic_btn.setStyleSheet("background-color:teal;font-style:italic;")
            else :
                self.italic_btn.setStyleSheet("background-color:lime;font-style:italic;")
        else :
            if self.is_dark :
                self.italic_btn.setStyleSheet("background-color:grey;font-style:normal;")
            else :
                self.italic_btn.setStyleSheet("background-color:pink;font-style:normal;")

    def underline_text(self):
        is_underlined =self.text_box.fontUnderline()
        self.text_box.setFontUnderline(not is_underlined)

        if not is_underlined:
            if self.is_dark:
                self.underline_btn.setStyleSheet("background-color:teal;")
            else :
                self.underline_btn.setStyleSheet("background-color:lime;")
        else :
            if self.is_dark:
                self.underline_btn.setStyleSheet("background-color:grey;")
            else :
                    self.underline_btn.setStyleSheet("background-color:pink")


    def justify_text(self):
        if self.justify_state ==1:
            self.text_box.setAlignment(Qt.AlignCenter)
            self.justify_btn.setText("Center")
            self.justify_state =2 

        elif self.justify_state ==2:
            self.text_box.setAlignment(Qt.AlignRight)
            self.justify_btn.setText("Right")
            self.justify_state =3 

        elif self.justify_state ==3:
            self.text_box.setAlignment(Qt.AlignJustify)
            self.justify_btn.setText("Justify")
            self.justify_state =4 

        elif self.justify_state ==4:
            self.text_box.setAlignment(Qt.AlignLeft)
            self.justify_btn.setText("Left")
            self.justify_state =1 

        else :
            pass 



    def get_font_size(self):
        current_size =self.text_box.font().pointSize()
        self.font_size.setValue(int(current_size))

    def change_font_size(self):
        new_size =self.font_size.value()
        self.text_box.setFontPointSize(new_size)


    def toggle_autosave(self):
        if self.auto_save:
            self.auto_save =False 
            if self.is_dark:
                self.autosave_btn.setStyleSheet("background-color:grey;")
            else :
                self.autosave_btn.setStyleSheet("background-color:pink;")
            self.timer.stop()
        else :
            self.auto_save =True 
            self.autosave_btn.setStyleSheet("background-color:#2f8571;")
            self.timer.start(10000)

    def search_notes(self):
        search_text =self.search_box.text().strip().lower()
        for i in range(self.notes_list.count()):
            item =self.notes_list.item(i)
            if not search_text or search_text in item.text().lower():
                item.setHidden(False)
            else :
                item.setHidden(True)


    def auto_save_function(self):
        if self.auto_save:
            self.timer.start(10000)

    def save_as_txt(self):
        note_title =self.title_box.text().strip()
        default_name =f"{note_title }.txt"if note_title else "untitled.txt"
        file_path ,_ = QFileDialog.getSaveFileName(self ,"Export Note as Text",default_name ,"Text Files(*.txt);;All Files(*)")
        if file_path:
            plain_text =self.text_box.toPlainText()
            with open(file_path ,"w",encoding ="utf-8")as file :
                file.write(plain_text)

    def save_as_pdf(self):
        note_title =self.title_box.text().strip()
        default_name =f"{note_title }.pdf"if note_title else "untitled.pdf"

        file_path ,_ = QFileDialog.getSaveFileName(self ,"Export Note as PDF",default_name ,"PDF Files(*.pdf);;All Files(*)")
        if file_path:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            self.text_box.document().print_(printer)

    def open_external_file(self):
        file_path ,_ = QFileDialog.getOpenFileName(self ,"Open Document","","Text Files(*.txt);;HTML Files(*.html)")

        if file_path :
            file_name =os.path.basename(file_path)
            title_without_ext ,ext =os.path.splitext(file_name)

            try :
                with open(file_path ,"r",encoding ="utf-8")as file :
                    file_content =file.read()

                self.title_box.setText(title_without_ext)

                if ext.lower()==".html":
                    self.text_box.setHtml(file_content)
                else :
                    self.text_box.setPlainText(file_content)

                self.valid_title()

            except Exception as e :
                self.title_box.setText("Error")
                self.text_box.setPlainText(f"Could not read file structure: {str(e)}")



class FlashcardDialog(QDialog):
    def __init__(self ,categories ,card =None ,current_category =None):
        super().__init__()
        self.setWindowTitle("Flashcard")
        layout = QFormLayout()

        self.question_edit= QLineEdit()
        self.answer_edit= QLineEdit()

        self.rating_combo= QComboBox()
        self.rating_combo.addItems(["Easy","Medium","Hard"])

        self.category_combo = QComboBox()
        self.category_combo.addItems(categories)

        if current_category :
                    self.category_combo.setCurrentText(current_category)

        if card :
            self.question_edit.setText(card ["question"])
            self.answer_edit.setText(card ["answer"])
            self.rating_combo.setCurrentText(card ["rating"])

        layout.addRow("Question:",self.question_edit)
        layout.addRow("Answer:",self.answer_edit)
        layout.addRow("Difficulty:",self.rating_combo)
        layout.addRow("Category:",self.category_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok |QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)


    def get_data(self):
        return {
        "question":
        self.question_edit.text(),

        "answer":
        self.answer_edit.text(),

        "rating":
        self.rating_combo.currentText(),

        "category":
        self.category_combo.currentText()
        }



class FlashcardApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Flashcard App")
        self.load_data()

    def generate_from_pdf(self, pdf_path, progress_slot=None, success_slot=None, error_slot=None):
        if not pdf_path or not os.path.exists(pdf_path):
            QMessageBox.warning(self, "No PDF Open", "Please open a PDF in the reader first.")
            return False

        self.card_display.setText("Generating flashcards from the selected PDF...")

        pdf_config = AppConfig.load_namespace("pdf_reader")
        user_key = pdf_config.get("api_key", API_KEY)
        if not user_key:
            QMessageBox.warning(self, "API Key Missing", "Please add your Gemini API key in Settings first.")
            return False
        self.flashcard_thread = FlashcardWorker(
        client=genai.Client(api_key=user_key),
        pdf_path=pdf_path)
        
        self.flashcard_thread.progress_signal.connect(progress_slot or self.on_flashcard_progress)
        self.flashcard_thread.success_signal.connect(success_slot or self.on_flashcard_success)
        self.flashcard_thread.error_signal.connect(error_slot or self.on_flashcard_error)
        self.flashcard_thread.start()
        return True

    def on_flashcard_progress(self, status_text):
        if hasattr(self, "card_display"):
            self.card_display.setText(status_text)

    def on_flashcard_success(self, category_name, cards):
        unique_name = self.make_unique_category_name(category_name)
        self.flashcards[unique_name] = cards
        self.refresh_categories()
        self.current_category = unique_name
        self.current_index = 0
        self.load_deck()
        self.save_data()

    def on_flashcard_error(self, error_message):
        if hasattr(self, "card_display"):
            self.card_display.setText("Flashcard generation failed.")

    def make_unique_category_name(self, category_name):
        base_name = str(category_name or "PDF Deck").strip() or "PDF Deck"
        candidate = base_name
        counter = 2
        while candidate in self.flashcards:
            candidate = f"{base_name} {counter}"
            counter += 1
        return candidate

    def save_data(self):
        flash_data = {"decks": self.flashcards}
        AppConfig.save_namespace("flashcards", flash_data)


    def load_data(self):

        flash_data = AppConfig.load_namespace("flashcards")
        self.flashcards = flash_data.get("decks", {})
        if not self.flashcards:
            self.flashcards = {
                "English": [{"question": "What is a noun?", "answer": "A naming word", "rating": "Easy"}],
                "Maths": [{"question": "Area of Circle?", "answer": "πr²", "rating": "Easy"}]
        }
        self.current_category = None
        self.current_index =0 
        self.stack = QStackedWidget()
        self.create_home_page()
        self.create_category_page()
        self.create_deck_page()

        layout = QVBoxLayout()
        layout.addWidget(self.stack)

        self.setLayout(layout)
        self.save_data()





    def create_home_page(self):
        self.home_page = QWidget()
        layout = QVBoxLayout()
        title = QLabel("FLASHCARD APP")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
                    font-size:32px;
                    font-weight:bold;
                """)

        deck_btn = QPushButton("Decks")
        deck_btn.setMinimumHeight(60)
        deck_btn.clicked.connect(
        lambda :
        self.stack.setCurrentWidget(self.category_page))

        layout.addStretch()
        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(deck_btn)
        layout.addStretch()

        self.home_page.setLayout(layout)
        self.stack.addWidget(self.home_page)



    def create_category_page(self):

        self.category_page = QWidget()
        layout = QVBoxLayout()
        title = QLabel("Select Category")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
        """)

        layout.addWidget(title)

        self.category_list = QListWidget()
        self.refresh_categories()
        self.category_list.itemDoubleClicked.connect(self.open_selected_category)

        layout.addWidget(self.category_list)

        add_btn = QPushButton("Add Category")
        rename_btn = QPushButton("Rename Category")
        delete_btn = QPushButton("Delete Category")
        back_btn = QPushButton("Back")

        add_btn.clicked.connect(self.add_category)
        rename_btn.clicked.connect(self.rename_category)
        delete_btn.clicked.connect(self.delete_category)
        back_btn.clicked.connect(
        lambda :
        self.stack.setCurrentWidget(self.home_page))

        layout.addWidget(add_btn)
        layout.addWidget(rename_btn)
        layout.addWidget(delete_btn)
        layout.addWidget(back_btn)

        self.category_page.setLayout(layout)

        self.stack.addWidget(self.category_page)


    def refresh_categories(self):
        if not hasattr(self ,"category_list"):
            return 

        self.category_list.clear()

        for category in self.flashcards.keys():
            self.category_list.addItem(category)



    def add_category(self):
        name ,ok = QInputDialog.getText(self ,"Add Category","Category Name:")
        if ok and name.strip():
            if name in self.flashcards :
                QMessageBox.warning(self ,"Error","Category already exists.")
                return 

            self.flashcards [name ]=[]
            self.refresh_categories()
            self.save_data()


    def rename_category(self):
        item =self.category_list.currentItem()

        if not item :
            return 
        old_name =item.text()
        new_name ,ok = QInputDialog.getText(self ,"Rename Category","New Name:",text =old_name)
        if ok and new_name.strip():
            if new_name in self.flashcards :
                QMessageBox.warning(self ,"Error","Category already exists.")
                return 

            self.flashcards [new_name ]=(self.flashcards.pop(old_name))
            self.refresh_categories()
            self.save_data()



    def delete_category(self):
        item =self.category_list.currentItem()
        if not item :
            return 
        category =item.text()
        reply = QMessageBox.question(self ,"Delete Category",f"Delete '{category }' and all flashcards?",QMessageBox.Yes |QMessageBox.No)
        if reply == QMessageBox.Yes :
            del self.flashcards [category ]
            self.refresh_categories()
            self.save_data()


    def open_selected_category(self):
        item =self.category_list.currentItem()
        if not item :
            return 
        self.current_category =(item.text())
        self.current_index =0 
        self.load_deck()
        self.stack.setCurrentWidget(self.deck_page)


    def create_deck_page(self):
        self.deck_page = QWidget()
        main_layout = QHBoxLayout()



        left_layout = QVBoxLayout()

        deck_title = QLabel("Flashcard Deck")
        deck_title.setAlignment(Qt.AlignCenter)
        deck_title.setStyleSheet("""
            font-size:20px;
            font-weight:bold;
        """)

        self.deck_list = QListWidget()
        self.deck_list.currentRowChanged.connect(self.select_flashcard)

        self.show_btn = QPushButton("Show Answer")
        self.next_btn = QPushButton("Next")
        self.prev_btn = QPushButton("Previous")
        self.add_btn = QPushButton("Add Flashcard")
        self.edit_btn = QPushButton("Edit Flashcard")
        self.delete_btn = QPushButton("Delete Flashcard")
        self.back_btn = QPushButton("Back to Categories")

        self.show_btn.clicked.connect(self.show_answer)
        self.next_btn.clicked.connect(self.next_card)
        self.prev_btn.clicked.connect(self.previous_card)
        self.add_btn.clicked.connect(self.add_flashcard)
        self.edit_btn.clicked.connect(self.edit_flashcard)
        self.delete_btn.clicked.connect(self.delete_flashcard)
        self.back_btn.clicked.connect(
        lambda :
        self.stack.setCurrentWidget(self.category_page))

        left_layout.addWidget(deck_title)
        left_layout.addWidget(self.deck_list)
        left_layout.addWidget(self.show_btn)
        left_layout.addWidget(self.next_btn)
        left_layout.addWidget(self.prev_btn)
        left_layout.addWidget(self.add_btn)
        left_layout.addWidget(self.edit_btn)
        left_layout.addWidget(self.delete_btn)
        left_layout.addWidget(self.back_btn)



        right_layout = QVBoxLayout()
        self.category_label = QLabel("Category")
        self.category_label.setAlignment(Qt.AlignCenter)
        self.category_label.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
        """)

        self.card_display = QLabel("Select a flashcard")
        self.card_display.setObjectName("flashcard_main")
        self.card_display.setAlignment(Qt.AlignCenter)
        self.card_display.setWordWrap(True)


        right_layout.addWidget(self.category_label)

        right_layout.addWidget(self.card_display)
        main_layout.addLayout(left_layout ,1)
        main_layout.addLayout(right_layout ,3)
        self.deck_page.setLayout(main_layout)
        self.stack.addWidget(self.deck_page)




    def load_deck(self):
        self.deck_list.clear()
        cards =self.flashcards.get(self.current_category ,[])
        self.category_label.setText(f"{self.current_category } Deck")

        for card in cards :
            self.deck_list.addItem(card ["question"])

        if cards :
            self.deck_list.setCurrentRow(0)
            self.current_index =0 
            self.display_question()
        else :
            self.card_display.setText("No Flashcards Available")



    def select_flashcard(self ,row):
        cards =self.flashcards.get(self.current_category ,[])

        if row <0 or not cards :
            return 

        self.current_index =row 
        self.display_question()



    def display_question(self):
        cards =self.flashcards.get(self.current_category ,[])

        if not cards :
            return 

        card =cards [self.current_index ]
        self.card_display.setText(f"""Question: {card ['question']}
                                Difficulty: {card ['rating']}""")



    def show_answer(self):
        cards =self.flashcards.get(self.current_category ,[])

        if not cards :
            return 

        card =cards [self.current_index ]
        self.card_display.setText(f"""Answer: {card ['answer']}
                                Difficulty: {card ['rating']}""")




    def next_card(self):
        cards =self.flashcards.get(self.current_category ,[])

        if not cards :
            return 

        self.current_index =(self.current_index +1)%len(cards)
        self.deck_list.setCurrentRow(self.current_index)



    def previous_card(self):
        cards =self.flashcards.get(self.current_category ,[])

        if not cards :
            return 

        self.current_index =(self.current_index -1)%len(cards)
        self.deck_list.setCurrentRow(self.current_index)


    def add_flashcard(self):
        dialog =FlashcardDialog(list(self.flashcards.keys()),current_category =self.current_category)

        if dialog.exec_():
            data =dialog.get_data()
            if not data ["question"].strip():
                return 
            if not data ["answer"].strip():
                return 
            self.flashcards [data ["category"]].append(
            {
            "question":
            data ["question"],

            "answer":
            data ["answer"],

            "rating":
            data ["rating"]
            })

            if data ["category"]==self.current_category :
                self.load_deck()
                self.save_data()


    def edit_flashcard(self):
        cards =self.flashcards.get(self.current_category ,[])

        if not cards :
            return 

        card =cards [self.current_index ]
        dialog =FlashcardDialog(list(self.flashcards.keys()),card ,self.current_category)
        if dialog.exec_():
            data =dialog.get_data()
            old_card =cards.pop(self.current_index)
            new_card ={
            "question":
            data ["question"],

            "answer":
            data ["answer"],

            "rating":
            data ["rating"]
            }

            destination =data ["category"]
            self.flashcards [destination ].append(new_card)
            self.current_index =0 
            self.load_deck()
            self.save_data()


    def delete_flashcard(self):
        cards =self.flashcards.get(self.current_category ,[])

        if not cards :
            return 
        reply = QMessageBox.question(self ,"Delete Flashcard","Delete this flashcard?",QMessageBox.Yes |QMessageBox.No)
        if reply == QMessageBox.Yes :
            cards.pop(self.current_index)
            if cards :
                self.current_index =min(self.current_index ,len(cards)-1)
            else :
                self.current_index = 0 
            self.load_deck()
            self.save_data()


class Ask_Ai(QWidget):
    def __init__(self):
        super().__init__()
        self.client = None
        self.zoom_factor = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 3.0
        self.screen_scale = self.compute_scale_from_screen()
        self.base_font_size = int(16 * self.screen_scale)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 60, 15, 15)
        layout.setSpacing(10)

        self.chat_display = QWebEngineView()
        self.chat_display.setStyleSheet("background-color: #0f172a; border-radius: 8px;")
        self.setup_web_canvas()
        layout.addWidget(self.chat_display, 5)

        input_layout = QHBoxLayout()
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Ask Gemini anything about your studies... (Press Ctrl+Enter to send)")
        self.prompt_input.setMaximumHeight(80)
        self.apply_prompt_style()
        
        self.send_btn = QPushButton("Send ✨")
        self.send_btn.setFixedSize(100, 80)
        
        input_layout.addWidget(self.prompt_input)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout, 1)

        self.send_btn.clicked.connect(self.send_prompt_to_ai)

        self.submit_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.prompt_input)
        self.submit_shortcut.activated.connect(self.send_prompt_to_ai)

        self.zoom_in_sc = QShortcut(QKeySequence("Ctrl++"), self)
        self.zoom_in_sc.activated.connect(self.zoom_in)
        self.zoom_out_sc = QShortcut(QKeySequence("Ctrl+-"), self)
        self.zoom_out_sc.activated.connect(self.zoom_out)
        self.zoom_reset_sc = QShortcut(QKeySequence("Ctrl+0"), self)
        self.zoom_reset_sc.activated.connect(self.zoom_reset)

        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #38bdf8;
                color: #020617;
                font-weight: bold;
                font-size: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #7dd3fc;
            }
            QPushButton:disabled {
                background-color: #1e293b;
                color: #64748b;
            }
        """)


    def setup_web_canvas(self):
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            
            <script>
                if (!Array.prototype.at) {
                    Array.prototype.at = function(n) {
                        n = Math.trunc(n) || 0;
                        if (n < 0) n += this.length;
                        if (n < 0 || n >= this.length) return undefined;
                        return this[n];
                    };
                }
                if (!String.prototype.at) {
                    String.prototype.at = function(n) {
                        n = Math.trunc(n) || 0;
                        if (n < 0) n += this.length;
                        if (n < 0 || n >= this.length) return "";
                        return this.charAt(n);
                    };
                }
            </script>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
            <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/marked@4.3.0/marked.min.js"></script>

            <style>
                body {
                    background-color: #0f172a;
                    color: #f8fafc;
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    padding: 20px;
                    margin: 0;
                    font-size: {BASE_FONT_SIZE}px;
                    line-height: 1.6;
                }
                .chat-msg {
                    margin-bottom: 24px;
                    padding: 15px;
                    border-radius: 8px;
                    max-width: 85%;
                }
                .user-msg {
                    background-color: #1e293b;
                    margin-left: auto;
                    border-left: 4px solid #64748b;
                }
                .ai-msg {
                    background-color: #020617;
                    margin-right: auto;
                    border-left: 4px solid #38bdf8;
                    border: 1px solid #1e293b;
                }
                .status-msg {
                    color: #38bdf8;
                    font-style: italic;
                    animation: pulse 1.5s infinite;
                }
                pre {
                    background-color: #1e293b;
                    padding: 12px;
                    border-radius: 6px;
                    overflow-x: auto;
                    border: 1px solid #334155;
                }
                code {
                    font-family: 'Consolas', monospace;
                    color: #f43f5e;
                    background-color: #1e293b;
                    padding: 2px 4px;
                    border-radius: 4px;
                }
                pre code {
                    color: #f8fafc;
                    background-color: transparent;
                    padding: 0;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                    margin: 15px 0;
                }
                th, td {
                    border: 1px solid #334155;
                    padding: 8px 12px;
                    text-align: left;
                }
                th {
                    background-color: #1e293b;
                }
                @keyframes pulse {
                    0% { opacity: 0.6; }
                    50% { opacity: 1; }
                    100% { opacity: 0.6; }
                }
            </style>
        </head>
        <body>
            <div id="chat-container"></div>

            <script>
                function appendMessage(role, textContent) {
                    const container = document.getElementById('chat-container');
                    const statusObj = document.getElementById('ai-loading-status');
                    if (statusObj) statusObj.remove();

                    const msgDiv = document.createElement('div');
                    msgDiv.className = 'chat-msg ' + (role === 'user' ? 'user-msg' : 'ai-msg');
                    
                    if (role === 'status') {
                        msgDiv.className = 'chat-msg ai-msg status-msg';
                        msgDiv.id = 'ai-loading-status';
                        msgDiv.innerText = textContent;
                    } else if (role === 'user') {
                        msgDiv.innerText = textContent;
                    } else {
                        // Render full Markdown text safely
                        msgDiv.innerHTML = marked.parse(textContent);
                    }

                    container.appendChild(msgDiv);
                    
                    if (role === 'ai') {
                        renderMathInElement(msgDiv, {
                            delimiters: [
                                {left: '$$', right: '$$', display: true},
                                {left: '$', right: '$', display: false},
                                {left: '\\(', right: '\\)', display: false},
                                {left: '\\[', right: '\\]', display: true}
                            ],
                            throwOnError: false
                        });
                    }

                    window.scrollTo(0, document.body.scrollHeight);
                }
            </script>
        </body>
        </html>
        """

        
        html_template = html_template.replace('{BASE_FONT_SIZE}', str(int(self.base_font_size)))
        self.chat_display.setHtml(html_template)
        self.chat_display.setZoomFactor(self.zoom_factor)
        self.overlay_button_size = (36, 24)
        self.zoom_in_btn = QPushButton('+', self.chat_display)
        self.zoom_out_btn = QPushButton('-', self.chat_display)
        for btn in (self.zoom_in_btn, self.zoom_out_btn):
            btn.setFixedSize(self.overlay_button_size[0], self.overlay_button_size[1])
            btn.setStyleSheet('background-color: rgba(60,60,60,0.9); color: white; border-radius:4px;')
            btn.raise_()
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.position_overlay_buttons()

    def position_overlay_buttons(self):
        try:
            rect = self.chat_display.geometry()
            margin = 100
            bw, bh = self.overlay_button_size
            base_x = rect.x() + rect.width() - margin - bw + 50
            base_y = rect.y() + rect.height() - margin - bh
            self.zoom_in_btn.move(base_x, base_y - (bh + 6))
            self.zoom_out_btn.move(base_x, base_y)
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_overlay_buttons()

    def compute_scale_from_screen(self):
        try:
            screen = QApplication.primaryScreen()
            if screen:
                width = screen.size().width()
            else:
                width = 1366
        except Exception:
            width = 1366
        baseline = 1366
        scale = width / baseline
        return max(0.7, min(1.8, scale))

    def apply_prompt_style(self):
        fs = int(self.base_font_size * self.zoom_factor)
        style = f"""
            QTextEdit {{
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #f8fafc;
                border-radius: 8px;
                font-size: {fs}px;
                padding: 10px;
            }}
            QTextEdit:focus {{ border: 1px solid #38bdf8; }}
        """
        self.prompt_input.setStyleSheet(style)
        if hasattr(self, 'send_btn'):
            self.send_btn.setFixedSize(int(100 * self.screen_scale * self.zoom_factor), int(80 * self.screen_scale * self.zoom_factor))

    def update_web_font(self):
        try:
            new_fs = int(self.base_font_size * self.zoom_factor)
            js = f"document.body.style.fontSize = '{new_fs}px';"
            self.chat_display.page().runJavaScript(js)
            self.chat_display.setZoomFactor(self.zoom_factor * self.screen_scale)
        except Exception:
            pass

    def zoom_in(self):
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor = min(self.max_zoom, self.zoom_factor + 0.1)
            self.apply_prompt_style()
            self.update_web_font()

    def zoom_out(self):
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor = max(self.min_zoom, self.zoom_factor - 0.1)
            self.apply_prompt_style()
            self.update_web_font()

    def zoom_reset(self):
        self.zoom_factor = 1.0
        self.apply_prompt_style()
        self.update_web_font()

    def send_prompt_to_ai(self):
        user_text = self.prompt_input.toPlainText().strip()
        if not user_text:
            return
        
        pdf_config = AppConfig.load_namespace("pdf_reader")
        active_key = pdf_config.get("api_key" , API_KEY)

        if not active_key:
            QMessageBox.warning(self, "API Key Missing", "Please add your Gemini API key in Settings first.")
            return

        self.client = genai.Client(api_key=active_key)

        escaped_user_text = user_text.replace("'", "\\'")
        self.chat_display.page().runJavaScript(f"appendMessage('user', `{escaped_user_text}`);")
        self.prompt_input.clear()

        self.send_btn.setEnabled(False)
        self.prompt_input.setEnabled(False)
        self.chat_display.page().runJavaScript("appendMessage('status', 'Gemini is typing...');")

        self.chat_thread = AiChatWorker(self.client, user_text)
        self.chat_thread.success_signal.connect(self.on_ai_success)
        self.chat_thread.error_signal.connect(self.on_ai_error)
        self.chat_thread.start()

    def on_ai_success(self, raw_markdown_response):
        self.send_btn.setEnabled(True)
        self.prompt_input.setEnabled(True)
        self.prompt_input.setFocus()
        
        escaped_response = raw_markdown_response.replace("`", "\\`").replace("$", "\\$")
        js_execution_string = f"appendMessage('ai', `{escaped_response}`);"
        self.chat_display.page().runJavaScript(js_execution_string)

    def on_ai_error(self, error_message):
        self.send_btn.setEnabled(True)
        self.prompt_input.setEnabled(True)
        self.chat_display.page().runJavaScript(f"appendMessage('ai', '⚠️ Error generating answer: {error_message}');")


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        title = QLabel("Settings & Support")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)
        api_box = QFrame()
        api_box.setStyleSheet("background-color: #1e293b; border-radius: 8px; padding: 15px;")
        api_layout = QVBoxLayout(api_box)
        api_title = QLabel("Gemini API Configuration")
        api_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        api_layout.addWidget(api_title)
        api_instructions = QLabel("To use integrated AI features like PDF Summaries, Chat Bot, or Flashcard Generation, a Gemini API key is required.")
        api_instructions.setWordWrap(True)
        api_instructions.setFont(QFont("Segoe UI", 10))
        api_instructions.setStyleSheet("color: #94a3b8; margin-top: 2px; margin-bottom: 5px;")
        api_layout.addWidget(api_instructions)
        api_link = QLabel('Get a free API key instantly from: <a href="https://aistudio.google.com/" style="color: #3b82f6; text-decoration: underline; font-weight: bold;">Google AI Studio</a>')
        api_link.setOpenExternalLinks(True)  
        api_link.setFont(QFont("Segoe UI", 10))
        api_link.setStyleSheet("margin-bottom: 10px;")
        api_layout.addWidget(api_link)
        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.Password)
        self.api_input.setPlaceholderText("Paste your Gemini API Key here...")
        
        pdf_config = AppConfig.load_namespace("pdf_reader")
        self.api_input.setText(pdf_config.get("api_key", ""))
        
        self.api_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #475569;
                padding: 10px;
                border-radius: 6px;
            }
        """)
        api_layout.addWidget(self.api_input)

        save_btn = QPushButton("Save API Key")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        save_btn.clicked.connect(self.save_api_key)
        api_layout.addWidget(save_btn)
        layout.addWidget(api_box)
        donate_box = QFrame()
        donate_box.setStyleSheet("background-color: #1e293b; border-radius: 8px; padding: 15px;")
        donate_layout = QVBoxLayout(donate_box)

        donate_title = QLabel("Support StudyMind Development")
        donate_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        donate_layout.addWidget(donate_title)

        donate_desc = QLabel("If StudyMind helped you with your studies, consider supporting! Scan via PhonePe, GPay, or Paytm:")
        donate_desc.setWordWrap(True)
        donate_layout.addWidget(donate_desc)

        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        QR_BASE64_STRING = "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" 
        
        try:
            qr_bytes = base64.b64decode(QR_BASE64_STRING)
            pixmap = QPixmap()
            pixmap.loadFromData(qr_bytes)
            self.qr_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            self.qr_label.setText("Could not load QR Code image.")
            
        donate_layout.addWidget(self.qr_label)
        layout.addWidget(donate_box)
        
        layout.addStretch()

    def save_api_key(self):
        new_key = self.api_input.text().strip()
        pdf_config = AppConfig.load_namespace("pdf_reader")
        pdf_config["api_key"] = new_key
        
        try:
            AppConfig.save_namespace("pdf_reader", pdf_config)
            QMessageBox.information(self, "Success", "API Key saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")


if __name__ =="__main__":
    app = QApplication(sys.argv)
    window =StudyMind()
    window.showMaximized()
    sys.exit(app.exec_())