import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QDialog, QMessageBox, QPushButton,
    QVBoxLayout, QTableWidgetItem
)
from PyQt5.QtChart import QChart, QChartView, QPieSeries
from PyQt5.QtGui import QPainter
from musicc import Ui_Dialog

class MusicApp(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.create_table_if_not_exists()

        self.ui.btnAdd.clicked.connect(self.add_record)
        self.ui.btnSearch.clicked.connect(self.search_record)
        self.ui.btnUpdate.clicked.connect(self.update_record)
        self.ui.btnDelete.clicked.connect(self.delete_record)


        self.chartButton = QPushButton("Show Chart", self)
        self.chartButton.move(370, 150)
        self.chartButton.resize(100, 30)
        self.chartButton.clicked.connect(self.show_chart)


        self.ui.tableMusic.setColumnCount(9)
        self.ui.tableMusic.setHorizontalHeaderLabels([
            "ID", "Composer", "Composition", "Movement", "Ensemble",
            "Source", "Transcriber", "Catalog Name", "Seconds"
        ])

    def db_connect(self):
        return sqlite3.connect("musika.sqlite3")

    def create_table_if_not_exists(self):
        conn = self.db_connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS musicnet_metadata (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                composer TEXT,
                composition TEXT,
                movement TEXT,
                ensemble TEXT,
                source TEXT,
                transcriber TEXT,
                catalog_name TEXT,
                seconds INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def get_input_data(self):
        return {
            "composer": self.ui.lineComposer.text().strip(),
            "composition": self.ui.lineComposition.text().strip(),
            "movement": self.ui.lineMovement.text().strip(),
            "ensemble": self.ui.lineEnsemble.text().strip(),
            "source": self.ui.lineSource.text().strip(),
            "transcriber": self.ui.lineTranscriber.text().strip(),
            "catalog": self.ui.lineCatalog.text().strip(),
            "seconds": self.ui.lineSeconds.text().strip()
        }

    def add_record(self):
        data = self.get_input_data()
        if not data["composer"] or not data["composition"]:
            QMessageBox.warning(self, "შეცდომა", "Composer და Composition აუცილებელია!")
            return
        try:
            conn = self.db_connect()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO musicnet_metadata 
                (composer, composition, movement, ensemble, source, transcriber, catalog_name, seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["composer"], data["composition"], data["movement"], data["ensemble"],
                data["source"], data["transcriber"], data["catalog"],
                int(data["seconds"]) if data["seconds"] else None
            ))
            conn.commit()
            QMessageBox.information(self, "✓", "ჩანაწერი დაემატა.")
        except Exception as e:
            QMessageBox.critical(self, "შეცდომა", str(e))
        finally:
            conn.close()

    def search_record(self):
        composer = self.ui.lineComposer.text().strip()
        if not composer:
            QMessageBox.warning(self, "შეცდომა", "შეიყვანე Composer.")
            return
        try:
            conn = self.db_connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM musicnet_metadata WHERE LOWER(composer) = LOWER(?)", (composer,))

            results = cursor.fetchall()
            if results:
                self.ui.tableMusic.setRowCount(0)

                for row_number, row_data in enumerate(results):
                    self.ui.tableMusic.insertRow(row_number)
                    for column_number, data in enumerate(row_data):
                        item = QTableWidgetItem(str(data) if data is not None else "")
                        self.ui.tableMusic.setItem(row_number, column_number, item)
            else:
                QMessageBox.information(self, "შედეგი", "ვერ მოიძებნა.")
                self.ui.tableMusic.setRowCount(0)
        except Exception as e:
            QMessageBox.critical(self, "შეცდომა", str(e))
        finally:
            conn.close()

    def update_record(self):
        composer = self.ui.lineComposer.text().strip()
        data = self.get_input_data()
        if not composer:
            QMessageBox.warning(self, "შეცდომა", "შეიყვანე Composer.")
            return
        try:
            conn = self.db_connect()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE musicnet_metadata SET
                    composition = ?, movement = ?, ensemble = ?, source = ?,
                    transcriber = ?, catalog_name = ?, seconds = ?
                WHERE composer = ?
            """, (
                data["composition"], data["movement"], data["ensemble"],
                data["source"], data["transcriber"], data["catalog"],
                int(data["seconds"]) if data["seconds"] else None, composer
            ))
            conn.commit()
            if cursor.rowcount:
                QMessageBox.information(self, "✓", "განახლდა.")
            else:
                QMessageBox.warning(self, "შედეგი", "არ მოიძებნა.")
        except Exception as e:
            QMessageBox.critical(self, "შეცდომა", str(e))
        finally:
            conn.close()

    def delete_record(self):
        composer = self.ui.lineComposer.text().strip()
        if not composer:
            QMessageBox.warning(self, "შეცდომა", "შეიყვანე Composer.")
            return
        try:
            conn = self.db_connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM musicnet_metadata WHERE composer = ?", (composer,))
            conn.commit()
            if cursor.rowcount:
                QMessageBox.information(self, "✓", "წაიშალა.")
            else:
                QMessageBox.warning(self, "შედეგი", "არ მოიძებნა.")
        except Exception as e:
            QMessageBox.critical(self, "შეცდომა", str(e))
        finally:
            conn.close()

    def show_chart(self):
        try:
            conn = self.db_connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT composer, COUNT(*) FROM musicnet_metadata
                GROUP BY composer ORDER BY COUNT(*) DESC LIMIT 5
            """)
            data = cursor.fetchall()
            conn.close()

            if not data:
                QMessageBox.information(self, "შედეგი", "ბაზა ცარიელია.")
                return

            series = QPieSeries()
            for composer, count in data:
                series.append(composer, count)

            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("Top 5 კომპოზიტორი ჩანაწერების მიხედვით")

            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)

            chart_dialog = QDialog(self)
            chart_dialog.setWindowTitle("Chart")
            layout = QVBoxLayout()
            layout.addWidget(chart_view)
            chart_dialog.setLayout(layout)
            chart_dialog.resize(500, 400)
            chart_dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "შეცდომა", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MusicApp()
    window.show()
    sys.exit(app.exec_())