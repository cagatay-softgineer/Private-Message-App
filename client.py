import sys
import json
import requests
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QLabel, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Server Selection Example")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Read JSON file and create server list
        self.servers_file = 'servers.json'
        with open(self.servers_file) as f:
            self.servers = json.load(f)

        self.server_combobox = QComboBox()
        for server in self.servers:
            self.server_combobox.addItem(server['name'], server)

        self.server_combobox.currentIndexChanged.connect(self.select_server)
        self.layout.addWidget(self.server_combobox)

        # Connect Server Button
        self.connect_button = QPushButton("Connect Server")
        self.connect_button.clicked.connect(self.delayed_connect_server)
        self.layout.addWidget(self.connect_button)
        self.connect_button.setEnabled(False)  # Initially disable until server is checked

        self.webview = QWebEngineView()
        self.layout.addWidget(self.webview)

        self.error_label = QLabel("Server not reachable or disabled.")
        self.error_label.setStyleSheet("color: red; font-weight: bold;")
        self.error_label.setVisible(False)
        self.layout.addWidget(self.error_label)

        # Timer for error label visibility
        self.error_timer = QTimer(self)
        self.error_timer.setSingleShot(True)
        self.error_timer.timeout.connect(self.hide_error_label)

        
        # Timer for delayed connect action
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.do_connect_server)

    def hide_error_label(self):
        self.error_label.setVisible(False)
    
    def select_server(self, index):
        server = self.server_combobox.currentData()
        
        # Check if 'enabled' key exists and is True
        if 'enabled' in server and server['enabled']:
            server = self.server_combobox.currentData()
            url = f"http://{server['ip']}"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    if 'enabled' in server and not server['enabled']:
                        server['enabled'] = True
                        self.update_json_file()  # Update JSON file on status change
                    self.error_label.setText("Server is reachable.")
                    self.error_label.setStyleSheet("color: green; font-weight: bold;")
                    self.connect_button.setEnabled(True)  # Enable connect button if server is reachable
                else:
                    if 'enabled' in server and server['enabled']:
                        server['enabled'] = False
                        self.update_json_file()  # Update JSON file on status change
                    self.error_label.setText(f"Server is not reachable (Status Code: {response.status_code})")
                    self.error_label.setStyleSheet("color: red; font-weight: bold;")
                    self.connect_button.setEnabled(False)  # Disable connect button if server is not reachable
                self.error_label.setVisible(True)
                self.error_timer.start(5000)
            except requests.ConnectionError:
                self.error_label.setText("Failed to connect to the server.")
                self.error_label.setStyleSheet("color: red; font-weight: bold;")
                self.error_label.setVisible(True)
                self.error_timer.start(5000)
                self.connect_button.setEnabled(False)
                html_content = """
                <html>
                <head><style>
                h2 { color: red; }
                p { color: red; }
                </style></head>
                <body>
                <h2>Server Disabled</h2>
                <p>This server is currently disabled.</p>
                </body>
                </html>
                """
                self.webview.setHtml(html_content)
        else:
            html_content = """
                <html>
                <head><style>
                h2 { color: red; }
                p { color: red; }
                </style></head>
                <body>
                <h2>Server Disabled</h2>
                <p>This server is currently disabled.</p>
                </body>
                </html>
            """
            self.webview.setHtml(html_content)
            self.error_label.setVisible(True)
            self.error_timer.start(5000)
            self.connect_button.setEnabled(False)  # Disable connect button if server is disabled

    def delayed_connect_server(self):
        # Start timer to delay connect action
        self.timer.start(500)  # Adjust delay time (in milliseconds) as needed

    def do_connect_server(self):
        # Called after delay to actually connect to the server
        server = self.server_combobox.currentData()
        url = f"http://{server['ip']}"
        qurl = QUrl(url)
        self.webview.load(qurl)

    def update_json_file(self):
        with open(self.servers_file, 'w') as f:
            json.dump(self.servers, f, indent=4)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
