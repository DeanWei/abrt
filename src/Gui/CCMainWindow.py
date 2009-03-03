import sys
import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
import CCDBusBackend
import sys
from CC_gui_functions import *
from CCDumpList import getDumpList, DumpList
from CCReporterDialog import ReporterDialog
from CCReport import Report
from exception import installExceptionHandler, handleMyException
try:
    import rpm
except:
    rpm = None

installExceptionHandler("cc-gui", "0.0.1")

class MainWindow():
    def __init__(self):
        self.theme = theme = gtk.icon_theme_get_default()
        try:
            self.ccdaemon = CCDBusBackend.DBusManager()
        except Exception, e:
            # show error message if connection fails
            # FIXME add an option to start the daemon
            gui_error_message(e.message)
            sys.exit()
        #Set the Glade file
        # FIXME add to PATH
        self.gladefile = "/usr/share/abrt/ccgui.glade"  
        self.wTree = gtk.glade.XML(self.gladefile) 
        
        #Get the Main Window, and connect the "destroy" event
        self.window = self.wTree.get_widget("main_window2")
        self.window.set_default_size(700, 480)
        if (self.window):
            self.window.connect("delete_event", self.delete_event_cb)
            self.window.connect("destroy", self.destroy)
        
        self.appBar = self.wTree.get_widget("appBar")
        
        # set colours for descritpion heading
        self.wTree.get_widget("evDescription").modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        
        #init the dumps treeview
        self.dlist = self.wTree.get_widget("tvDumps")
        self.dumpsListStore = gtk.ListStore(gtk.gdk.Pixbuf, str,str,str,str, object)
        # set filter
        self.modelfilter = self.dumpsListStore.filter_new()
        self.modelfilter.set_visible_func(self.filter_dumps, None)
        self.dlist.set_model(self.modelfilter)
        # add pixbuff separatelly
        icon_column = gtk.TreeViewColumn('Icon')
        icon_column.cell = gtk.CellRendererPixbuf()
        n = self.dlist.append_column(icon_column)
        icon_column.pack_start(icon_column.cell, False)
        icon_column.set_attributes(icon_column.cell, pixbuf=(n-1))
        # ===============================================
        columns = [None]*4
        columns[0] = gtk.TreeViewColumn('Package')
        columns[1] = gtk.TreeViewColumn('Application')
        columns[2] = gtk.TreeViewColumn('Date')
        columns[3] = gtk.TreeViewColumn('Crash Rate')
        # create list
        for column in columns:
            n = self.dlist.append_column(column)
            column.cell = gtk.CellRendererText()
            column.pack_start(column.cell, False)
            column.set_attributes(column.cell, text=(n-1))
            column.set_resizable(True)
        #connect signals
        self.dlist.connect("cursor-changed", self.on_tvDumps_cursor_changed)
        self.wTree.get_widget("bDelete").connect("clicked", self.on_bDelete_clicked, self.dlist)
        self.wTree.get_widget("bReport").connect("clicked", self.on_bReport_clicked)
        self.wTree.get_widget("bQuit").connect("clicked", self.on_bQuit_clicked)
        self.ccdaemon.connect("crash", self.on_data_changed_cb, None)
        self.ccdaemon.connect("analyze-complete", self.on_analyze_complete_cb)
        
        # load data
        #self.load()
    def hydrate(self):
        self.dumpsListStore.clear()
        self.rows = self.ccdaemon.getDumps()
        try:
            dumplist = getDumpList(self.ccdaemon, refresh=True)
        except Exception, e:
            gui_error_message("Error while loading the dumplist, please check if crash-catcher daemon is running\n %s" % e.message)
        for entry in dumplist:
            try:
                icon = get_icon_for_package(self.theme,entry.getPackageName())
            except:
                icon = None
            self.dumpsListStore.append([icon, entry.getPackage(),entry.getExecutable(), entry.getTime("%Y.%m.%d %H:%M:%S"),entry.getCount(), entry])
            
    def filter_dumps(self, model, miter, data):
        # for later..
        return True

    def on_tvDumps_cursor_changed(self,treeview):
        dumpsListStore, path = self.dlist.get_selection().get_selected_rows()
        if not path:
            self.wTree.get_widget("lDescription").set_label("")
            return
        # this should work until we keep the row object in the last position
        dump = dumpsListStore.get_value(dumpsListStore.get_iter(path[0]), len(self.dlist.get_columns()))
        
        #move this to Dump class
        lPackage = self.wTree.get_widget("lPackage")
        self.wTree.get_widget("lDescription").set_label(dump.getDescription())
        #print self.rows[row]
    def on_bDelete_clicked(self, button, treeview):
        dumpsListStore, path = self.dlist.get_selection().get_selected_rows()
        if not path:
            return
        # this should work until we keep the row object in the last position
        dump = dumpsListStore.get_value(dumpsListStore.get_iter(path[0]), len(self.dlist.get_columns()))
        try:
            if self.ccdaemon.DeleteDebugDump(dump.UUID):
                self.hydrate()
                treeview.emit("cursor-changed")
            else:
                print "Couldn't delete"
        except Exception, e:
            print e
    
    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        gtk.main_quit()
    
    def on_data_changed_cb(self, *args):
        ret = gui_question_dialog("Another crash detected, do you want to refresh the data?",self.window)
        if ret == gtk.RESPONSE_YES:
            self.hydrate()
        else:
            pass
        #print "got another crash, refresh gui?"
    
    def on_analyze_complete_cb(self, daemon, report):
        dumplist = getDumpList(self.ccdaemon)
        #entry = dumplist.ddict[UUID]
        # tady asi nedostanem UUID, ale vysledek nasi volane metody
        #print report
        #print "GUI: Analyze for package %s crash with UUID %s is complete" % (entry.Package, UUID)
        #print "We should refresh the UI ..."
        if not report:
            gui_error_message("Unable to get report! Debuginfo missing?")
            return
        report_dialog = ReporterDialog(report)
        result = report_dialog.run()
        if result:
            self.ccdaemon.Report(result)
        #ret = gui_question_dialog("GUI: Analyze for package %s crash with UUID %s is complete" % (entry.Package, UUID),self.window)
        #if ret == gtk.RESPONSE_YES:
        #    self.hydrate()
        #else:
        #    pass
        #print "got another crash, refresh gui?"
    
    
    def on_bReport_clicked(self, button):
        # FIXME don't duplicate the code, move to function
        dumpsListStore, path = self.dlist.get_selection().get_selected_rows()
        if not path:
            return
        dump = dumpsListStore.get_value(dumpsListStore.get_iter(path[0]), len(self.dlist.get_columns()))
        # show the report window with selected dump
        try:
            report = self.ccdaemon.getReport(dump.getUUID())
        except Exception, e:
            # FIXME #3	dbus.exceptions.DBusException: org.freedesktop.DBus.Error.NoReply: Did not receive a reply
            # do this async and wait for yum to end with debuginfoinstal
            gui_error_message("Error getting the report: %s" % e.message)
            return
        return
        if not report:
            gui_error_message("Unable to get report! Debuginfo missing?")
            return
        report_dialog = ReporterDialog(report)
        result = report_dialog.run()
        if result:
            self.ccdaemon.Report(result)


    def delete_event_cb(self, widget, event, data=None):
        # Change FALSE to TRUE and the main window will not be destroyed
        # with a "delete_event".
        return self.on_bQuit_clicked(widget)
        
    def on_bQuit_clicked(self, widget):
        ret = gui_question_dialog("Do you really want to quit?",self.window)
        if ret == gtk.RESPONSE_YES:
            gtk.main_quit()
        return True
            
    def show(self):
        self.window.show()
    

if __name__ == "__main__":
    cc = MainWindow()
    cc.hydrate()
    cc.show()
    gtk.main()

