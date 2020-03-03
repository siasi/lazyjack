
#
# This script provide the capability to mark a defect in Really as Accepted and the
# correspondent CDETS bug as resolved.
#
# author: siasi@cisco.com
#

import platform
import sys
import re, datetime

from rally import RallyService

from batchcli import Task, TaskEngine, SimpleCli
from cdets import EnclosureTest, CdetsDefect, getCdetsDefects, CdetsService
from getpass import getpass,getuser
from cc import runCommand
from optparse import OptionParser


class ValidateDefect(Task):

    def __init__(self, name, rallyService, cdetsService, model):
        Task.__init__(self, name)
        self.rally = rallyService
        self.cdetsService = cdetsService
        self.model = model

    def run(self, cli):
    
        self.model.rallyDefect = self.rally.getDefect(self.model.id)
        
        self.model.cdetsDefect = self.__toCdetsBug(self.model.rallyDefect, self.cdetsService, cli)

        if not self.model.id:
            self.failed = True
            return

        if not self.__isDefectCompliantWithQualityProcess(self.model.cdetsDefect, cli):
            self.failed = True

    def __isDefectCompliantWithQualityProcess(self, cdetsDefect, cli):   
        #cli.newMessage("Checking Enclosures")

        if not cdetsDefect.hasAllRequiredEnclosureForRState():
            cli.newMessage("CDETS Defect is NOT compliant to Quality Process and cannot be move to R state.")
            cli.newMessage("Missing Enclosures:")
            for enclosure in cdetsDefect.getMissingEnclosures():
                cli.newMessage(" - " + enclosure.name)
            return False

        cli.newMessage("CDETS Defect is compliant to Quality Process")
        return True

    def __toCdetsBug(self, rallyDefect, cdets, cli):
        cli.newMessage(rallyDefect.FormattedID + " :  " + rallyDefect.Name)

        if not rallyDefect.Name.startswith('CSC'):
            cli.newMessage("Unable to get CDETS defect from Rally defect " +  rallyDefect.FormattedID)
            return None

        cdetsId = rallyDefect.Name.split()[0]
        return cdets.getBug(cdetsId)

class MoveToA(Task):

    def __init__(self, name, rallyService, model):
        Task.__init__(self, name)
        self.rally = rallyService
        self.model = model

    def run(self, cli):
        cli.newMessage("Updating Rally defect " + self.model.rallyDefect.FormattedID)
        self.rally.accept(self.model.rallyDefect)
        cli.newMessage("Defect is in A state")

class MoveToR(Task):

    def __init__(self, name, cdetsService, model):
        Task.__init__(self, name)
        self.cdetsService = cdetsService
        self.model = model


    def run(self, cli):
        if self.model.cdetsDefect.isReadyToMoveToRState():
            cli.newMessage("Updating CDETS defect")
        else:
            cli.newMessage("Updating CDETS defect: adding Engineer and To-be-fixed")
            self.cdetsService.resolveBug(self.model.cdetsDefect, self.model.rParams)
        
        cli.newMessage("Bug is now in R state")

class CdetsDefectParameters():
    def __init__(self):
        pass
	
class CollectParameters(Task):
    
    def __init__(self, name, cdets, model):
        Task.__init__(self, name)
        self.params = CdetsDefectParameters()
        self.id = model.id
        self.cdets = cdets
        self.model = model

    def run(self, cli):
        self.params.id = self.id
        values = self.cdets.getLatestApplyTo(3)
        
        self.params.applyTo = cli.ask("Please enter Apply To", default=values[-1])
        self.params.origin = cli.select("Please enter Origin or (L)ist valid values", self.cdets.getValidValues('Bug-origin'))
        self.params.breackage = negateToBoolean(cli.negate("Breackage"))
        self.params.inReleasedCode =negateToBoolean(cli.negate("Is bug in released code?"))
	
        isDevEscape = cli.negate("Is a Dev-Escape?")
        self.params.isDevEscape = negateToBoolean(isDevEscape)
        self.params.devEscapeActivity = cli.select("Enter Dev-Escape activity or (L)ist valid values", self.cdets.getDevEscapeActivityValues(isDevEscape))
        self.model.rParams = self.params
	
	
class SelectDefect(Task):

    def __init__(self, name, rally, model):
        Task.__init__(self, name)
        self.rally = rally
	self.model = model
	
    def run(self, cli):
        defects = self.rally.getDefectsInCurrentIterationFor(getuser())
	defectsToShow = [defect.FormattedID + ' ' + defect.Name for defect in defects if defect.ScheduleState != 'Accepted']
	
	if not defectsToShow:
	    cli.newMessage("There are no defects to be accepted")
	    cli.newMessage("Please make sure defects are assigned and are in current or past iteration")
	    self.failed = True
	    return
	
	selected = cli.select("Please select the defect ID or (L)ist assigned defects:", defectsToShow)
	self.model.id = selected[:6]
	
def negateToBoolean(b):
    if b:
        return "N"
    return "Y"	

class TasksModel():
    
    def __init__(self):
        self.id = None
        self.cdetsDefect = None
        self.rParams = None

 
def resolve(defectId):

    model = TasksModel()
    
    rally = RallyService()
    #for iter in rally.getCurrentIterations():
    #    if hasattr(iter, 'Name'):
    #	    print iter
        
    #sys.exit(0)
    cdets = CdetsService()
    
    validate = ValidateDefect("Validate defect in Rally and CDEST", rally, cdets, model)
    collect = CollectParameters("Collect CDETS Defect parameters", cdets, model) 
    moveToR = MoveToR("Move to R the CDETS Defect", cdets, model)
    moveToA = MoveToA("Move to A the Rally Defect", rally, model)
    
    engine = TaskEngine(SimpleCli())
    
    if not defectId:
        engine.addTask(SelectDefect("Select the defect to move to A", rally, model))
    else:
        model.id =  defectId[2:]
    
    engine.addTask(validate)
    engine.addTask(collect)
    engine.addTask(moveToR)
    engine.addTask(moveToA)

    engine.run()

DEFECT_ID_PATTERN = re.compile('DE\d{3}')

if __name__ == "__main__":
   
    import __init__ as lazyjack
    parser = OptionParser(prog="review", usage="%prog [options] defectId", description="", version=lazyjack.opt_ver)
    parser.add_option("-d", "--defect", dest="defectId",
                      help="The defect to move to A state", metavar="DEFECT ID")
    (opt, args) = parser.parse_args()
	
    if opt.defectId and not re.match(DEFECT_ID_PATTERN, opt.defectId):
        print "Please provide a Defect ID with valid format."
	parser.print_help()
	sys.exit(1)
     
    resolve(opt.defectId)
    
#cdets -p CSC.embu -r ctm -m To-be-fixed
