
from pyral import Rally, rallySettings
import datetime


def getRallyConnection():
    server = "rally1.rallydev.com"
    user = "auditor@cisco.com"
    password = "cisco123"
    workspace = "default"
    project = "default"
        
    rally = Rally(server, user, password)
    rally.enableLogging('lj.rally.log')
    return rally
    
class RallyService():

    def __init__(self):
        self.rally = getRallyConnection()
	
    def getDefect(self, defectId):
        queryDefect = 'FormattedID = "' + defectId + ' "'
        return list(self.rally.get('Defect', fetch=True, query=queryDefect))[0]
	
    def accept(self, rallyDefect):
        defect_data = { "FormattedID" : rallyDefect.FormattedID.encode(),  "ScheduleState"  : "Accepted"  }

        try:
            defect = self.rally.update('Defect', defect_data)
        except Exception, details:
            sys.stderr.write('ERROR: %s \n' % details)
            sys.exit(1)
	    
    def getIterationsForRealease(self, releaseName, teams):
        today = datetime.date.today().isoformat()
        query = 'Name = "' + releaseName  + '"' 
	release = list(self.rally.get('Release', fetch=True, query=query))
	query = '(StartDate >= "' + release[0].ReleaseStartDate  + '") AND (EndDate <= "' + release[0].ReleaseDate + '")'
	#query += ' OR (((StartDate < "' + release[0].ReleaseStartDate + '") AND (EndDate < "' + release[0].ReleaseDate + '"))'
	#query += ' OR ((StartDate < "' + release[0].ReleaseDate + '") AND (EndDate > "' + release[0].ReleaseDate + '")))'
	
	print query
	
	return self.rally.get('Iteration', fetch="Name,StartDate,EndDate,Project", query=query) 
    
    def getPastIterations(self, releaseName, teams):
        today = datetime.date.today().isoformat()
        query = 'Name = "' + releaseName  + '"' 
	release = list(self.rally.get('Release', fetch=True, query=query))
	query = '((StartDate >= "' + release[0].ReleaseStartDate  + '") AND (EndDate <= "' + release[0].ReleaseDate + '"))'
	query += ' AND (EndDate < "' + today + '")'
	#query += ' OR ((StartDate < "' + release[0].ReleaseDate + '") AND (EndDate > "' + release[0].ReleaseDate + '")))'
	
	print query
	
	return self.rally.get('Iteration', fetch="Name,StartDate,EndDate,Project", query=query) 
    
    def getCurrentIterations(self):
        today = datetime.date.today().isoformat()
        query = '(StartDate <= "' + today  + '") AND (EndDate >= "' + today + '")' 
	return self.rally.get('Iteration', fetch="Name,StarDate,EndDate,Project", query=query)
	 
    def getDefectsInCurrentIterationFor(self, userId):
        query = '(Iteration.Name = "' + '2013-01 (07JAN)' + '") AND (Owner.Name = "' + userId + '@cisco.com")'
	#print "Query Defect:", query
        return self.rally.get('Defect', fetch=True, query=query)

    def getDefectsForIteration(self, iteration):
        query = 'Iteration.Name = "' + iteration.Name + '"'
	#print "Query Defect:", query, "for project", iteration.Project.Name
        return self.rally.get('Defect', fetch=True, project=iteration.Project.Name, query=query)

    def getUsForIteration(self, iteration, releaseName):
        queryUS = 'Iteration.Name = "' + iteration.Name + '"'
        return self.rally.get('HierarchicalRequirement', fetch=True, project=iteration.Project.Name, query=queryUS)
