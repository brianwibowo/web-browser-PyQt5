import sys
from PyQt5.QtCore import QUrl, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStatusBar, QToolBar, QAction, QLineEdit, QTabWidget, QVBoxLayout, QWidget,
    QFileDialog, QMenu, QComboBox, QDialog, QListWidget, QListWidgetItem, QPushButton, QMessageBox,  QShortcut, QLabel, QCheckBox
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import pyqtSignal
from urllib.parse import urlparse

class DownloadManager(QWebEnginePage):
    def acceptNavigationRequest(self, qurl, _type, isMainFrame):
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            self.browser.download_requested.emit(qurl)
            return False
        return super().acceptNavigationRequest(qurl, _type, isMainFrame)

class Browser(QWebEngineView):
    download_requested = pyqtSignal(QUrl)

    def __init__(self, is_incognito=False, *args, **kwargs):
        super(Browser, self).__init__(*args, **kwargs)

        if is_incognito:
            # Untuk mode incognito, gunakan profil incognito yang baru
            profile = QWebEngineProfile(self)
        else:
            profile = QWebEngineProfile.defaultProfile()

        self.setPage(QWebEnginePage(profile, self))

        # Menghubungkan signal downloadRequested dengan metode on_download_requested dalam kelas Browser untuk menanggapi permintaan unduhan.
        download_manager = profile.downloadRequested.connect(self.on_download_requested)

    def on_download_requested(self, download):
        self.download_requested.emit(download.url())
        download.accept()

    def navigate_to_url(self, url):
        qurl = QUrl(url)
        if qurl.scheme() == "":
            qurl.setScheme("https://")
        self.setUrl(qurl)

class ShortcutManager:
    def __init__(self, window):
        self.window = window
        self.create_shortcuts()

    def create_shortcuts(self):
        shortcut_new_tab = QShortcut(QKeySequence("Ctrl+T"), self.window)
        shortcut_new_tab.activated.connect(self.window.create_new_tab)

        shortcut_forward = QShortcut(QKeySequence("Ctrl+F"), self.window)
        shortcut_forward.activated.connect(self.window.navigate_forward)

        shortcut_backward = QShortcut(QKeySequence("Ctrl+B"), self.window)
        shortcut_backward.activated.connect(self.window.navigate_back)

        shortcut_home = QShortcut(QKeySequence("Ctrl+H"), self.window)
        shortcut_home.activated.connect(self.window.go_to_home)

        shortcut_refresh = QShortcut(QKeySequence("Ctrl+R"), self.window)
        shortcut_refresh.activated.connect(self.window.reload_page)

        shortcut_go = QShortcut(QKeySequence("Ctrl+G"), self.window)
        shortcut_go.activated.connect(self.window.search_button_clicked)

    def navigate_home(self):
        self.current_browser.setUrl(QUrl('https://www.google.com/'))

class HistoryManager(QDialog):
    item_selected = pyqtSignal(QUrl)

    def __init__(self, history_list, clear_history_callback, parent=None):
        super(HistoryManager, self).__init__(parent)
        self.setWindowTitle('History')
        self.setGeometry(100, 100, 400, 300)

        self.history_list = history_list

        self.list_widget = QListWidget(self)
        self.list_widget.doubleClicked.connect(self.item_double_clicked)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)

        # Tambahkan QPushButton untuk clear history
        clear_button = QPushButton("Clear History", self)
        clear_button.clicked.connect(clear_history_callback)
        layout.addWidget(clear_button)

        self.populate_history_list()

    def populate_history_list(self):
        for url in self.history_list:
            item = QListWidgetItem(url)
            self.list_widget.addItem(item)

    def item_double_clicked(self, item):
        selected_url = item.text()
        self.item_selected.emit(QUrl(selected_url))
        self.accept()

    def clear_history_clicked(self):
        # Clear the history list and update the list widget
        self.history_list.clear()
        self.list_widget.clear()

