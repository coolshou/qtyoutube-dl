#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 20:55:27 2019

@author: coolshou
"""
import sys
try:
    #from PyQt5.QtGui import (QGuiApplication)
    from PyQt5.QtWidgets import ( QMessageBox,
                                 QFileDialog, QHeaderView, QDialog,
                                 QWidget, QLabel, QPushButton, QHBoxLayout,
                                 QVBoxLayout)
    from PyQt5.QtCore import (QStandardPaths, QRect, pyqtSlot, 
                              QModelIndex, QSize, QPoint)
    from PyQt5.QtGui import (QIcon)
#    from PyQt5.uic import loadUi
except ImportError as error:
    print("pip install PyQt5 (%s)" % error)
    sys.exit(1)
    
class ButtonsChoiceDialog(QDialog):

#    if os.name == "nt":
#        STYLE = wx.DEFAULT_DIALOG_STYLE
#    else:
#        STYLE = wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX

    BORDER = 10

    def __init__(self, parent, choices, message, *args, **kwargs):
        super(ButtonsChoiceDialog, self).__init__(parent, *args,  **kwargs)

        buttons = []

        # Create components
        #panel = wx.Panel(self)
        panel = QWidget(self)
        
        #info_bmp = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_MESSAGE_BOX)

        #info_icon = wx.StaticBitmap(panel, wx.ID_ANY, info_bmp)
        info_icon = QIcon(":/info")
        #msg_text = wx.StaticText(panel, wx.ID_ANY, message)
        msg_text = QLabel(message)
        #buttons.append(wx.Button(panel, wx.ID_CANCEL, _("Cancel")))
        buttons.append(QPushButton("Cancel"))
        for index, label in enumerate(choices):
            #buttons.append(wx.Button(panel, index + 1, label))
            buttons.append(QPushButton(label))

        # Get the maximum button width & height
        max_width = max_height = -1

        for button in buttons:
            #button_width, button_height = button.GetSize()
            button_width, button_height = button.size()

            if button_width > max_width:
                max_width = button_width

            if button_height > max_height:
                max_height = button_height

        max_width += 10

        # Set buttons width & bind events
        for button in buttons:
            if button != buttons[0]:
                button.SetMinSize((max_width, max_height))
            else:
                # On Close button change only the height
                button.SetMinSize((-1, max_height))

            #button.Bind(wx.EVT_BUTTON, self._on_close)
            button.clicked.connect(self._on_close)

        # Set sizers
        #vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        vertical_sizer = QVBoxLayout()
        #message_sizer = wx.BoxSizer(wx.HORIZONTAL)
        message_sizer = QHBoxLayout()
        
        message_sizer.Add(info_icon)
        message_sizer.AddSpacer((10, 10))
        #message_sizer.Add(msg_text, flag=wx.EXPAND)
        message_sizer.Add(msg_text)

        #vertical_sizer.Add(message_sizer, 1, wx.ALL, border=self.BORDER)
        vertical_sizer.addWidget(message_sizer)
        
        #buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer = QHBoxLayout()
        for button in buttons[1:]:
            buttons_sizer.addWidget(button)
            #buttons_sizer.AddSpacer((5, -1))

        buttons_sizer.AddSpacer((-1, -1), 1)
        #buttons_sizer.Add(buttons[0], flag=wx.ALIGN_RIGHT)
        buttons_sizer.addWidget(buttons[0])
        #vertical_sizer.Add(buttons_sizer, flag=wx.EXPAND | wx.ALL, border=self.BORDER)
        vertical_sizer.addWidget(buttons_sizer)

        #panel.SetSizer(vertical_sizer)
        panel.setLayout(vertical_sizer)

        #width, height = panel.GetBestSize()
        width, height = panel.size()
        self.SetSize((width, height * 1.3))

        #self.Center()

    def _on_close(self, event):
        self.EndModal(event.GetEventObject().GetId())
