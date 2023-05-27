from PyQt5.QtWidgets import QApplication, QWidget, QSplitter, QGridLayout, QPushButton, QVBoxLayout

class GridWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        vbox = QVBoxLayout()
        splitter = QSplitter()

        grid = QGridLayout()
        grid.addWidget(self.create_button('1'), 0, 0)
        grid.addWidget(self.create_button('2'), 0, 1)
        grid.addWidget(self.create_button('3'), 0, 2)
        grid.addWidget(self.create_button('4'), 1, 0, 2, 1)  # This creates a tall 1x2 button
        grid.addWidget(self.create_button('5'), 1, 1)
        grid.addWidget(self.create_button('6'), 1, 2)

        widget = QWidget()
        widget.setLayout(grid)

        splitter.addWidget(widget)
        vbox.addWidget(splitter)

        self.setLayout(vbox)
        self.setGeometry(300, 300, 280, 170)
        self.setWindowTitle('Buttons')
        self.show()

    def create_button(self, text):
        button = QPushButton(text, self)
        return button

if __name__ == '__main__':
    app = QApplication([])
    grid = GridWidget()
    app.exec_()



