import sys
import sqlite3
import pandas as pd  # 导入 pandas 库
import requests
from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QMessageBox, QInputDialog, QFileDialog, QDialog, QFormLayout, QLabel
)


class DetailDialog(QDialog):
    """查看详情对话框"""
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("查看详情")
        self.resize(400, 400)  # 调整窗口大小以容纳图片

        # 布局
        layout = QVBoxLayout()

        # 图片地址
        img_url = data[0]  # 第一个字段是图片地址
        if img_url == "无":
            # 如果图片地址为“无”，显示文本
            no_image_label = QLabel("无图片")
            no_image_label.setAlignment(Qt.AlignCenter)  # 居中显示
            layout.addWidget(no_image_label)
        else:
            # 尝试从互联网加载图片
            try:
                # 使用 requests 下载图片
                response = requests.get(img_url)
                if response.status_code == 200:
                    # 将图片数据加载到 QPixmap
                    pixmap = QPixmap()
                    pixmap.loadFromData(QByteArray(response.content))
                    if pixmap.isNull():
                        # 如果图片加载失败，显示错误信息
                        error_label = QLabel("图片加载失败")
                        error_label.setAlignment(Qt.AlignCenter)
                        layout.addWidget(error_label)
                    else:
                        # 显示图片
                        image_label = QLabel()
                        image_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio))  # 缩放图片
                        image_label.setAlignment(Qt.AlignCenter)
                        layout.addWidget(image_label)
                else:
                    # 如果请求失败，显示错误信息
                    error_label = QLabel("无法下载图片")
                    error_label.setAlignment(Qt.AlignCenter)
                    layout.addWidget(error_label)
            except Exception as e:
                # 如果发生异常，显示错误信息
                error_label = QLabel(f"图片加载失败: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(error_label)

        # 字段名称
        fields = [
            "图片地址", "标题", "品牌", "价格", "销量_文本", "销量", "店铺名称", "评论数_字符", "评论数", "评分"
        ]

        # 添加字段到布局
        form_layout = QFormLayout()
        for field, value in zip(fields[1:], data[1:]):  # 跳过图片地址字段
            label = QLabel(value)
            form_layout.addRow(field, label)

        layout.addLayout(form_layout)
        self.setLayout(layout)


class PhoneSalesManager(QWidget):
    def __init__(self, is_admin):
        super().__init__()
        self.is_admin = is_admin  # 是否是管理员
        self.initUI()
        self.connectDB()
        self.loadData()

    def initUI(self):
        self.setWindowTitle("手机销售数据管理系统")
        self.setGeometry(100, 100, 1200, 800)

        # 布局
        layout = QVBoxLayout()

        # 搜索栏
        searchLayout = QHBoxLayout()
        self.searchInput = QLineEdit(self)
        self.searchInput.setPlaceholderText("输入标题搜索")
        self.brandInput = QLineEdit(self)  # 新增品牌输入框
        self.brandInput.setPlaceholderText("输入品牌搜索")
        self.minPriceInput = QLineEdit(self)  # 新增最小价格输入框
        self.minPriceInput.setPlaceholderText("最小价格")
        self.maxPriceInput = QLineEdit(self)  # 新增最大价格输入框
        self.maxPriceInput.setPlaceholderText("最大价格")
        searchButton = QPushButton("搜索", self)
        searchButton.clicked.connect(self.searchData)
        searchLayout.addWidget(self.searchInput)
        searchLayout.addWidget(self.brandInput)  # 添加品牌输入框
        searchLayout.addWidget(self.minPriceInput)  # 添加最小价格输入框
        searchLayout.addWidget(self.maxPriceInput)  # 添加最大价格输入框
        searchLayout.addWidget(searchButton)
        layout.addLayout(searchLayout)

        # 表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            ["图片地址", "标题", "品牌", "价格", "销量_文本", "销量", "店铺名称", "评论数_字符", "评论数", "评分"]
        )
        layout.addWidget(self.table)

        # 如果是管理员，显示按钮；否则隐藏
        if self.is_admin:
            # 按钮
            self.buttonLayout = QHBoxLayout()
            self.addButton = QPushButton("添加", self)
            self.deleteButton = QPushButton("删除", self)
            self.updateButton = QPushButton("修改", self)
            self.detailButton = QPushButton("查看详情", self)
            self.exportButton = QPushButton("导出为 Excel", self)
            self.buttonLayout.addWidget(self.addButton)
            self.buttonLayout.addWidget(self.deleteButton)
            self.buttonLayout.addWidget(self.updateButton)
            self.buttonLayout.addWidget(self.detailButton)
            self.buttonLayout.addWidget(self.exportButton)
            self.addButton.clicked.connect(self.addData)
            self.deleteButton.clicked.connect(self.deleteData)
            self.updateButton.clicked.connect(self.updateData)
        else:
            self.buttonLayout = QHBoxLayout()
            self.detailButton = QPushButton("查看详情", self)
            self.exportButton = QPushButton("导出为 Excel", self)
            self.buttonLayout.addWidget(self.detailButton)
            self.buttonLayout.addWidget(self.exportButton)

        layout.addLayout(self.buttonLayout)
        self.setLayout(layout)
        self.detailButton.clicked.connect(self.showDetail)
        self.exportButton.clicked.connect(self.exportToExcel)

    def connectDB(self):
        """连接 SQLite 数据库"""
        try:
            self.connection = sqlite3.connect("../phone_sales.db")  # 数据库文件
            self.cursor = self.connection.cursor()
            # 如果表不存在，则创建表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS phone_sales (
                    img TEXT,
                    title TEXT NOT NULL,
                    brand TEXT,
                    price TEXT,
                    sales_text TEXT,
                    sales TEXT,
                    shopname TEXT,
                    comments_count_text TEXT,
                    comments_count TEXT,
                    star TEXT
                )
            """)
            self.connection.commit()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"数据库连接失败: {e}")
            sys.exit()

    def loadData(self):
        """加载数据到表格"""
        try:
            self.cursor.execute("SELECT * FROM phone_sales")
            phones = self.cursor.fetchall()

            self.table.setRowCount(0)
            for row, phone in enumerate(phones):
                self.table.insertRow(row)
                for col, value in enumerate(phone):
                    self.table.setItem(row, col, QTableWidgetItem(str(value)))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据失败: {e}")

    def searchData(self):
        """条件搜索：按标题、品牌、价格区间搜索"""
        # 获取搜索条件
        title = self.searchInput.text().strip()
        brand = self.brandInput.text().strip()
        min_price = self.minPriceInput.text().strip()  # 最小价格
        max_price = self.maxPriceInput.text().strip()  # 最大价格

        # 如果没有输入任何条件，则加载全部数据
        if not title and not brand and not min_price and not max_price:
            self.loadData()
            return

        try:
            # 动态构建 SQL 查询
            query = "SELECT * FROM phone_sales WHERE 1=1"
            params = []

            if title:
                query += " AND title LIKE ?"
                params.append(f"%{title}%")
            if brand:
                query += " AND brand LIKE ?"
                params.append(f"%{brand}%")
            if min_price:
                query += " AND CAST(price AS REAL) >= ?"
                params.append(float(min_price))
            if max_price:
                query += " AND CAST(price AS REAL) <= ?"
                params.append(float(max_price))

            # 执行查询
            self.cursor.execute(query, params)
            phones = self.cursor.fetchall()

            # 更新表格数据
            self.table.setRowCount(0)
            for row, phone in enumerate(phones):
                self.table.insertRow(row)
                for col, value in enumerate(phone):
                    self.table.setItem(row, col, QTableWidgetItem(str(value)))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {e}")

    def addData(self):
        """添加数据"""
        img, ok = QInputDialog.getText(self, "添加手机销售数据", "图片地址:")
        if not ok or not img:
            return

        title, ok = QInputDialog.getText(self, "添加手机销售数据", "标题:")
        if not ok or not title:
            return

        brand, ok = QInputDialog.getText(self, "添加手机销售数据", "品牌:")
        if not ok or not brand:
            return

        price, ok = QInputDialog.getText(self, "添加手机销售数据", "价格:")
        if not ok or not price:
            return

        sales_text, ok = QInputDialog.getText(self, "添加手机销售数据", "销量_文本:")
        if not ok or not sales_text:
            return

        sales, ok = QInputDialog.getText(self, "添加手机销售数据", "销量:")
        if not ok or not sales:
            return

        shopname, ok = QInputDialog.getText(self, "添加手机销售数据", "店铺名称:")
        if not ok or not shopname:
            return

        comments_count_text, ok = QInputDialog.getText(self, "添加手机销售数据", "评论数_字符:")
        if not ok or not comments_count_text:
            return

        comments_count, ok = QInputDialog.getText(self, "添加手机销售数据", "评论数:")
        if not ok or not comments_count:
            return

        star, ok = QInputDialog.getText(self, "添加手机销售数据", "评分:")
        if not ok or not star:
            return

        try:
            self.cursor.execute(
                "INSERT INTO phone_sales (img, title, brand, price, sales_text, sales, shopname, comments_count_text, comments_count, star) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (img, title, brand, price, sales_text, sales, shopname, comments_count_text, comments_count, star)
            )
            self.connection.commit()
            self.loadData()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加失败: {e}")

    def deleteData(self):
        """删除数据"""
        selectedRow = self.table.currentRow()
        if selectedRow == -1:
            QMessageBox.warning(self, "警告", "请选择要删除的行")
            return

        title = self.table.item(selectedRow, 1).text()
        try:
            self.cursor.execute("DELETE FROM phone_sales WHERE title = ?", (title,))
            self.connection.commit()
            self.loadData()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {e}")

    def updateData(self):
        """修改数据"""
        selectedRow = self.table.currentRow()
        if selectedRow == -1:
            QMessageBox.warning(self, "警告", "请选择要修改的行")
            return

        img = self.table.item(selectedRow, 0).text()
        title = self.table.item(selectedRow, 1).text()
        brand = self.table.item(selectedRow, 2).text()
        price = self.table.item(selectedRow, 3).text()
        sales_text = self.table.item(selectedRow, 4).text()
        sales = self.table.item(selectedRow, 5).text()
        shopname = self.table.item(selectedRow, 6).text()
        comments_count_text = self.table.item(selectedRow, 7).text()
        comments_count = self.table.item(selectedRow, 8).text()
        star = self.table.item(selectedRow, 9).text()

        img, ok = QInputDialog.getText(self, "修改手机销售数据", "图片地址:", text=img)
        if not ok or not img:
            return

        title, ok = QInputDialog.getText(self, "修改手机销售数据", "标题:", text=title)
        if not ok or not title:
            return

        brand, ok = QInputDialog.getText(self, "修改手机销售数据", "品牌:", text=brand)
        if not ok or not brand:
            return

        price, ok = QInputDialog.getText(self, "修改手机销售数据", "价格:", text=price)
        if not ok or not price:
            return

        sales_text, ok = QInputDialog.getText(self, "修改手机销售数据", "销量_文本:", text=sales_text)
        if not ok or not sales_text:
            return

        sales, ok = QInputDialog.getText(self, "修改手机销售数据", "销量:", text=sales)
        if not ok or not sales:
            return

        shopname, ok = QInputDialog.getText(self, "修改手机销售数据", "店铺名称:", text=shopname)
        if not ok or not shopname:
            return

        comments_count_text, ok = QInputDialog.getText(self, "修改手机销售数据", "评论数_字符:", text=comments_count_text)
        if not ok or not comments_count_text:
            return

        comments_count, ok = QInputDialog.getText(self, "修改手机销售数据", "评论数:", text=comments_count)
        if not ok or not comments_count:
            return

        star, ok = QInputDialog.getText(self, "修改手机销售数据", "评分:", text=star)
        if not ok or not star:
            return

        try:
            self.cursor.execute(
                "UPDATE phone_sales SET img = ?, title = ?, brand = ?, price = ?, sales_text = ?, sales = ?, shopname = ?, comments_count_text = ?, comments_count = ?, star = ? WHERE title = ?",
                (img, title, brand, price, sales_text, sales, shopname, comments_count_text, comments_count, star, title)
            )
            self.connection.commit()
            self.loadData()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"修改失败: {e}")

    def showDetail(self):
        """查看详情"""
        selectedRow = self.table.currentRow()
        if selectedRow == -1:
            QMessageBox.warning(self, "警告", "请选择要查看的行")
            return

        # 获取选中行的数据
        data = []
        for col in range(self.table.columnCount()):
            data.append(self.table.item(selectedRow, col).text())

        # 弹出详情对话框
        detailDialog = DetailDialog(data, self)
        detailDialog.exec_()

    def exportToExcel(self):
        """导出数据为 Excel 文件"""
        try:
            # 从数据库加载数据
            self.cursor.execute("SELECT * FROM phone_sales")
            data = self.cursor.fetchall()

            # 将数据转换为 pandas DataFrame
            columns = ["图片地址", "标题", "品牌", "价格", "销量_文本", "销量", "店铺名称", "评论数_字符", "评论数", "评分"]
            df = pd.DataFrame(data, columns=columns)

            # 弹出文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(self, "保存 Excel 文件", "", "Excel 文件 (*.xlsx)")

            if file_path:
                # 导出为 Excel 文件
                df.to_excel(file_path, index=False)
                QMessageBox.information(self, "成功", f"数据已导出到 {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def closeEvent(self, event):
        """关闭窗口时断开数据库连接"""
        self.cursor.close()
        self.connection.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PhoneSalesManager(is_admin=True)  # 默认以管理员身份打开
    window.show()
    sys.exit(app.exec_())