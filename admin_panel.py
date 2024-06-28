from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QLabel, QScrollArea, QComboBox, QHBoxLayout
from PyQt5.QtCore import Qt
import pandas as pd
from cryptography.fernet import Fernet, InvalidToken

class AdminPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Panel")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Load encryption key
        with open('secret.key', 'rb') as key_file:
            self.key = key_file.read()
        self.cipher_suite = Fernet(self.key)

        # Read users.xlsx and messages.xlsx
        self.users_df = pd.read_excel('database/users.xlsx')
        self.messages_df = pd.read_excel('database/messages.xlsx')

        # Ensure data type compatibility
        self.messages_df['user_id'] = self.messages_df['user_id'].astype(str)

        # Create user filter
        self.user_filter_combo = QComboBox()
        self.user_filter_combo.addItem("All Users")
        self.user_filter_combo.addItems(self.users_df['username'].tolist())
        self.user_filter_combo.currentIndexChanged.connect(self.display_messages)

        # Create QLabel widget for messages
        self.messages_label = QTextEdit()
        self.messages_label.setReadOnly(True)
        self.messages_label.setStyleSheet("background-color: #f0f0f0; color: #333333; padding: 10px; border: 1px solid #cccccc; border-radius: 5px;")

        # Scroll area for messages
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidget(self.messages_label)

        # Add user filter and messages widget to layout
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by User:"))
        filter_layout.addWidget(self.user_filter_combo)
        filter_layout.addStretch(1)

        self.layout.addLayout(filter_layout)
        self.layout.addWidget(scroll_area)

        # Display messages initially
        self.display_messages()

    def decrypt_message(self, encrypted_message):
        try:
            decrypted_message = self.cipher_suite.decrypt(encrypted_message.encode()).decode()
            return decrypted_message
        except InvalidToken:
            return "Decryption error"

    def display_messages(self):
        selected_user = self.user_filter_combo.currentText()
        if selected_user == "All Users":
            messages_info = ""
            merged_df = pd.merge(self.messages_df, self.users_df, left_on='user_id', right_on='username', how='left')
            if not merged_df.empty:
                for index, row in merged_df.iterrows():
                    decrypted_message = self.decrypt_message(row['message'])
                    messages_info += f"<div><b>{self.users_df['username'][int(row['user_id'])]}</b>: {decrypted_message}</div>"
                self.messages_label.setHtml(messages_info)
            else:
                self.messages_label.setText("<div style='padding: 10px;'><i>No messages found.</i></div>")
        else:
            user_id = self.users_df[self.users_df['username'] == selected_user].index.values.astype(str)[0]
            filtered_messages_df = self.messages_df[self.messages_df['user_id'] == user_id]

            if not filtered_messages_df.empty:
                messages_info = ""
                for index, row in filtered_messages_df.iterrows():
                    decrypted_message = self.decrypt_message(row['message'])
                    messages_info += f"<div><b>{selected_user}</b>: {decrypted_message}</div>"
                self.messages_label.setHtml(messages_info)
            else:
                self.messages_label.setText("<div style='padding: 10px;'><i>No messages found.</i></div>")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = AdminPanel()
    window.show()
    sys.exit(app.exec_())
