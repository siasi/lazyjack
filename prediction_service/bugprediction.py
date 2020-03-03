import os
import csv

class Classification():
    "The classification obtained as result of the calssification algorithm."

    def __init__(self, files):
        self.files = files
        self.topPercentage = 5

    def size(self):
        "The size of the classification."
        return len(self.files)

    def topSize(self):
        "The size of the top of the classification."
        return len(self.files) / 100 * self.topPercentage

    def top(self):
        "The top of the classification."
        return self.files[:self.topSize()]

    def storeTop(self, classificationFile):
        "Store the classification passed as parameter in the passed classificationFile."

        f = open(classificationFile, "w")
        writer = csv.writer(f)
        writer.writerows(self.top())
        f.close()

class DefectsCache():
    "A cache for the data of the defect repository."

    def __init__(self):
        self.cache = {}
        self.knownBugs = set()
	
    def addValidBug(self, bugId, age):
        "Add a bug to the cache with its age."
        self.cache[bugId] = float(age)
        self.knownBugs.add(bugId)

    def addNotValidBug(self, bugId):
        "Add a bug to the cache. The bug has age equal to 0."
        self.cache[bugId] = float(0)
        self.knownBugs.add(bugId)

    def fill(self, cacheFile):
        "Fill this cache with values in passed file."

        if os.path.exists(cacheFile):
            with open(cacheFile, 'rb') as cFile:
                cacheReader = csv.reader(cFile)
                for row in cacheReader:
                    bugId = row[0]
                    age = row[1]
                    self.addValidBug(bugId, age)
                cFile.close()    

    def store(self, cacheFile):
        "Store this cache in the passed file."

        cacheFile = open(cacheFile, "wb")
        writer = csv.writer(cacheFile)
        
        writer.writerows(self.toCsv())
        cacheFile.flush()
        cacheFile.close()  
	
    def getAge(self, bugId):
        return self.cache[bugId]  
	
    def toCsv(self):
        return [[bugId, age] for bugId, age in self.cache.iteritems()]


class PredictionService():
    "Offer API for the prediction of bugs injection."

    def __init__(self, data_file):
        "Keep the path of the file containing the list of critical bugs."
        f = open(data_file, "rb")
        self.criticalFiles = [x[0] for x in csv.reader(f)]
        f.close()

    def prediction(changeSet):
        """Return the prediction for the input changeset.
        The changeset is a list of files paths that are part of the project.
        The result value is True if the changeset have high prediction 
        to inject a bug. False otherwise.
        """

        # check for at least a ranked file in change set
        for changed in changeSet:
            if changed in self.criticalFiles:
                return True
        return False
