import wx
from scaling_app.api import request_exploration_step
from scaling_app.customdialogs import NewObjectDialog, make_implication_string


def ask_attributes(self):
    # Displays a dialog to enter the starting attributes for the exploration.
    dialog = wx.TextEntryDialog(None, "Enter starting attributes:", "Attribute Exploration")
    dialog.ShowModal()
    attributes_string = dialog.GetValue()
    dialog.Destroy()
    attributes = []
    for a in attributes_string.split(","):
        attributes.append(a.lstrip().rstrip())
    return list(set(attributes))


def ask_starting_object(self, additional=False):
    # Displays a dialog asking if starting objects should be added
    if additional:
        question_Str = "Do you want to add another starting object?"
    else:
        question_Str = "Do you want to add starting objects?"

    dialog = wx.MessageDialog(None, question_Str, "Attribute Exploration", wx.YES_NO | wx.CANCEL)
    answer = dialog.ShowModal()
    dialog.Destroy()
    return answer


def ask_implication_holds(self, implication):
    # Displays a dialog asking whether the specified implication holds
    implication_text = "Does the following implication hold? " + "\n" + make_implication_string(implication[0])

    dialog = wx.MessageDialog(None, implication_text, "Attribute Exploration", wx.YES_NO | wx.CANCEL)
    answer = dialog.ShowModal()
    dialog.Destroy()
    return answer


def ask_object(self, implications, objects, attributes, asked_implication=None):
    # Displays a dialog for entering a new object.
    dialog = NewObjectDialog(None, wx.ID_ANY, title="Attribute Exploration", asked_implication=asked_implication, implications=implications, objects=objects, attributes=attributes)
    if asked_implication:
        dialog.SetRequiredAttributes(asked_implication)
        pass
    answer = dialog.ShowModal()
    new_object = dialog.GetValues()
    dialog.Destroy()
    if answer == wx.ID_CANCEL:
        return wx.ID_CANCEL, wx.ID_CANCEL
    else:
        return new_object


def display_result(self, result):
    # Displays the context resulting from the exploration step in the single valued grid
    objects = result['step']['result']['context']['objects']
    attributes = result['step']['result']['context']['attributes']
    incidence = dict()
    for i in result['step']['result']['context']['incidence']:
        x_coord = objects.index(i[0])
        y_coord = attributes.index(i[1])
        incidence[x_coord, y_coord] = "✘"
    self.scservice.fill_context(objects, attributes, incidence)


class ExplorationService:

    def __init__(self, frame, datastorage, menuservice, simplecontextservice, tableservice):
        self.frame = frame
        self.datastorage = datastorage
        self.mservice = menuservice
        self.scservice = simplecontextservice
        self.tservice = tableservice

    def explore(self, evt):
        # Performs attribute exploration algorithm.

        objects = []
        attributes = ask_attributes(self)
        incidence = []
        implications = []

        # Add starting objects
        answer = ask_starting_object(self)
        while answer == wx.ID_YES:

                name, incident_attributes = ask_object(self, implications, objects, attributes)
                objects.append(name)
                for a in incident_attributes:
                    incidence.append([name, a])

                answer = ask_starting_object(self, True)
        if answer == wx.ID_CANCEL:
            return

        # Exploration
        while True:
            result = request_exploration_step(self.mservice.api_address, objects, attributes, incidence, implications)
            asked_implication = result['step']['result']['implications']

            display_result(self, result)

            # No further implications, Exploration over:
            if not asked_implication:
                break

            answer = ask_implication_holds(self, asked_implication)

            if answer == wx.ID_CANCEL:
                display_result(self, result)
                break

            if answer == wx.ID_YES:
                implications += asked_implication

            if answer == wx.ID_NO:
                name, incident_attributes = ask_object(self, implications, objects, attributes, asked_implication)

                if name == wx.ID_CANCEL:
                    display_result(self, result)
                    break

                objects.append(name)
                for a in incident_attributes:
                    incidence.append([name, a])
