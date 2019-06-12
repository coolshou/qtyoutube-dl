#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  1 22:31:53 2019

@author: coolshou
"""
import sys
import os
from gettext import gettext as _
try:
    #from PyQt5.QtGui import (QGuiApplication)
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                                 QFileDialog, QHeaderView, QPushButton)
    from PyQt5.QtCore import (QStandardPaths, pyqtSlot, 
                              QModelIndex, QSize, QPoint, QItemSelection,
                              QTimer)
    from PyQt5.QtGui import (QIcon, QStandardItemModel, QStandardItem)
    from PyQt5.uic import loadUi
except ImportError as error:
    print("pip install PyQt5 (%s)" % error)
    sys.exit(1)

from parsers import OptionsParser
from optionsmanager import OptionsManager as opt_manager
from logmanager import LogManager
from downloadmanager import (
    DownloadManager,
    DownloadList,
    DownloadItem
)
from updatemanager import (
    UpdateThread
)
from info import (
    __descriptionfull__,
    __licensefull__,
    __projecturl__,
    __appname__,
    __author__
)
from version import __version__

from dialog import ButtonsChoiceDialog

import images


        
class ListCtrl(QStandardItemModel):
    def __init__(self, columns, *args, **kwargs):
        super(ListCtrl, self).__init__(*args, **kwargs)
        self.columns = columns
        self._list_index = 0
        self._url_list = set()
        self._set_columns()

    def Clear(self):
        """Clear the ListCtrl widget & reset self._list_index and
        self._url_list. """
        #self.DeleteAllItems()
        print("Clear")
        #self.clear()
        self.removeRows(0, self._list_index)
        #self.setRowCount(0) #header
        self._list_index = 0
        self._url_list = set()
        
    def bind_item(self, download_item):
        #self.InsertStringItem(self._list_index, download_item.url)
        #self.SetItemData(self._list_index, download_item.object_id)

        itm = QStandardItem(download_item.url)
        itm.setData(download_item.object_id)

        self._update_from_item(self._list_index, download_item)
        
        self.setItem(self._list_index, itm)
        
        self._list_index += 1
        
    def _update_from_item(self, row, download_item):
        progress_stats = download_item.progress_stats

        for key in self.columns:
            column = self.columns[key][0]
            itm = self.item(row, column)
            if not itm:
                itm = QStandardItem("")
            if key == "status" and progress_stats["playlist_index"]:
                # Not the best place but we build the playlist status here
                status = "{0} {1}/{2}".format(progress_stats["status"],
                                              progress_stats["playlist_index"],
                                              progress_stats["playlist_size"])

                t = status
            else:
                t = progress_stats[key]
            itm.setText(t)
            #print("text: %s" %itm.text())
            self.setItem(row, column, itm)
            
    def has_url(self, url):
        """Returns True if the url is aleady in the ListCtrl else False.

        Args:
            url (string): URL string.

        """
        return url in self._url_list
        
    def _set_columns(self):
        """Initializes ListCtrl columns.
        See MainFrame STATUSLIST_COLUMNS attribute for more info. """
        #headerList = []
        for column_item in sorted(self.columns.values()):
            #header
            idx = column_item[0]
            item = QStandardItem(column_item[1])

            #headerList.append(column_item[1]) # text
            self.setHorizontalHeaderItem(idx, item)
            '''
            self.InsertColumn(column_item[0], column_item[1], width=wx.LIST_AUTOSIZE_USEHEADER)

            # If the column width obtained from wxLIST_AUTOSIZE_USEHEADER
            # is smaller than the minimum allowed column width
            # then set the column width to the minumum allowed size
            if self.GetColumnWidth(column_item[0]) < column_item[2]:
                self.SetColumnWidth(column_item[0], column_item[2])

            # Set auto-resize if enabled
            if column_item[3]:
                self.setResizeColumn(column_item[0])
            '''
        #self.setHorizontalHeaderLabels(headerList)
    def get_next_selected(self, start=-1, reverse=False):
        if start == -1:
            start = self._list_index - 1 if reverse else 0
        else:
            # start from next item
            if reverse:
                start -= 1
            else:
                start += 1

        end = -1 if reverse else self._list_index
        step = -1 if reverse else 1

        for index in range(start, end, step):
            if self.IsSelected(index):
                return index

        return -1

    def is_empty(self):
        """Returns True if the list is empty else False. """
        return self._list_index == 0
        
class MainWindow(QMainWindow):
    #LABEL
    ADD_LABEL = _("Add")
    DOWNLOAD_LIST_LABEL = _("Download list")
    DELETE_LABEL = _("Delete")
    DELETEALL_LABEL = _("Clear")
    #PLAY_LABEL = _("Play")
    UP_LABEL = _("Up")
    DOWN_LABEL = _("Down")
    #RELOAD_LABEL = _("Reload")
    #PAUSE_LABEL = _("Pause")
    START_LABEL = _("Start")
    STOP_LABEL = _("Stop")
    INFO_LABEL = _("Info")
    ABOUT_LABEL = _("About")
    
    QUESTION_LABEL = _("Question")
    WARNING_LABEL = _("Warning")
    
    PROVIDE_URL_MSG = _("You need to provide at least one URL")
    QUIT_MSG = _("Are You sure to quit?")
    
    
    VIDEO_LABEL = _("Filename")
    EXTENSION_LABEL = _("Extension")
    SIZE_LABEL = _("Size")
    PERCENT_LABEL = _("Percent")
    ETA_LABEL = _("ETA")
    SPEED_LABEL = _("Speed")
    STATUS_LABEL = _("Status")
    
    URL_REPORT_MSG = _("Total Progress: {0:.1f}% | Queued ({1}) Paused ({2}) Active ({3}) Completed ({4}) Error ({5})")
    CLOSING_MSG = _("Stopping downloads")
    DOWNLOAD_STARTED = _("Downloads started")

    UPDATING_MSG = _("Downloading latest youtube-dl. Please wait...")
    UPDATE_ERR_MSG = _("Youtube-dl download failed [{0}]")
    UPDATE_SUCC_MSG = _("Successfully downloaded youtube-dl")
    
    #################################
    # STATUSLIST_COLUMNS
    #
    # Dictionary which contains the columns for the wxListCtrl widget.
    # Each key represents a column and holds informations about itself.
    # Structure informations:
    #  column_key: (column_number, column_label, minimum_width, is_resizable)
    #
    STATUSLIST_COLUMNS = {
        'filename': (0, VIDEO_LABEL, 150, True),
        'extension': (1, EXTENSION_LABEL, 60, False),
        'filesize': (2, SIZE_LABEL, 80, False),
        'percent': (3, PERCENT_LABEL, 65, False),
        'eta': (4, ETA_LABEL, 45, False),
        'speed': (5, SPEED_LABEL, 90, False),
        'status': (6, STATUS_LABEL, 160, False)
    }
    
    def __init__(self):
        super(MainWindow, self).__init__()
        if getattr(sys, 'frozen', False):
            # we are running in a |PyInstaller| bundle
            basedir = sys._MEIPASS
        else:
            basedir = os.path.dirname(__file__)

        loadUi(os.path.join(basedir, "qtyoutube-dl.ui"), self)
        self.setWindowIcon(QIcon(":qtyoutube-dl"))
        #load setting
        #self.cfg = QSettings("coolshou.idv", "qtyoutube-dl")
        #self._savepath = ""
        
        #self.loadSettings()

            
        ###################################
        cfgpath = os.path.join(QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation), "qtyoutube-dl")
        if not os.path.exists(cfgpath):
            os.mkdir(cfgpath)
        self.opt_manager = opt_manager(cfgpath)
        self.log_manager = LogManager(cfgpath, self.opt_manager.options['log_time'])
        self.download_manager = None
        self.update_thread = None
        self.app_icon = None  #REFACTOR Get and set on __init__.py

        self._download_list = DownloadList()
        
        self._status_list = ListCtrl(self.STATUSLIST_COLUMNS)
        self._status_list.rowsInserted.connect(self._update_btns)
        #self._status_list.selectionChanged.connect(self._on_selectionChanged)
        self.tv_status.setModel(self._status_list)
        self.tv_status.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tv_status.clicked.connect(self._on_clicked)
        #self._status_selection = self.tv_status.selectionModel();
        #self._status_selection.selectionChanged.connect(self._on_selectionChanged)
        #self.tv_status.activated.connect(self._on_activated)
        # Set up youtube-dl options parser
        self._options_parser = OptionsParser()
        # Set the Timer
        self._app_timer = QTimer(self)
        self._app_timer.timeout.connect(self._on_timer)
        #upadte ui
        self.setSettings()
        #self._url_list = []
        ############################################
        #button
        #self.le_savepath.textChanged.connect(self.updateSavePath)
        self.path_combobox.currentTextChanged.connect(self.updateSavePath)
        ###################################
        # set bitmap
        bitmap_data = (
           ("add", ":/add"),
           ("down", ":/down"),
           ("up", ":/up"),
           ("copy", ":/copy"),
           ("delete", ":/delete"),
           ("start", ":/get"),
           ("stop", ":/stop"),
           ("pause", ":/pause"),
           ("resume", ":/resume"),
           ("qtyoutube-dl", ":/qtyoutube-dl"),
           ("setting", ":/setting"),
           ("trash", ":/trash"),
           ("info", ":/info")
        )
#           ("pause", ":/pause"),
#           ("resume", ":/resume")
        
        self._bitmaps = {}

        for item in bitmap_data:
            target, name = item
            #self._bitmaps[target] = wx.Bitmap(os.path.join(self._pixmaps_path, name))
            self._bitmaps[target] = QIcon(name)
        
        # Dictionary to store all the buttons
        # Set the data for all the wx.Button items
        # name, label, size, event_handler
        buttons_data = (
            ("delete", self.DELETE_LABEL, (-1, -1), self._on_delete, self.pb_del),
            ("clear", self.DELETEALL_LABEL, (-1, -1), self._on_delAll, self.pb_delAll),
            ("up", self.UP_LABEL, (-1, -1), self._on_arrow_up, self.pb_up),
            ("down", self.DOWN_LABEL, (-1, -1), self._on_arrow_down, self.pb_down),
            ("start", self.START_LABEL, (-1, -1), self._on_start, self.pb_Start),
            ("savepath", "...", (35, -1), self._on_savepath, self.pb_savepath),
            ("add", self.ADD_LABEL, (-1, -1), self._on_add, self.pb_add)
        )
            #("play", self.PLAY_LABEL, (-1, -1), self._on_play, QPushButton),        
            #("reload", self.RELOAD_LABEL, (-1, -1), self._on_reload, QPushButton),
            #("pause", self.PAUSE_LABEL, (-1, -1), self._on_pause, QPushButton),

        self._buttons = {}
        for item in buttons_data:
            name, label, size, evt_handler, parent = item

            #button = parent(self._panel, size=size)
            button = parent
            if parent == QPushButton:
                button.setText(label)
#            elif parent == wx.BitmapButton:
#                button.setToolTip(wx.ToolTip(label))

#            if name in self._bitmaps:
#                #button.SetBitmap(self._bitmaps[name], wx.TOP)
#                button.SetBitmap(self._bitmaps[name], wx.TOP)

            if evt_handler is not None:
                #button.Bind(wx.EVT_BUTTON, evt_handler)
                button.clicked.connect(evt_handler)

            self._buttons[name] = button
        
        self._path_combobox = self.path_combobox
          
        #test data
        #self.te_urls.append("https://www.youtube.com/watch?v=a9V0nl_ezLw")
        
        self._initAction()
        self.show()

    @pyqtSlot(QModelIndex, int, int)
    def _update_btns(self, idx, first, last):
        #print("%s : %s , %s" %(idx, first, last))
        iSum = self._status_list.rowCount()
        if iSum >= 1:
            #print("iSum:%s" % iSum)
            self.pb_Start.setEnabled(True)
        else:
            self.pb_Start.setEnabled(False)
            
    def _update_pause_button(self, event):
        selected_rows = self._status_list.get_all_selected()

        label = _("Pause")
        bitmap = self._bitmaps["pause"]

        for row in selected_rows:
            object_id = self._status_list.GetItemData(row)
            download_item = self._download_list.get_item(object_id)

            if download_item.stage == "Paused":
                # If we find one or more items in Paused
                # state set the button functionality to resume
                label = _("Resume")
                bitmap = self._bitmaps["resume"]
                break

        self._buttons["pause"].setText(label)
        self._buttons["pause"].setToolTip(label)
        self._buttons["pause"].setIcon(bitmap)
        
    def _initAction(self):
        #Action menu
        #view-log
        #option-setting
        self.actionupdate.triggered.connect(self._on_update)
        self.actionAbout.triggered.connect(self._on_about)
        pass


          
    def _get_urls(self):
        """Returns urls list. """
        return [line for line in self.te_urls.toPlainText().split('\n') if line]

    def _create_popup(self, icon, text, title, style):
        msg = QMessageBox(icon, title, text, style)
        msg.setWindowIcon(QIcon(":qtyoutube-dl"))
        return msg.exec()
        
    def _on_add(self):
        urls = self._get_urls()

        if not urls:
            self._create_popup(QMessageBox.Warning,
                               self.PROVIDE_URL_MSG,
                               self.WARNING_LABEL,
                               QMessageBox.Ok)
        else:
            #self._url_list.Clear()
            options = self._options_parser.parse(self.opt_manager.options)

            for url in urls:
                #make sure it is http or https
                if "http://" in url or "https://" in url:
                    download_item = DownloadItem(url, options)
                    download_item.path = self.opt_manager.options["save_path"]

                    if not self._download_list.has_item(download_item.object_id):
                        self._status_list.bind_item(download_item)
                        self._download_list.insert(download_item)
                    
                    #clear line

    def _on_arrow_up(self, event):
        index = self._status_list.get_next_selected()

        if index != -1:
            while index >= 0:
                object_id = self._status_list.GetItemData(index)
                download_item = self._download_list.get_item(object_id)

                new_index = index - 1
                if new_index < 0:
                    new_index = 0

                if not self._status_list.IsSelected(new_index):
                    self._download_list.move_up(object_id)
                    self._status_list.move_item_up(index)
                    self._status_list._update_from_item(new_index, download_item)

                index = self._status_list.get_next_selected(index)

    def _on_arrow_down(self, event):
        index = self._status_list.get_next_selected(reverse=True)

        if index != -1:
            while index >= 0:
                object_id = self._status_list.GetItemData(index)
                download_item = self._download_list.get_item(object_id)

                new_index = index + 1
                if new_index >= self._status_list.GetItemCount():
                    new_index = self._status_list.GetItemCount() - 1

                if not self._status_list.IsSelected(new_index):
                    self._download_list.move_down(object_id)
                    self._status_list.move_item_down(index)
                    self._status_list._update_from_item(new_index, download_item)

                index = self._status_list.get_next_selected(index, True)
                
    def _on_delAll(self):
        self._status_list.Clear()
        self._download_list.clear()
    
    def _on_delete(self):
        #get select idx
        index = self._status_list.get_next_selected()

        if index == -1:
            dlg = ButtonsChoiceDialog(self, [_("Remove all"), _("Remove completed")], _("No items selected. Please pick an action"), _("Delete"))
            ret_code = dlg.ShowModal()
            dlg.Destroy()

            #REFACTOR Maybe add this functionality directly to DownloadList?
            if ret_code == 1:
                for ditem in self._download_list.get_items():
                    if ditem.stage != "Active":
                        self._status_list.remove_row(self._download_list.index(ditem.object_id))
                        self._download_list.remove(ditem.object_id)

            if ret_code == 2:
                for ditem in self._download_list.get_items():
                    if ditem.stage == "Completed":
                        self._status_list.remove_row(self._download_list.index(ditem.object_id))
                        self._download_list.remove(ditem.object_id)
        else:
            if self.opt_manager.options["confirm_deletion"]:
                self._create_popup(QMessageBox.Question,
                                   _("Are you sure you want to remove selected items?"),
                                   _("Delete"),
                                   QMessageBox.Yes | QMessageBox.No)
                #dlg = wx.MessageDialog(self, _("Are you sure you want to remove selected items?"), _("Delete"), wx.YES_NO | wx.ICON_QUESTION)
                #result = dlg.ShowModal() == wx.ID_YES
                result = dlg.ShowModal() == QMessageBox.Yes
                dlg.Destroy()
            else:
                result = True

            if result:
                while index >= 0:
                    object_id = self._status_list.GetItemData(index)
                    selected_download_item = self._download_list.get_item(object_id)

                    if selected_download_item.stage == "Active":
                        #self._create_popup(_("Item is active, cannot remove"), self.WARNING_LABEL, wx.OK | wx.ICON_EXCLAMATION)
                        self._create_popup(QMessageBox.Information,
                                           _("Item is active, cannot remove"), 
                                           self.WARNING_LABEL, 
                                           QMessageBox.OK)
                    else:
                        #if selected_download_item.stage == "Completed":
                            #dlg = wx.MessageDialog(self, "Do you want to remove the files associated with this item?", "Remove files", wx.YES_NO | wx.ICON_QUESTION)

                            #result = dlg.ShowModal() == wx.ID_YES
                            #dlg.Destroy()

                            #if result:
                                #for cur_file in selected_download_item.get_files():
                                    #remove_file(cur_file)

                        self._status_list.remove_row(index)
                        self._download_list.remove(object_id)
                        index -= 1

                    index = self._status_list.get_next_selected(index)

        #self._update_pause_button(None)
    
    @pyqtSlot(QModelIndex)    
    def _on_clicked(self, mIdx):
        print("select: %s, %s" % (mIdx, mIdx.row()))
        if mIdx.row() >=0:
            self.pb_del.setEnabled(True)
            
        else:
            self.pb_del.setEnabled(False)
            self.pb_up.setEnabled(False)
            self.pb_down.setEnabled(False)
            
    @pyqtSlot(QModelIndex)
    def _on_activated(self, mIdx):
        print("select: %s" % mIdx)
    
    @pyqtSlot(QItemSelection, QItemSelection)    
    def _on_selectionChanged(self, selected, deselected):
        print("selected: %s" % selected)
    
    def _on_savepath(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select save Directory"))
        if folder:
            #self._savepath = folder
            self.le_savepath.setText(folder)
            
    def _on_start(self, event):
        if self.download_manager is None:
            if self.update_thread is not None and self.update_thread.is_alive():
                self._create_popup(QMessageBox.Information,
                                   _("Update in progress. Please wait for the update to complete"),
                                   self.WARNING_LABEL,
                                   QMessageBox.OK)
            else:
                self._start_download()
        else:
            self.download_manager.stop_downloads()

    def _start_download(self):
        if self._status_list.is_empty():
            self._create_popup(_("No items to download"),
                               self.WARNING_LABEL,
                               QMessageBox.OK)
        else:
            self._app_timer.start(100)
            self.download_manager = DownloadManager(self, self._download_list, self.opt_manager, self.log_manager)
            self.download_manager.sig_callafter.connect(self._download_manager_handler)
            self.download_manager.sig_worker_callafter.connect(self._download_worker_handler)
            self._status_bar_write(self.DOWNLOAD_STARTED)
            self._buttons["start"].setText(self.STOP_LABEL)
            self._buttons["start"].setToolTip(self.STOP_LABEL)
            self._buttons["start"].setIcon(self._bitmaps["stop"])

    def _on_timer(self):
        total_percentage = 0.0
        queued = paused = active = completed = error = 0

        for item in self._download_list.get_items():
            if item.stage == "Queued":
                queued += 1
            if item.stage == "Paused":
                paused += 1
            if item.stage == "Active":
                active += 1
                total_percentage += float(item.progress_stats["percent"].split('%')[0])
            if item.stage == "Completed":
                completed += 1
            if item.stage == "Error":
                error += 1

        # REFACTOR Store percentage as float in the DownloadItem?
        # REFACTOR DownloadList keep track for each item stage?

        items_count = active + completed + error + queued
        total_percentage += completed * 100.0 + error * 100.0

        if items_count:
            total_percentage /= items_count

        msg = self.URL_REPORT_MSG.format(total_percentage, queued, paused, active, completed, error)

        if self.update_thread is None:
            # Don't overwrite the update messages
            self._status_bar_write(msg)

    def _status_bar_write(self, msg):
        """Display msg in the status bar. """
        self.statusbar.showMessage(msg)
        
    def _download_manager_worker_handler(self, signal, data):
        print("dl_work: %s: %s" % (signal, data))
        print("_download_list: %s" % self._download_list.get_items())

    def _download_worker_handler(self, data):
        """downloadmanager.Worker thread handler.

        Handles messages from the Worker thread.

        Args:
            See downloadmanager.Worker _talk_to_gui() method.

        """
        #signal, data = msg.data
        #signal = sig

        download_item = self._download_list.get_item(data["index"])
        download_item.update_stats(data)
        row = self._download_list.index(data["index"])

        self._status_list._update_from_item(row, download_item)
        
    def _download_manager_handler(self, data):
        """downloadmanager.DownloadManager thread handler.

        Handles messages from the DownloadManager thread.

        Args:
            See downloadmanager.DownloadManager _talk_to_gui() method.

        """
        #data = msg.data

        if data == 'finished':
            self._print_stats()
            self._reset_widgets()
            self.download_manager = None
            self._app_timer.stop()
            self._after_download()
        elif data == 'closed':
            self._status_bar_write(self.CLOSED_MSG)
            self._reset_widgets()
            self.download_manager = None
            self._app_timer.stop()
        elif data == 'closing':
            self._status_bar_write(self.CLOSING_MSG)
        elif data == 'report_active':
            pass
            #NOTE Remove from here and downloadmanager
            #since now we have the wx.Timer to check progress

    def _on_update(self, event):
        """Event handler of the self._update_btn widget.

        This method is used when the update button is pressed to start
        the update process.

        Note:
            Currently there is not way to stop the update process.

        """
        if self.opt_manager.options["disable_update"]:
            self._create_popup(_("Updates are disabled for your system. Please use the system's package manager to update youtube-dl."),
                               self.INFO_LABEL,
                               QMessageBox.OK)
        else:
            self._update_youtubedl()

    def _update_youtubedl(self):
        """Update youtube-dl binary to the latest version. """
        if self.download_manager is not None and self.download_manager.is_alive():
            self._create_popup(self.DOWNLOAD_ACTIVE,
                               self.WARNING_LABEL,
                               QMessageBox.OK)
        elif self.update_thread is not None and self.update_thread.is_alive():
            self._create_popup(self.UPDATE_ACTIVE,
                               self.INFO_LABEL,
                               QMessageBox.OK)
        else:
            self.update_thread = UpdateThread(self.opt_manager.options['youtubedl_path'])
            self.update_thread.sig_callafter.connect(self._update_handler)

    def _update_handler(self, sig, msg):
        """updatemanager.UpdateThread thread handler.

        Handles messages from the UpdateThread thread.

        Args:
            See updatemanager.UpdateThread _talk_to_gui() method.

        """
        #data = msg.data

        if sig == 'download':
            self._status_bar_write("%s: %s" % (self.UPDATING_MSG, msg))
        elif sig == 'error':
            self._status_bar_write(self.UPDATE_ERR_MSG.format(msg))
        elif sig == 'correct':
            self._status_bar_write(self.UPDATE_SUCC_MSG)
        else:
            self._reset_widgets()
            self.update_thread = None

    def _reset_widgets(self):
        """Resets GUI widgets after update or download process. """
        self._buttons["start"].setText(_("Start"))
        self._buttons["start"].setToolTip(_("Start"))
        self._buttons["start"].setIcon(self._bitmaps["start"])
        
    def _on_about(self, event):
        #msg = "Name: %s\n" % __appname__
        msg = "Version: %s\n" % __version__
        msg += "Web: %s\n" % __projecturl__
        msg += "  %s\n" %__descriptionfull__
        
        QMessageBox.about(self, "about - %s" % __appname__, msg)
        
    def updateSavePath(self, text):
        #TODO: make sure path of "text" exist
        self._savepath = text
        
    def loadSettings(self):
        '''load setting from file'''
        '''
        self.cfg.beginGroup("main")
        #save path, 
        self._savepath = self.cfg.value("savepath", 
                                        QStandardPaths.writableLocation(QStandardPaths.DownloadLocation))
        if not self._savepath:
            self._savepath = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
            
        self._size = self.cfg.value("size", self.size())
        self._pos = self.cfg.value("pos", self.pos())
        
        #TODO: download list, resume?
        self.cfg.endGroup()
        '''
        
    def setSettings(self):
        '''update setting to GUI'''
        self.resize(QSize(self.opt_manager.options["size"][0],
                          self.opt_manager.options["size"][1]))
        self.move(QPoint(self.opt_manager.options["pos"][0],
                         self.opt_manager.options["pos"][0]))
        #self.le_savepath.setText(self.opt_manager.options["save_path"])
        self.path_combobox.addItem(self.opt_manager.options["save_path"])
        
    def saveSettings(self):
        '''save setting to file'''
        self.opt_manager.options["size"] = "(%s,%s)" % (self.width(), self.height())
        #self.opt_manager.options["pos"]
        #print("self.size(): %s" % self.opt_manager.options["size"])
        self.opt_manager.save_to_file()
        '''
        self.cfg.beginGroup("main")
        #save path
        self.cfg.setValue("savepath", self._savepath)
        self.cfg.setValue("size", self.size())
        self.cfg.setValue("pos", self.pos())
        #TODO: download list
        self.cfg.endGroup()
        '''
    
    def closeEvent(self, event):
        #
        self.saveSettings()
        if 0:
            close = self._create_popup(QMessageBox.Question,
                                   self.QUIT_MSG,
                                   self.QUESTION_LABEL,
                                   QMessageBox.Yes | QMessageBox.Cancel)
            
            if close == QMessageBox.Yes:
                
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()




if __name__ == "__main__":
    app = QApplication(sys.argv)

    MainWindow = MainWindow()

    sys.exit(app.exec_())

