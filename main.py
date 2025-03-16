from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow


class Order(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lui = uic.loadUi("login.ui", self)