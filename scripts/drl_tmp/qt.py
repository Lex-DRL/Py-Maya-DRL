# coding: utf-8
__author__ = 'DRL'

from PySide.QtGui import *

class drl_widget(QWidget):
  def __init__(self):
    super(drl_widget, self).__init__()
    self.setWindowTitle(u'АЗАЗА!')
    l = QVBoxLayout()
    self.setLayout(l)

    self.drl_lbl = QLabel(u'Вот такой вот лэйбл!')
    l.addWidget(self.drl_lbl)

    btn = QPushButton(u'Лады!')
    l.addWidget(btn)
    btn.clicked.connect(self.action)

    ln = QLineEdit()
    l.addWidget(ln)
    ln.textChanged.connect(self.textChange)


  def action(self):
    print 'action'

  def textChange(self, text):
    self.drl_lbl.setText(u'Текст: %s' % text)


app = QApplication([])
w = drl_widget()
w.show()
app.exec_()