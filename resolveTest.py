import unittest
from resolve import MoveToR, RallyService, CdetsService, CollectParameters, ValidateDefect, TasksModel
from batchcli import Cli, BatchCli
from cdets import CdetsDefect

class CollectParametersTest(unittest.TestCase):

    def setUp(self):
        self.rally = FakeRallyService()
        self.cdets = FakeCdetsService()
        self.model = TasksModel()

        self.m = CollectParameters("Collect Defect Parameters", self.cdets, self.model)
        self.m.defectId = "111"
        self.c = FakeCli()


    def test_task_is_defined(self):
        self.m != None

    def test_task_show_apply_to_values(self):
        bc = BatchCli(self.c)

        messages = []
        messages.append("[  ?  ] Please enter Apply To [009.006(003.246)]")
        messages.append("[  ?  ] Please enter Origin or (L)ist valid values [v1]")
        messages.append("[  ?  ] Breackage (Y|N) [N]")
        messages.append("[  ?  ] Is bug in released code? (Y|N) [N]")
        messages.append("[  ?  ] Is a Dev-Escape? (Y|N) [N]")
        messages.append("[  ?  ] Enter Dev-Escape activity or (L)ist valid values [v1]")

        self.c.expect(messages)
        self.c.pleaseAnswer("\n","\n","\n","\n","\n","\n","\n")

        self.m.run(bc) 
        self.c.verify()


class ValidateDefectTest(unittest.TestCase):

    def setUp(self):
        self.rally = FakeRallyService()
        self.cdets = FakeCdetsService()
        self.model = TasksModel()

        self.m = ValidateDefect("Validate the CDETS Defect", self.rally, self.cdets, self.model)
        self.m.defectId = "111"
        self.c = FakeCli()

    def test_rally_defect_with_invalid_name_print_error_and_exit(self):
        messages = []
        messages.append("DE111 :  Defect")
        messages.append("Unable to get CDETS defect from Rally defect DE111")
        self.c.expect(messages)

        self.m.run(self.c)
        self.assertEquals(self.c.latestMessage, "Unable to get CDETS defect from Rally defect DE111")
        self.assertTrue(self.m.failed)

    def test_rally_defect_with_valid_name_and_not_ready_to_r(self):
        self.rally.defect = FakeRallyDefect("CSC1111 Defect Title")

        bug = FakeCdetsBug("CSC111")
        bug.missingEnclosures = [FakeEnclosure("A missing enclosure")]
        self.cdets.returnBug(bug)

        messages = []
        messages.append("DE111 :  CSC1111 Defect Title")
        messages.append("CDETS Defect is NOT compliant to Quality Process and cannot be move to R state.")
        messages.append("Missing Enclosures:")
        messages.append(" - A missing enclosure")
        
        self.c.expect(messages)

        self.m.run(self.c)

        self.c.verify()
        self.assertTrue(self.m.failed)

class MoveToRTest(unittest.TestCase):

    def setUp(self):
        self.rally = FakeRallyService()
        self.cdets = FakeCdetsService()
        self.model = TasksModel()

        self.m = MoveToR("Move to R the CDETS Defect", self.cdets, self.model)
        self.m.model = self.model
        self.m.defectId = "111"
        self.c = FakeCli()

    def test_task_is_defined(self):
        self.m != None

    def test__move_to_r(self):
        self.rally.defect = FakeRallyDefect("CSC1111 Defect Title")
        self.cdets.returnBug(FakeCdetsBug("CSC111"))

        messages = []
        messages.append("Updating CDETS defect")
        messages.append("Bug is now in R state")
        self.c.expect(messages)

        self.m.defectId = "CSC111"
        self.m.model.cdetsDefect = FakeCdetsBug("CSC111")
        self.m.run(self.c)

        self.c.verify()
        self.assertFalse(self.m.failed)


class FakeRallyDefect():
    def __init__(self, name="Defect"):
        self.FormattedID = "DE111"
        self.Name = name

class FakeRallyService(RallyService):

    def __init__(self):
        self.defect = FakeRallyDefect()

    def getDefect(self, defectId):
        return self.defect

    def accept(self, rallyDefect):
        pass

class FakeCdetsBug(CdetsDefect):
    
    def __init__(self, id):
        self.cdetsId = id
        self.missingEnclosures = []

    def getMissingEnclosures(self):
        if not self.missingEnclosures:
            return None
        return self.missingEnclosures

    def isReadyToMoveToRState(self):
        return True

    def hasAllRequiredEnclosureForRState(self):
        return not self.getMissingEnclosures()

class FakeEnclosure():

    def __init__(self, name):
        self.name = name 

class FakeCdetsService(CdetsService):

    def __init__(self, bug=None):
        self.bug = bug

    def getBug(self, id):
        return self.bug

    def returnBug(self, bug):
        self.bug = bug

    def resolveBug(self, cdetsDefect, params):
        pass

    def getLatestApplyTo(self, n):
        return ["009.006(003.244)", "009.006(003.245)", "009.006(003.246)"]

    def getValidValues(self, field):
        return ["v1", "v2"]

    def getDevEscapeActivityValues(self, isDevEscape):
        return ["v1", "v2"]

class FakeCli(Cli):

    def __init__(self):
        self.countAsk = 0
        self.countLog = 0
        self.predefinedAnswer = []
        self.expectedMessages = []
        self.messages = []


    def newMessage(self, message):
        self.latestMessage = message
        self.messages.append(message)

    def ask(self, message, default=None):
        self.latestMessage = message
        self.messages.append(message)
        return self.__getAnswer()

    def negate(self, message, default=None):
        self.latestMessage = message
        return False

    def select(self, message, default=None):
        self.latestMessage = message
        return False

    def __getAnswer(self):
        if self.countAsk not in range(0, len(self.predefinedAnswer)):
            raise AssertionError("Unexpected call to ask method!")
        answer = self.predefinedAnswer[self.countAsk]
        self.countAsk = self.countAsk + 1
        return answer

    def pleaseAnswer(self, *answer):
        self.countAsk = 0
        self.predefinedAnswer = list(answer)

    def expect(self, messages):
        self.expectedMessages = messages

    def verify(self):
        if self.expectedMessages:
            if not self.expectedMessages == self.messages:
                msg = 'Expected message "' + str(self.expectedMessages) + '" in sequence, but was "'  + str(self.messages) + '"'
                msg = msg + '\n'
                msg = msg + 'Messages not matching: '
                msg = msg + str(set(self.messages) - set(self.expectedMessages))
                msg = msg + '\n'
                msg = msg + 'Missing messages: '
                msg = msg + str(set(self.expectedMessages) - set(self.messages))
                raise AssertionError(msg)

if __name__ == "__main__":
    unittest.main()