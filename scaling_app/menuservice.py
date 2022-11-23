import json
import wx
import sys
import tkinter.filedialog

from wx import grid

from scaling_app import constants, api, tableservice
import gettext

_ = gettext.gettext


def connection_error_dialog(address=None):
    if address:
        errortext = _("Connection to API (" + address + ") could not be established")
    else:
        errortext = _("API could not be reached")
    dialog = wx.MessageDialog(None, errortext, _('Connection Error'), wx.ICON_WARNING | wx.OK)
    dialog.ShowModal()
    dialog.Destroy()


class MenuService:

    def __init__(self, frame, datastorage, tableservice, graphservice, statservice):
        self.frame = frame
        self.datastorage = datastorage
        self.tableservice = tableservice
        self.graphservice = graphservice
        self.statservice = statservice

        self.api_address = "http://127.0.0.1:8080"

    def csv_tab_changed(self, evt=None):
        self.tableservice.get_save_to_storage()()
        self.frame.menupanel.page_changed(self.frame.csvtabs.GetSelection())
        evt.Skip()

    def show_row_menu(self, evt):

        menu = wx.Menu()
        row_label = self.tableservice.current_grid.GetRowLabelValue(evt.GetRow())
        col = None
        if self.frame.csvtabs.GetSelection() > 0:
            selected_scaling = self.datastorage.tabs[self.frame.csvtabs.GetSelection()].GetCornerLabelValue()
            col = self.datastorage.table.col_labels.index(selected_scaling)

        if not self.tableservice.value_in_data(row_label, col):
            delrow = menu.Append(wx.ID_ANY, _("Delete Object"))
            self.frame.Bind(wx.EVT_MENU, self.tableservice.get_delete_row(evt.GetRow()), delrow)
        purgerow = menu.Append(wx.ID_ANY, _("Purge Object"))
        self.frame.Bind(wx.EVT_MENU, self.tableservice.get_purge_row(evt), purgerow)
        floodrow = menu.Append(wx.ID_ANY, _("Fill Object"))
        self.frame.Bind(wx.EVT_MENU, self.tableservice.get_flood_row(evt), floodrow)
        if not self.tableservice.value_in_data(row_label, col):
            edit = menu.Append(wx.ID_ANY, _("Edit Label"))
            self.frame.Bind(wx.EVT_MENU, self.tableservice.get_edit_row_label(evt), edit)
        new = menu.Append(wx.ID_ANY, _("Add Object"))
        self.frame.Bind(wx.EVT_MENU, self.tableservice.get_add_row(evt), new)

        self.frame.PopupMenu(menu)
        menu.Destroy()

    def show_col_menu(self, evt):

        menu = wx.Menu()
        delcol = menu.Append(wx.ID_ANY, _("Delete Attribute"))
        self.frame.Bind(wx.EVT_MENU, self.tableservice.get_delete_col(evt.GetCol()), delcol)
        purgecol = menu.Append(wx.ID_ANY, _("Purge Attribute"))
        self.frame.Bind(wx.EVT_MENU, self.tableservice.get_purge_col(evt), purgecol)
        if self.frame.csvtabs.GetSelection() > 0:
            floodcol = menu.Append(wx.ID_ANY, _("Fill Attribute"))
            self.frame.Bind(wx.EVT_MENU, self.tableservice.get_flood_col(evt), floodcol)
        edit = menu.Append(wx.ID_ANY, _("Edit Label"))
        self.frame.Bind(wx.EVT_MENU, self.tableservice.get_edit_col_label(evt), edit)
        new = menu.Append(wx.ID_ANY, _("Add Attribute"))
        self.frame.Bind(wx.EVT_MENU, self.tableservice.get_add_col(evt), new)

        attribute = self.frame.main_grid.GetColLabelValue(evt.GetCol())

        if self.frame.csvtabs.GetSelection() == 0:
            if attribute not in self.datastorage.table.scalings and attribute in self.datastorage.table.attribute_levels:
                if not self.tableservice.col_empty(evt.GetCol()):
                    menu.AppendSeparator()
                    scaling = wx.Menu()
                    custom = scaling.Append(wx.ID_ANY, _("Custom Scaling"))
                    self.frame.Bind(wx.EVT_MENU, self.tableservice.get_to_scaling(evt.GetCol(), constants.EMPTY), custom)

                    nominal = scaling.Append(wx.ID_ANY, _("Nominal Scaling"))
                    self.frame.Bind(wx.EVT_MENU, self.tableservice.get_to_scaling(evt.GetCol(), constants.DIAGONAL), nominal)

                    level = self.datastorage.table.attribute_levels[attribute]
                    if constants.allows_order(level):
                        ordinal = scaling.Append(wx.ID_ANY, _("Ordinal Scaling"))
                        interordinal = scaling.Append(wx.ID_ANY, _("Interordinal Scaling"))
                        self.frame.Bind(wx.EVT_MENU, self.tableservice.get_to_scaling(evt.GetCol(), constants.ORDINAL), ordinal)
                        self.frame.Bind(wx.EVT_MENU, self.tableservice.get_to_scaling(evt.GetCol(), constants.INTERORDINAL), interordinal)

                    menu.Append(wx.ID_ANY, _("Scale Attribute"), scaling)

            if self.frame.main_grid.GetColLabelValue(evt.GetCol()) not in self.datastorage.stats_visible:
                menu.AppendSeparator()
                stats = menu.Append(wx.ID_ANY, _("Display Statistics"))
                self.frame.Bind(wx.EVT_MENU, self.statservice.get_add_stats(evt.GetCol(), self.frame.main_grid.GetColLabelValue(evt.GetCol())), stats)

            level = wx.Menu()
            level_nom = wx.MenuItem(menu, -1, _("Nominal"))
            level_nom.SetBackgroundColour(constants.LEVEL_NOM_COLOR)
            level.Append(level_nom)
            self.frame.Bind(wx.EVT_MENU, self.tableservice.get_set_level(evt.GetCol(), attribute, constants.LEVEL_NOM), level_nom)
            level_ord = level.Append(wx.ID_ANY, _("Ordinal"))
            level_ord.SetBackgroundColour(constants.LEVEL_ORD_COLOR)
            self.frame.Bind(wx.EVT_MENU, self.tableservice.get_set_level(evt.GetCol(), attribute, constants.LEVEL_ORD), level_ord)
            if self.tableservice.check_numeric_col(evt.GetCol()):
                level_int = level.Append(wx.ID_ANY, _("Interval"))
                level_int.SetBackgroundColour(constants.LEVEL_INT_COLOR)
                self.frame.Bind(wx.EVT_MENU, self.tableservice.get_set_level(evt.GetCol(), attribute, constants.LEVEL_INT), level_int)
                level_rat = level.Append(wx.ID_ANY, _("Ratio"))
                level_rat.SetBackgroundColour(constants.LEVEL_RAT_COLOR)
                self.frame.Bind(wx.EVT_MENU, self.tableservice.get_set_level(evt.GetCol(), attribute, constants.LEVEL_RAT), level_rat)

            menu.Append(wx.ID_ANY, _("Set Level of Measurement"), level)

        self.frame.PopupMenu(menu)
        menu.Destroy()

    def label_menu(self, evt):

        evt.Skip()
        if self.tableservice.current_attribute() not in self.datastorage.result_visible:
            if evt.GetCol() == -1:
                self.show_row_menu(evt)
            else:
                self.show_col_menu(evt)

    def cell_menu(self, evt):

        menu = wx.Menu()
        if self.frame.csvtabs.GetSelection() != 1:
            purge = menu.Append(wx.ID_ANY, _("Purge Table"))
            reset = menu.Append(wx.ID_ANY, _("Reset Table"))
            self.frame.Bind(wx.EVT_MENU, self.tableservice.purge_table, purge)
            self.frame.Bind(wx.EVT_MENU, self.tableservice.reset_table, reset)
        if self.frame.csvtabs.GetSelection() == 0:
            dropcols = menu.Append(wx.ID_ANY, _("Drop Empty Columns"))
            droprows = menu.Append(wx.ID_ANY, _("Drop Empty Rows"))
            self.frame.Bind(wx.EVT_MENU, self.tableservice.drop_empty_cols, dropcols)
            self.frame.Bind(wx.EVT_MENU, self.tableservice.drop_empty_rows, droprows)
        if self.frame.csvtabs.GetSelection() == 1:
            self.add_draw_types(menu)

        if self.frame.csvtabs.GetSelection() > 0 and _("Scaling:") in self.frame.csvtabs.GetPageText(self.frame.csvtabs.GetSelection()):
            menu.AppendSeparator()
            self.add_draw_types(menu)

        if self.frame.csvtabs.GetSelection() > 0 and self.tableservice.current_attribute() in self.datastorage.result_visible:
            menu.AppendSeparator()
            to_scaling = menu.Append(wx.ID_ANY, _("Go to Scaling"))
            self.frame.Bind(wx.EVT_MENU, self.tableservice.get_to_scaling(evt.GetCol(), None), to_scaling)
        if self.frame.csvtabs.GetSelection() > 0:
            menu.AppendSeparator()
            attribute = self.tableservice.current_attribute()
            if attribute in self.datastorage.stats_visible:
                rescale = wx.Menu()
                custom = rescale.Append(wx.ID_ANY, _("Custom Scaling"))
                self.frame.Bind(wx.EVT_MENU, self.tableservice.get_rescale(constants.EMPTY), custom)

                nominal = rescale.Append(wx.ID_ANY, _("Nominal Scaling"))
                self.frame.Bind(wx.EVT_MENU, self.tableservice.get_rescale(constants.DIAGONAL), nominal)

                ordinal = rescale.Append(wx.ID_ANY, _("Ordinal Scaling"))
                self.frame.Bind(wx.EVT_MENU, self.tableservice.get_rescale(constants.ORDINAL), ordinal)

                interordinal = rescale.Append(wx.ID_ANY, _("Interordinal Scaling"))
                self.frame.Bind(wx.EVT_MENU, self.tableservice.get_rescale(constants.INTERORDINAL), interordinal)

                menu.Append(wx.ID_ANY, _("Rescale"), rescale)

            if self.frame.csvtabs.GetSelection() != 1:
                delete = menu.Append(wx.ID_ANY, _("Delete Scaling"))
                self.frame.Bind(wx.EVT_MENU, self.tableservice.get_delete_selected_scaling(self.tableservice.current_grid.GetCornerLabelValue()), delete)

        self.frame.PopupMenu(menu)
        menu.Destroy()

    def add_draw_types(self, menu):

        draw = wx.Menu()
        dim = draw.Append(wx.ID_ANY, _("Dim Draw"))
        self.frame.Bind(wx.EVT_MENU, self.tableservice.get_draw_lattice(constants.dim), dim)

        freese = draw.Append(wx.ID_ANY, _("Freese Draw"))
        self.frame.Bind(wx.EVT_MENU, self.tableservice.get_draw_lattice(constants.freese), freese)

        standard = draw.Append(wx.ID_ANY, _("Standard Draw"))
        self.frame.Bind(wx.EVT_MENU, self.tableservice.get_draw_lattice(constants.standard), standard)

        infadd = draw.Append(wx.ID_ANY, _("Inf-Additive Draw"))
        self.frame.Bind(wx.EVT_MENU, self.tableservice.get_draw_lattice(constants.inf), infadd)

        menu.Append(wx.ID_ANY, _("Draw Lattice"), draw)

    def graph_menu(self):

        menu = wx.Menu()
        redraw = menu.Append(wx.ID_ANY, _("Redraw Lattice"))
        clear = menu.Append(wx.ID_ANY, _("Clear Lattice"))

        self.frame.Bind(wx.EVT_MENU, self.graphservice.create_lattice_graph, redraw)
        self.frame.Bind(wx.EVT_MENU, self.graphservice.clear, clear)

        self.frame.PopupMenu(menu)
        menu.Destroy()

    def load_data(self, evt=None):

        tkinter.Tk().withdraw()
        filepath = tkinter.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filepath == "":
            return
        csvfile = open(filepath)
        storage_backup = self.datastorage.data
        self.datastorage.data = csvfile

        try:
            self.tableservice.fill_table()
            self.datastorage.clear_table()
            self.tableservice.clear_scalings()
            self.statservice.clear_stats()
            if self.frame.result_grid.GetNumberCols() > 0:
                self.frame.result_grid.DeleteCols(0, self.frame.result_grid.GetNumberCols())
            if self.frame.result_grid.GetNumberRows() > 0:
                self.frame.result_grid.DeleteRows(0, self.frame.result_grid.GetNumberRows())
            for i in range(self.frame.main_grid.GetNumberRows()):
                self.frame.result_grid.AppendRows(1)
                self.frame.result_grid.SetRowLabelValue(i, self.frame.main_grid.GetRowLabelValue(i))
        except:
            errortext = _('An error has occurred loading the context from the selected file. The file may be poorly formatted.')
            dialog = wx.MessageDialog(None, errortext, _('Error Loading Context'), wx.OK)
            dialog.ShowModal()
            dialog.Destroy()
            self.datastorage.data = storage_backup

    def load_fca(self, evt=None):
        tkinter.Tk().withdraw()
        filepath = tkinter.filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filepath == "":
            return
        fca = json.load(open(filepath))

        self.frame.main_grid.DeleteRows(0, self.frame.main_grid.GetNumberRows())
        tableservice.delete_cols(self.frame.main_grid)

        attributes = fca["context"]["attributes"]
        i = 0
        for a in attributes:
            self.frame.main_grid.AppendCols(1)
            self.frame.main_grid.SetColLabelValue(i, a)
            i += 1

        adj_list = fca["context"]["adjacency-list"]
        j = 0
        for b in adj_list:
            self.frame.main_grid.AppendRows(1)
            self.frame.main_grid.SetRowLabelValue(j, b["object"])
            intent = b["attributes"]
            for i in range(len(attributes)):
                if attributes[i] in intent:
                    self.frame.main_grid.SetCellValue(j, i, "True")
                else:
                    self.frame.main_grid.SetCellValue(j, i, "False")
            j += 1

        implications = fca["implication_sets"][0]["implications"]
        implications_formatted = list()
        for i in implications:
            implications_formatted.append((i["premise"], i["conclusion"]))
        self.datastorage.implications_tab.display(implications_formatted)

        self.datastorage.clear_table()
        self.tableservice.clear_scalings()
        self.statservice.clear_stats()

        self.frame.main_grid.SetRowLabelSize(grid.GRID_AUTOSIZE)
        self.frame.main_grid.SetCornerLabelValue("")
        self.tableservice.check_attribute_levels()

    def load_lattice(self, evt=None):

        tkinter.Tk().withdraw()
        filepath = tkinter.filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filepath == "":
            return
        file = open(filepath)
        storage_backup = self.datastorage.lattice
        self.datastorage.lattice = json.load(file)

        try:
            self.graphservice.create_lattice_graph()
        except:
            errortext = _('An error has occurred loading the lattice from the selected file. The file may be poorly formatted.')
            dialog = wx.MessageDialog(None, errortext, _('Error Loading Lattice'), wx.OK)
            dialog.ShowModal()
            dialog.Destroy()
            self.datastorage.lattice = storage_backup

    def save_data(self, e):

        tkinter.Tk().withdraw()
        filepath = tkinter.filedialog.asksaveasfilename(defaultextension=".csv")
        if filepath == "":
            return

        content = ""
        row_count = self.frame.main_grid.GetNumberRows()
        row_len = self.frame.main_grid.GetNumberCols()

        for labels in range(row_len):
            value = self.frame.main_grid.GetColLabelValue(labels)
            value = value.replace(",", "\,")
            content += value
            if labels < row_len - 1:
                content += ","
        content += "\n"

        for i in range(row_count):
            value = self.frame.main_grid.GetRowLabelValue(i)
            value = value.replace(",", "\,")
            value += ","
            content += value
            for j in range(row_len):

                value = self.frame.main_grid.GetCellValue(i, j)
                value = value.replace(",", "\,")
                content += value
                if j < row_len - 1:
                    content += ","
            content += "\n"

        f = open(filepath, "w")
        f.seek(0)
        f.write(content)
        f.truncate()
        f.close()
        self.datastorage.clear_edited()

    def empty_frame(self, e):
        print("Empty Frame")

    def manual(self, e):
        self.datastorage.status()

    def about(self, e):
        self.datastorage.status()

    def connect(self, evt=None):

        dialog = wx.TextEntryDialog(None, "Enter API Address:", value=self.api_address)
        answer = dialog.ShowModal()
        if answer == wx.ID_OK:
            wx.BeginBusyCursor()
            if api.check_connection(dialog.GetValue()):
                self.api_address = dialog.GetValue()
            else:
                connection_error_dialog(dialog.GetValue())
            wx.EndBusyCursor()
        dialog.Destroy()

    def quit_scaling(self, e=None):
        if not self.datastorage.edited:
            sys.exit(0)
        else:
            errortext = _('You have unsaved changes. Do you want to close the application regardless?')
            dialog = wx.MessageDialog(None, errortext, _('Data Loss Warning'), wx.ICON_WARNING | wx.YES_NO)
            answer = dialog.ShowModal()
            if answer == wx.ID_YES:
                dialog.Destroy()
                sys.exit(0)
            dialog.Destroy()

