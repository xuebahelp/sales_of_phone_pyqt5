import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QMessageBox, QButtonGroup, QDialog, QDesktopWidget
)


class RegisterDialog(QDialog):
    """注册界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("注册")
        self.resize(300, 150)  # 设置注册界面大小

        # 布局
        layout = QVBoxLayout()

        # 用户名输入
        self.usernameLabel = QLabel("用户名:", self)
        self.usernameInput = QLineEdit(self)
        layout.addWidget(self.usernameLabel)
        layout.addWidget(self.usernameInput)

        # 密码输入
        self.passwordLabel = QLabel("密码:", self)
        self.passwordInput = QLineEdit(self)
        self.passwordInput.setEchoMode(QLineEdit.Password)  # 密码隐藏
        layout.addWidget(self.passwordLabel)
        layout.addWidget(self.passwordInput)

        # 注册按钮
        self.registerButton = QPushButton("提交注册", self)
        self.registerButton.clicked.connect(self.register)
        layout.addWidget(self.registerButton)

        self.setLayout(layout)

        # 注册界面居中显示
        self.center()

    def center(self):
        """将注册界面居中显示"""
        screen = QDesktopWidget().screenGeometry()  # 获取屏幕尺寸
        size = self.geometry()  # 获取窗口尺寸
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def register(self):
        """注册逻辑"""
        username = self.usernameInput.text().strip()
        password = self.passwordInput.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "警告", "用户名和密码不能为空")
            return

        # 检查用户名是否已存在
        parent = self.parent()
        parent.cursor.execute("SELECT * FROM user WHERE username = ?", (username,))
        if parent.cursor.fetchone():
            QMessageBox.warning(self, "警告", "当前用户已经注册")
            return

        # 插入新用户
        try:
            parent.cursor.execute("INSERT INTO user (username, password) VALUES (?, ?)", (username, password))
            parent.connection.commit()
            QMessageBox.information(self, "成功", "注册成功")
            self.close()  # 关闭注册界面
        except Exception as e:
            QMessageBox.critical(self, "错误", f"注册失败: {e}")


class LoginWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.connectDB()

    def initUI(self):
        self.setWindowTitle("登录界面")
        self.resize(300, 200)  # 设置窗口大小

        # 布局
        layout = QVBoxLayout()

        # 用户名输入
        self.usernameLabel = QLabel("用户名:", self)
        self.usernameInput = QLineEdit(self)
        layout.addWidget(self.usernameLabel)
        layout.addWidget(self.usernameInput)

        # 密码输入
        self.passwordLabel = QLabel("密码:", self)
        self.passwordInput = QLineEdit(self)
        self.passwordInput.setEchoMode(QLineEdit.Password)  # 密码隐藏
        layout.addWidget(self.passwordLabel)
        layout.addWidget(self.passwordInput)

        # 用户类型单选框
        self.userTypeGroup = QButtonGroup(self)  # 用于管理单选框
        self.adminRadio = QRadioButton("管理员", self)
        self.userRadio = QRadioButton("普通用户", self)
        self.userTypeGroup.addButton(self.adminRadio)
        self.userTypeGroup.addButton(self.userRadio)
        self.adminRadio.setChecked(True)  # 默认选择管理员

        # 单选框布局
        radioLayout = QHBoxLayout()
        radioLayout.addWidget(self.adminRadio)
        radioLayout.addWidget(self.userRadio)
        layout.addLayout(radioLayout)

        # 按钮布局
        buttonLayout = QHBoxLayout()
        self.loginButton = QPushButton("登录", self)
        self.loginButton.clicked.connect(self.login)
        self.registerButton = QPushButton("注册", self)
        self.registerButton.clicked.connect(self.showRegisterDialog)
        buttonLayout.addWidget(self.loginButton)
        buttonLayout.addWidget(self.registerButton)
        layout.addLayout(buttonLayout)

        self.setLayout(layout)

        # 窗口居中显示
        self.center()

    def center(self):
        """将窗口居中显示"""
        screen = QDesktopWidget().screenGeometry()  # 获取屏幕尺寸
        size = self.geometry()  # 获取窗口尺寸
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def connectDB(self):
        """连接 SQLite 数据库"""
        try:
            self.connection = sqlite3.connect("../phone_sales.db")  # 数据库文件
            self.cursor = self.connection.cursor()
            # 如果表不存在，则创建表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL
                )
            """)
            # 插入默认管理员账号
            self.cursor.execute("INSERT OR IGNORE INTO user (username, password) VALUES (?, ?)", ("admin", "admin"))
            self.connection.commit()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"数据库连接失败: {e}")
            sys.exit()

    def login(self):
        """登录逻辑"""
        username = self.usernameInput.text().strip()
        password = self.passwordInput.text().strip()
        isAdmin = self.adminRadio.isChecked()  # 判断是否选择管理员

        if not username or not password:
            QMessageBox.warning(self, "警告", "用户名和密码不能为空")
            return

        if isAdmin:
            # 管理员登录
            if username == "admin" and password == "admin":
                QMessageBox.information(self, "成功", "管理员登录成功")
                self.open_main_window(is_admin=True)  # 打开主界面，传递管理员权限
            else:
                QMessageBox.warning(self, "失败", "管理员账号或密码错误")
        else:
            # 普通用户登录
            self.cursor.execute("SELECT * FROM user WHERE username = ? AND password = ?", (username, password))
            user = self.cursor.fetchone()
            if user:
                QMessageBox.information(self, "成功", "普通用户登录成功")
                self.open_main_window(is_admin=False)  # 打开主界面，传递普通用户权限
            else:
                QMessageBox.warning(self, "失败", "账号密码错误或用户名不存在")

    def open_main_window(self, is_admin):
        """打开主界面"""
        from main import MainWindow  # 动态导入 MainWindow
        self.main_window = MainWindow(is_admin)
        self.main_window.show()
        self.close()  # 关闭登录界面

    def showRegisterDialog(self):
        """显示注册界面"""
        if self.adminRadio.isChecked():
            QMessageBox.warning(self, "警告", "管理员账号不支持注册")
            return

        # 弹出注册界面
        registerDialog = RegisterDialog(self)
        registerDialog.exec_()

    def closeEvent(self, event):
        """关闭窗口时断开数据库连接"""
        self.cursor.close()
        self.connection.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWidget()
    window.show()
    sys.exit(app.exec_())