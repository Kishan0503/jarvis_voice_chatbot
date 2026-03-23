import sys
from PyQt6.QtWidgets import QApplication
from ui.app import JarvisApp


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Jarvis")
    app.setQuitOnLastWindowClosed(False)

    jarvis = JarvisApp(app)
    jarvis.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