class Window(QMainWindow):
    accept_navigation = pyqtSignal(QUrl)

    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.setCentralWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.navigation_bar = QToolBar('Navigation Toolbar')
        self.addToolBar(self.navigation_bar)

        back_button = QAction("<", self)
        back_button.setStatusTip('Go to the previous page you visited')
        back_button.triggered.connect(self.navigate_back)
        self.navigation_bar.addAction(back_button)

        refresh_button = QAction("↻", self)
        refresh_button.setStatusTip('Refresh this page')
        refresh_button.triggered.connect(self.reload_page)
        self.navigation_bar.addAction(refresh_button)

        next_button = QAction(">", self)
        next_button.setStatusTip('Go to the next page')
        next_button.triggered.connect(self.navigate_forward)
        self.navigation_bar.addAction(next_button)

        home_button = QAction("Home", self)
        home_button.setStatusTip('Go to the home page (Google page)')
        home_button.triggered.connect(self.go_to_home)
        self.navigation_bar.addAction(home_button)

        self.navigation_bar.addSeparator()

        self.new_tab_button = QAction("+", self)
        self.new_tab_button.setStatusTip('Open a new tab')
        self.new_tab_button.triggered.connect(self.create_new_tab)
        self.navigation_bar.addAction(self.new_tab_button)

        self.URLBar = QLineEdit()
        self.URLBar.returnPressed.connect(self.navigate_to_current_tab)
        self.navigation_bar.addWidget(self.URLBar)

        search_button = QAction("Search", self)
        search_button.setStatusTip('Search the web')
        search_button.triggered.connect(self.search_button_clicked)
        self.navigation_bar.addAction(search_button)

        self.search_engine_combo = QComboBox(self)
        self.search_engine_combo.addItems(['Google', 'Bing', 'DuckDuckGo', 'Yahoo'])
        self.navigation_bar.addWidget(self.search_engine_combo)

        go_button = QAction("Go", self)
        go_button.setStatusTip('Go to the selected search engine')
        go_button.triggered.connect(self.go_to_selected_engine)
        self.navigation_bar.addAction(go_button)

        self.addToolBarBreak()

        bookmarks_toolbar = QToolBar('Bookmarks', self)
        self.addToolBar(bookmarks_toolbar)

        bookmarks = [
            ("Facebook", 'Go to Facebook', "https://www.facebook.com"),
            ("Youtube", 'Go to YouTube', "https://www.youtube.com"),
            ("Instagram", 'Go to Instagram', "https://www.instagram.com"),
            ("Twitter", 'Go to Twitter', "https://www.twitter.com")
        ]

        for name, status_tip, url in bookmarks:
            action = QAction(name, self)
            action.setStatusTip(status_tip)
            action.triggered.connect(lambda _, u=url: self.create_tab(u))
            bookmarks_toolbar.addAction(action)

        self.show()

        self.current_browser = QWebEngineView()
        self.current_browser.urlChanged.connect(lambda qurl, browser=self.current_browser:
                                                 self.update_address_bar(qurl, browser))

        self.history_list = set()
        self.history_manager = HistoryManager(self.history_list, self.clear_browsing_history, self)
        self.history_manager.item_selected.connect(self.navigate_to_url_from_history)

        history_button = QAction("History", self)
        history_button.setStatusTip('View browsing history')
        history_button.triggered.connect(self.show_history)
        self.navigation_bar.addAction(history_button)

        self.accept_navigation.connect(self.navigate_to_url_from_history)

        self.incognito_mode_enabled = False

        self.create_tab('https://www.google.com')

        self.shortcut_manager = ShortcutManager(self)

        # Fitur 1: Tab Bar Multi-Line
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setUsesScrollButtons(True)

        # Fitur 3: Pengelolaan Bookmark yang Lebih Baik
        self.manage_bookmarks_action = QAction("Manage Bookmarks", self)
        self.manage_bookmarks_action.setStatusTip('Manage your bookmarks')
        self.manage_bookmarks_action.triggered.connect(self.show_bookmark_manager)
        self.navigation_bar.addAction(self.manage_bookmarks_action)

        # Fitur 5: Mode Malam dan Mode Terang
        self.night_mode_action = QAction("Night Mode", self, checkable=True)
        self.night_mode_action.setStatusTip('Toggle night mode')
        self.night_mode_action.toggled.connect(self.toggle_night_mode)
        self.navigation_bar.addAction(self.night_mode_action)

        # Fitur 7: Manajemen Riwayat Browsing yang Lebih Baik
        self.clear_history_action = QAction("Clear History", self)
        self.clear_history_action.setStatusTip('Clear browsing history')
        self.clear_history_action.triggered.connect(self.clear_browsing_history)
        self.navigation_bar.addAction(self.clear_history_action)

        # Mode Incognito
        self.incognito_mode_action = QAction("Incognito Mode", self, checkable=True)
        self.incognito_mode_action.setStatusTip('Toggle incognito mode')
        self.incognito_mode_action.toggled.connect(self.toggle_incognito_mode)
        self.navigation_bar.addAction(self.incognito_mode_action)

    def go_to_home(self):
        self.current_browser.setUrl(QUrl('https://www.google.com/'))

    def navigate_back(self):
        self.current_browser.back()

    def reload_page(self):
        self.current_browser.reload()

    def navigate_forward(self):
        self.current_browser.forward()

    def navigate_to_url(self):
        q = QUrl(self.URLBar.text())
        if q.scheme() == "":
            q.setScheme("http")
        self.current_browser.setUrl(q)
        self.update_history(q.toString())

    def create_tab(self, url):
        browser = Browser()
        browser.navigate_to_url(url)
        i = self.tabs.addTab(browser, url)
        self.tabs.setCurrentIndex(i)
        browser.loadFinished.connect(lambda _, i=i, browser=browser: self.tabs.setTabText(i, browser.page().title()))
        self.update_history(url)

    def create_new_tab(self, url=None):
        # Cek apakah mode incognito diaktifkan
        if self.incognito_mode_enabled:
            self.create_new_incognito_tab()
        else:
            # Mode incognito tidak diaktifkan, lanjutkan seperti sebelumnya
            browser = Browser()
            browser.navigate_to_url(url) if url else browser.navigate_to_url('https://www.google.com')
            i = self.tabs.addTab(browser, url if url else 'https://www.google.com')
            self.tabs.setCurrentIndex(i)
            browser.loadFinished.connect(lambda _, i=i, browser=browser: self.tabs.setTabText(i, browser.page().title()))
            self.update_history(url if url else 'https://www.google.com')

    def close_tab(self, i):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(i)

    def current_tab_changed(self, i):
        self.current_browser = self.tabs.widget(i)
        self.current_browser.urlChanged.connect(lambda qurl, browser=self.current_browser:
                                                self.update_address_bar(qurl, browser))
        qurl = self.current_browser.url()
        self.update_address_bar(qurl, self.current_browser)

    def update_address_bar(self, qurl, browser=None):
        if not qurl or (browser and browser != self.current_browser):
            return
        self.URLBar.setText(qurl.toString())
        self.URLBar.setCursorPosition(0)

    def search_button_clicked(self):
        search_query = self.URLBar.text()
        selected_search_engine = self.search_engine_combo.currentText()

        if not search_query:
            self.go_to_home()
        else:
            search_url = self.get_search_url(search_query, selected_search_engine)
            self.current_browser.setUrl(QUrl(search_url))

    def go_to_selected_engine(self):
        selected_search_engine = self.search_engine_combo.currentText()

        if selected_search_engine == 'Google':
            self.current_browser.setUrl(QUrl('https://www.google.com'))
        elif selected_search_engine == 'Bing':
            self.current_browser.setUrl(QUrl('https://www.bing.com'))
        elif selected_search_engine == 'DuckDuckGo':
            self.current_browser.setUrl(QUrl('https://duckduckgo.com'))
        elif selected_search_engine == 'Yahoo':
            self.current_browser.setUrl(QUrl('https://www.yahoo.com'))

    def navigate_to_current_tab(self):
        current_browser = self.current_browser
        input_text = self.URLBar.text()

        parsed_url = urlparse(input_text)
        if parsed_url.scheme and parsed_url.netloc:
            current_browser.navigate_to_url(input_text)
            if not self.incognito_mode_enabled:
                self.update_history(input_text)
        else:
            search_url = self.get_search_url(input_text)
            current_browser.navigate_to_url(search_url)
            if not self.incognito_mode_enabled:
                self.update_history(search_url)

    def show_bookmark_manager(self):
        # Implementasi pengelolaan bookmark yang lebih baik
        dialog = QDialog(self)
        dialog.setWindowTitle('Pengelolaan Bookmark')

        # Tambahkan elemen-elemen UI seperti daftar bookmark, tombol tambah, hapus, dll.
        # sesuai dengan kebutuhan.

        # Contoh:
        bookmark_list = QListWidget(dialog)
        add_button = QPushButton("Tambah Bookmark", dialog)
        remove_button = QPushButton("Hapus Bookmark", dialog)

        # Atur tata letak elemen-elemen UI di dalam dialog menggunakan QVBoxLayout atau QGridLayout.

        # Tambahkan logika untuk memperbarui dan mengelola daftar bookmark saat tombol-tombol ditekan.

        layout = QVBoxLayout(dialog)
        layout.addWidget(bookmark_list)
        layout.addWidget(add_button)
        layout.addWidget(remove_button)

        # Tampilkan dialog dan tangkap hasilnya jika diperlukan.
        result = dialog.exec_()
        if result == QDialog.Accepted:
            # Implementasi logika pengelolaan bookmark di sini.
            pass

    def add_bookmark(self, bookmark_list):
        # Mendapatkan URL dari halaman yang sedang ditampilkan di browser saat ini
        current_url = self.current_browser.url().toString()

        # Memastikan URL belum ada di daftar bookmark sebelum menambahkannya
        if current_url not in self.history_list:
            # Menambahkan URL ke daftar bookmark dan memperbarui daftar bookmark
            self.history_list.add(current_url)
            bookmark_list.addItem(QListWidgetItem(current_url))

    def remove_bookmark(self, bookmark_list):
        # Mendapatkan item terpilih dari daftar bookmark
        selected_item = bookmark_list.currentItem()

        if selected_item is not None:
            # Mendapatkan URL dari item terpilih
            selected_url = selected_item.text()

            # Menghapus URL dari daftar bookmark dan memperbarui daftar bookmark
            self.history_list.remove(selected_url)
            bookmark_list.takeItem(bookmark_list.row(selected_item))

    def get_search_url(self, query, engine=None):
        search_engines = {
            'Google': 'https://www.google.com/search?q={}',
            'Bing': 'https://www.bing.com/search?q={}',
            'DuckDuckGo': 'https://duckduckgo.com/?q={}',
            'Yahoo': 'https://search.yahoo.com/search?p={}',
        }
        selected_engine = engine if engine else self.search_engine_combo.currentText()
        return search_engines.get(selected_engine, 'https://www.google.com').format(query.replace(" ", "+"))

    def show_history(self):
        self.history_manager.exec_()

    def update_history(self, url):
        current_url = self.current_browser.url().toString()
        if current_url not in self.history_list:
            self.history_list.add(current_url)
            self.history_manager.populate_history_list()

    def navigate_to_url_from_history(self, url):
        self.URLBar.setText(url.toString())
        self.navigate_to_url()

        # Tambahkan metode berikut ke dalam kelas Window di dalam metode __init__ atau tempat yang sesuai

    def show_bookmark_manager(self):
        # Implementasi pengelolaan bookmark yang lebih baik
        dialog = QDialog(self)
        dialog.setWindowTitle('Pengelolaan Bookmark')

        # Tambahkan elemen-elemen UI seperti daftar bookmark, tombol tambah, hapus, dll.
        # sesuai dengan kebutuhan.

        # Contoh:
        bookmark_list = QListWidget(dialog)
        add_button = QPushButton("Tambah Bookmark", dialog)
        remove_button = QPushButton("Hapus Bookmark", dialog)

        # Populasi daftar bookmark dengan URL dari riwayat browsing
        for url in self.history_list:
            item = QListWidgetItem(url)
            bookmark_list.addItem(item)

        # Atur tata letak elemen-elemen UI di dalam dialog menggunakan QVBoxLayout atau QGridLayout.

        # Tambahkan logika untuk memperbarui dan mengelola daftar bookmark saat tombol-tombol ditekan.
        add_button.clicked.connect(lambda: self.add_bookmark(bookmark_list))
        remove_button.clicked.connect(lambda: self.remove_bookmark(bookmark_list))

        layout = QVBoxLayout(dialog)
        layout.addWidget(bookmark_list)
        layout.addWidget(add_button)
        layout.addWidget(remove_button)

        # Tampilkan dialog dan tangkap hasilnya jika diperlukan.
        result = dialog.exec_()
        if result == QDialog.Accepted:
            # Implementasi logika pengelolaan bookmark di sini.
            pass
        
    def toggle_incognito_mode(self, checked):
        if checked:
            # Aktifkan mode incognito
            self.incognito_mode_enabled = True
            self.history_list.clear()

            # Buat tab baru sebagai tab incognito
            self.create_new_incognito_tab()
        else:
            # Matikan mode incognito
            self.incognito_mode_enabled = False
            self.create_new_tab()

    def create_new_incognito_tab(self):
        incognito_browser = Browser(is_incognito=True)
        incognito_browser.setUrl(QUrl('https://www.google.com'))  # Atur halaman beranda untuk tab incognito
        incognito_browser.page().profile().setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        incognito_browser.page().profile().clearHttpCache()

        # Tambahkan tab incognito ke tab widget
        i = self.tabs.addTab(incognito_browser, 'Incognito')
        self.tabs.setCurrentIndex(i)

        # Tambahkan event listener untuk mengupdate alamat URL saat berubah
        incognito_browser.urlChanged.connect(lambda qurl, browser=incognito_browser:
                                             self.update_address_bar(qurl, browser))

        # Update riwayat dengan URL saat ini
        if not self.incognito_mode_enabled:
            self.update_history('https://www.google.com')  # Ganti dengan URL beranda tab incognito

    # Fitur 5: Mode Malam dan Mode Terang
    def toggle_night_mode(self, checked):
        if checked:
            # Implementasi untuk mode malam
            self.setStyleSheet("background-color: #2a2a2a; color: #ffffff;")
        else:
            # Implementasi untuk mode terang
            self.setStyleSheet("")

    # Fitur 7: Manajemen Riwayat Browsing yang Lebih Baik
    def clear_browsing_history(self):
        self.history_list.clear()
        self.history_manager.list_widget.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName('WEB BROWSER')
    window = Window()
    window.show()
    app.exec_()