import sys
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QMessageBox, QButtonGroup, QDialog, QDesktopWidget, QTableWidget, QTableWidgetItem
)

from component.phone_sales import PhoneSalesManager


class MarketShareTab(QWidget):
    """市场占比-饼图选项卡"""
    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadData()

    def initUI(self):
        layout = QVBoxLayout()

        # 创建 matplotlib 图形
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def loadData(self):
        """从数据库加载数据并绘制饼图"""
        try:
            connection = sqlite3.connect("../phone_sales.db")
            cursor = connection.cursor()
            cursor.execute("SELECT brand, SUM(sales) FROM phone_sales GROUP BY brand")
            data = cursor.fetchall()

            brands = [item[0] for item in data]
            sales = [item[1] for item in data]

            self.ax.clear()
            self.ax.pie(sales, labels=brands, autopct="%1.1f%%", startangle=90)
            self.ax.axis("equal")  # 保持圆形
            self.canvas.draw()

            connection.close()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据失败: {e}")


class SalesBarChartTab(QWidget):
    """手机销量-柱状图选项卡"""
    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadData()

    def initUI(self):
        layout = QVBoxLayout()

        # 创建 matplotlib 图形
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def loadData(self):
        """从数据库加载数据并绘制柱状图"""
        try:
            connection = sqlite3.connect("../phone_sales.db")
            cursor = connection.cursor()
            cursor.execute("SELECT price, sales FROM phone_sales")
            data = cursor.fetchall()

            # 将价格划分为区间
            price_bins = [0, 1000, 2000, 3000, 4000, 5000, float('inf')]  # 定义价格区间
            price_labels = ['0-1000', '1000-2000', '2000-3000', '3000-4000', '4000-5000', '5000+']  # 定义区间标签

            # 将价格数据分配到对应的区间
            prices = [float(item[0]) for item in data]
            sales = [int(item[1]) for item in data]
            price_groups = pd.cut(prices, bins=price_bins, labels=price_labels)

            # 计算每个价格区间的销量总和
            sales_by_price = pd.Series(sales).groupby(price_groups).sum()

            # 绘制柱状图
            self.ax.clear()
            sales_by_price.plot(kind='bar', color='skyblue', ax=self.ax)
            self.ax.set_xlabel("价格区间")
            self.ax.set_ylabel("销量")
            self.ax.set_title("价格区间与销量柱状图")
            self.canvas.draw()

            connection.close()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据失败: {e}")


class CorrelationScatterTab(QWidget):
    """相关性分析-散点图选项卡"""
    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadData()

    def initUI(self):
        layout = QVBoxLayout()

        # 创建 matplotlib 图形
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def loadData(self):
        """从数据库加载数据并绘制散点图"""
        try:
            connection = sqlite3.connect("../phone_sales.db")
            cursor = connection.cursor()
            # 查询评分和评论数
            cursor.execute("SELECT star, comments_count FROM phone_sales")
            data = cursor.fetchall()

            # 提取评分和评论数
            stars = [item[0] for item in data]  # 评分
            comments = [item[1] for item in data]  # 评论数

            # 绘制散点图
            self.ax.clear()
            self.ax.scatter(stars, comments, color="red")
            self.ax.set_xlabel("评分")
            self.ax.set_ylabel("评论数")
            self.ax.set_title("评分与评论数相关性分析")
            self.canvas.draw()

            connection.close()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据失败: {e}")


class MainWindow(QTabWidget):
    """主窗口"""
    def __init__(self, is_admin):
        super().__init__()
        self.is_admin = is_admin  # 是否是管理员
        self.initUI()

    def initUI(self):
        self.setWindowTitle("手机销售数据分析")
        self.setGeometry(100, 100, 800, 600)

        # 添加选项卡
        self.addTab(PhoneSalesManager(self.is_admin), "手机销售数据")
        self.addTab(MarketShareTab(), "市场占比-饼图")
        self.addTab(SalesBarChartTab(), "手机销量-柱状图")
        self.addTab(CorrelationScatterTab(), "相关性分析-散点图")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(is_admin=True)  # 默认以管理员身份打开
    window.show()
    sys.exit(app.exec_())