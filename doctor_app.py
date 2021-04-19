import sys
import os
from PyQt5.QtWidgets import *
import csv
import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re


class MainWidgets(QTableWidget):
    def __init__(self, r, c):
        super().__init__(r, c)
        self.pattern = '</strong></td><td>.*</td><td style'
        self.url_template = 'https://www.hipaaspace.com/medical_billing/coding/national_provider_identifier/codes/npi_{}.txt'
        self.path = ''

    def open_sheet(self):

        self.path = QFileDialog.getOpenFileName(self, os.getenv('HOME'), "", 'CSV(*.csv)')
        if self.path[0] != "":
            with open(self.path[0], newline="") as csv_file:
                self.setRowCount(0)
                self.setColumnCount(10)
                my_file = csv.reader(csv_file, dialect='excel')
                for row_data in my_file:
                    rows = self.rowCount()
                    self.insertRow(rows)
                    if len(row_data) > 10:
                        self.setColumnCount(len(row_data))
                    for column, stuff in enumerate(row_data):
                        item = QTableWidgetItem(stuff)
                        self.setItem(rows, column, item)
        else:
            pass

    def npi_specialities(self):
        column, prompt = QInputDialog.getText(self, 'Input Dialog',
                                              'Enter your NPI column(please use number):')
        if self.path != "":
            try:
                df = pd.read_csv(self.path[0])
                df = df.loc[df.iloc[:, int(column) - 1].notnull(), :]
                value = df.iloc[:, int(column) - 1].apply(lambda x: int(x))
                # value = pd.to_numeric(df.iloc[:, int(self.column) - 1])
                npi_dict = {}
                for npi in value:
                    url = self.url_template.format(npi)
                    try:
                        response = BeautifulSoup(urlopen(url), features='lxml')
                        table = str(response.find_all('table', class_='mappingresult')[0])
                        res = re.findall(self.pattern, table)
                        specialties = set(
                            [items[str(items).find('</strong></td><td>') + 18:str(items).find('</td><td style')] for
                             items
                             in
                             res])
                        npi_dict.update({npi: specialties})
                    except:
                        npi_dict.update({npi: {''}})
                        continue
                print(npi_dict)
                self.data = npi_dict
                self.populate_data_to_excel()
                return npi_dict
            except:
                if column == "":
                    pass
                else:
                    msg = QMessageBox()
                    msg.setWindowTitle("Error")
                    msg.setText("Plese make sure only numbers are in the NPI column")
                    msg.exec_()
        else:
            pass

    def populate_data_to_excel(self):
        df = pd.DataFrame(data=self.data,
                          columns=['NPI', 'Specialty 0', 'Specialty 1', 'Specialty 2', 'Specialty 3', 'Specialty 4',
                                   'Specialty 5'])
        df_npi = pd.DataFrame(self.data.keys()).rename(columns={0: 'NPI'})
        df['NPI'] = df_npi['NPI']

        df_specialty = pd.DataFrame(self.data.values())
        try:
            df['Specialty 0'] = df_specialty[0]
            df['Specialty 1'] = df_specialty[1]
            df['Specialty 2'] = df_specialty[2]
            df['Specialty 3'] = df_specialty[3]
            df['Specialty 4'] = df_specialty[4]
            df['Specialty 5'] = df_specialty[5]
        except:
            pass
        df['Specialty 0'] = df['Specialty 0'].apply(lambda x: str(x).replace('amp;', ''))
        df.to_csv(os.path.join(os.environ["HOMEPATH"], "Desktop\\Specialties for NPI.csv"), encoding='utf-8',
                  index=False)
        msg = QMessageBox()
        msg.setWindowTitle("Information")
        msg.setText("Done! File has been generated on your desktop :)")
        msg.exec_()


class Window(QMainWindow):

    def __init__(self):
        super().__init__()

        self.form_widget = MainWidgets(50, 50)
        self.setCentralWidget(self.form_widget)
        openMenu = QAction('Open File', self)
        openMenu.setShortcut("Ctrl+o")
        openMenu.triggered.connect(self.form_widget.open_sheet)

        search = QAction('Search NPI', self)
        search.triggered.connect(self.form_widget.npi_specialities)

        self.statusBar()
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu("&File")
        fileMenu.addAction(openMenu)
        fileMenu.addAction(search)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Window()
    w.setGeometry(200, 100, 1200, 800)
    w.setWindowTitle('NPI Search')
    w.show()
    sys.exit(app.exec_())
