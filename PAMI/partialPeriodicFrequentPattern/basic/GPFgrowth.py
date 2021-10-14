import sys

import validators
from urllib.request import urlopen
from PAMI.partialPeriodicFrequentPattern.basic.abstract import *

orderOfItem = {}


class Node:
    """
        A class used to represent the node of frequentPatternTree
        ...
        Attributes:
        ----------
        item : int
            storing item of a node
        parent : node
            To maintain the parent of every node
        child : list
            To maintain the children of node
        nodeLink : node
            To maintain the next node of node
        tidList : set
            To maintain timestamps of node

        Methods
        -------
        getChild(itemName)
        storing the children to their respective parent nodes
    """

    def __init__(self):
        self.item = -1
        self.parent = None
        self.child = []
        self.nodeLink = None
        self.tidList = set()

    def getChild(self, item):
        """
        :param item:
        :return: if node have node of item, then return it. if node don't have return []
        """

        for child in self.child:
            if child.item == item:
                return child
        return []


class Tree:
    """
        A class used to represent the frequentPatternGrowth tree structure

        ...
        Attributes
        ----------
        root : node
            Represents the root node of the tree
        nodeLinks : dictionary
            storing last node of each item
        firstNodeLink : dictionary
            storing first node of each item

        Methods
        -------
        addTransaction(transaction,timeStamp)
            creating transaction as a branch in frequentPatternTree
        fixNodeLinks(itemName, newNode)
            add newNode link after last node of item
        deleteNode(itemName)
            delete all node of item
        createPrefixTree(path,timeStampList)
            create prefix tree by path
        createConditionalTree(PFList, minSup, maxPer, minPR, last)
            create conditional tree. Its nodes are satisfy IP / (minSup+1) >= minPR

    """
    def __init__(self):
        self.root = Node()
        self.nodeLinks = {}
        self.firstNodeLink = {}

    def addTransaction(self, transaction, tid):
        """
        add transaction into tree
        :param transaction: it represents the one transactions in database
        :type transaction: list
        :param tid: represents the timestamp of transaction
        :type tid: list
        """
        current = self.root
        for item in transaction:
            child = current.getChild(item)
            if not child:
                newNode = Node()
                newNode.item = item
                newNode.parent = current
                current.child.append(newNode)
                current = newNode
                self.fixNodeLinks(item, newNode)
            else:
                current = child
            current.tidList.add(tid)

    def fixNodeLinks(self, item, newNode):
        """
        fix node link
        :param item: it represents item name of newNode
        :type item: string
        :param newNode: it represents node which is added
        :type newNode: Node
        """
        if item in self.nodeLinks:
            lastNode = self.nodeLinks[item]
            lastNode.nodeLink = newNode
        self.nodeLinks[item] = newNode
        if item not in self.firstNodeLink:
            self.firstNodeLink[item] = newNode

    def deleteNode(self, item):
        """
        delete the node from tree
        :param item: it represents the item name of node
        :type item: str
        """
        deleteNode = self.firstNodeLink[item]
        parentNode = deleteNode.parent
        parentNode.child.remove(deleteNode)
        parentNode.child += deleteNode.child
        parentNode.tidList |= deleteNode.tidList
        for child in deleteNode.child:
            child.parent = parentNode
        while deleteNode.nodeLink:
            deleteNode = deleteNode.nodeLink
            parentNode = deleteNode.parent
            parentNode.child.remove(deleteNode)
            parentNode.child += deleteNode.child
            parentNode.tidList |= deleteNode.tidList
            for child in deleteNode.child:
                child.parent = parentNode

    def createPrefixTree(self, path, tidList):
        """
        create prefix tree by path
        :param path: it represents path to root from prefix node
        :type path: list
        :param tidList: it represents tid of each item
        :type tidList: list
        """
        currentNode = self.root
        for item in path:
            child = currentNode.getChild(item)
            if not child:
                newNode = Node()
                newNode.item = item
                newNode.parent = currentNode
                currentNode.child.append(newNode)
                currentNode = newNode
                self.fixNodeLinks(item, newNode)
            else:
                currentNode = child
            currentNode.tidList |= tidList

    def createConditionalTree(self, PFList, minSup, maxPer, minPR, last):
        """
        create conditional tree by pflist
        :param PFList: it represent timeStamp each item
        :type PFList: dict
        :param minSup: it represents minSup
        :param maxPer: it represents maxPer
        :param minPR: it represents minPR
        :param last: it represents last timestamp in database
        :return: PFlist which satisfy ip / (minSup+1) >= minPR
        """
        keys = list(PFList)
        for item in keys:
            ip = calculateIP(maxPer, PFList[item], last).run()
            if ip / (minSup+1) >= minPR:
                continue
            else:
                self.deleteNode(item)
                del PFList[item]
        return PFList

class calculateIP:
    """
    This class calculate ip from timestamp
    ...
    Attributes
    ----------
    maxPer : float
        it represents user defined maxPer value
    timeStamp : list
        it represents timestamp of item
    timeStampFinal : int
        it represents last timestamp of database

    Methods
    -------
    run
        calculate ip from its timestamp list

    """
    def __init__(self, maxPer, timeStamp, timeStampFinal):
        self.maxPer = maxPer
        self.timeStamp = timeStamp
        self.timeStampFinal = timeStampFinal

    def run(self):
        """
        calculate ip from timeStamp list
        :return: it represents ip value
        """
        ip = 0
        self.timeStamp = sorted(list(self.timeStamp))
        if len(self.timeStamp) <= 0:
            return ip
        if self.timeStamp[0] - 0 <= self.maxPer:
            ip += 1
        for i in range(len(self.timeStamp)-1):
            if (self.timeStamp[i+1] - self.timeStamp[i]) <= self.maxPer:
                ip += 1
        if abs(self.timeStamp[(len(self.timeStamp)-1)] - self.timeStampFinal) <= self.maxPer:
            ip += 1
        return ip

class generatePFListver2:
    """
    generate time stamp list from input file
    ...
    Attributes
    ----------
    inputFile : str
        it is input file name
    minSup : float
        user defined minimum support value
    maxPer : float
        user defined max Periodicity value
    minPR : float
        user defined min PR value
    PFList : dict
        storing timestamps each item
    """
    def __init__(self, inputFile, minSup, maxPer, minPR):
        self.inputFile = inputFile
        self.minSup = minSup
        self.maxPer = maxPer
        self.minPR = minPR
        self.PFList = {}

    def run(self):
        """
        generate PFlist
        :return: timestamps and last timestamp
        """
        global orderOfItem
        tidList = {}
        dataSize = 0
        currentTime, last = int(), int()
        for l in self.inputFile:
            currentTime = int(l[0])
            for item in l[1:]:
                if item not in self.PFList:
                    self.PFList[item] = [1, currentTime, currentTime]
                    tidList[item] = set()
                    tidList[item].add(currentTime)
                else:
                    tidList[item].add(currentTime)
                    self.PFList[item][0] += 1
                    currentPeriodicity = currentTime - self.PFList[item][2]
                    self.PFList[item][2] = currentTime
                    if currentPeriodicity > self.PFList[item][1]:
                        self.PFList[item][1] = currentPeriodicity
            # for l in self.inputFile:
            #     currentTime = int(l.pop(0))
            #     for item in l:
            #         if item not in self.PFList:
            #             self.PFList[item] = [1, currentTime, currentTime]
            #             tidList[item] = set()
            #             tidList[item].add(currentTime)
            #         else:
            #             tidList[item].add(currentTime)
            #             self.PFList[item][0] += 1
            #             currentPeriodicity = currentTime - self.PFList[item][2]
            #             self.PFList[item][2] = currentTime
            #             if currentPeriodicity > self.PFList[item][1]:
            #                 self.PFList[item][1] = currentPeriodicity
            last = currentTime
        keys = list(self.PFList)
        for item in keys:
            currentPeriodicity = currentTime - self.PFList[item][2]
            if currentPeriodicity > self.PFList[item][1]:
                self.PFList[item][1] = currentPeriodicity
            ip = calculateIP(self.maxPer, tidList[item], last).run()
            if ip / (self.minSup+1) < self.minPR:
                del self.PFList[item]
                del tidList[item]
        tidList = {tuple([k]): v for k, v in sorted(tidList.items(), key=lambda x:len(x[1]), reverse=True)}
        orderOfItem = tidList.copy()
        return tidList, last


class generatePFTreever2:
    """
    create tree from tidList and input file
    ...
    Attributes
    ----------
    inputFile : str
        it represents input file name
    tidList : dict
        storing tids each item
    root : Node
        it represents the root node of the tree

    Methods
    -------
    run
        it create tree
    find separator(line)
        find separator in the line of database

    """
    def __init__(self, inputFile, tidList):
        self.inputFile = inputFile
        self.tidList = tidList
        self.root = Tree()

    def run(self):
        """
        create tree from database and tidList
        :return: the root node of tree
        """
        for transaction in self.inputFile:
            currentTime = int(transaction.pop(0))
            tempTransaction = [tuple([item]) for item in transaction if tuple([item]) in self.tidList]
            transaction = sorted(tempTransaction, key=lambda x: len(self.tidList[x]), reverse=True)
            self.root.addTransaction(transaction, currentTime)
            # for transaction in self.inputFile:
            #     tid = int(transaction.pop(0))
            #     tempTransaction = [tuple([item]) for item in transaction if tuple([item]) in self.tidList]
            #     transaction = sorted(tempTransaction, key=lambda x: len(self.tidList[x]), reverse=True)
            #     self.root.addTransaction(transaction, tid)
        return self.root
    
    
class PFGrowth:
    """
    This class is pattern growth algorithm
    ...
    Attributes
    ----------
    tree : Node
        represents the root node of prefix tree
    prefix : list
        prefix is list of prefix items
    PFList : dict
        storing time stamp each item
    minSup : float
        user defined min Support
    maxPer : float
        user defined max Periodicity
    minPR : float
        user defined min PR
    last : int
        represents last time stamp in database

    Methods
    -------
    run
        it is pattern growth algorithm

    """
    def __init__(self, tree, prefix, PFList, minSup, maxPer, minPR, last):
        self.tree = tree
        self.prefix = prefix
        self.PFList = PFList
        self.minSup = minSup
        self.maxPer = maxPer
        self.minPR = minPR
        self.last = last

    def run(self):
        """
        run the pattern growth algorithm
        :return: partial periodic frequent pattern in conditional pattern
        """
        global orderOfItem
        result = {}
        items = self.PFList
        if not self.prefix:
            items = reversed(self.PFList)
        for item in items:
            prefix = self.prefix.copy()
            prefix.append(item)
            PFList = {}
            prefixTree = Tree()
            prefixNode = self.tree.firstNodeLink[item]
            tidList = prefixNode.tidList
            path = []
            currentNode = prefixNode.parent
            while currentNode.item != -1:
                path.insert(0, currentNode.item)
                currentNodeItem = currentNode.item
                if currentNodeItem in PFList:
                    PFList[currentNodeItem] |= tidList
                else:
                    PFList[currentNodeItem] = tidList
                currentNode = currentNode.parent
            prefixTree.createPrefixTree(path, tidList)
            while prefixNode.nodeLink:
                prefixNode = prefixNode.nodeLink
                tidList = prefixNode.tidList
                path = []
                currentNode = prefixNode.parent
                while currentNode.item != -1:
                    path.insert(0, currentNode.item)
                    currentNodeItem = currentNode.item
                    if currentNodeItem in PFList:
                        PFList[currentNodeItem] = PFList[currentNodeItem] | tidList
                    else:
                        PFList[currentNodeItem] = tidList
                    currentNode = currentNode.parent
                prefixTree.createPrefixTree(path, tidList)
            ip = calculateIP(self.maxPer, self.PFList[item], self.last).run()
            s = len(self.PFList[item])
            if ip / (s+1) >= self.minPR and s >= self.minSup:
                result[tuple(prefix)] = [s, ip / (s+1)]
            if PFList:
                PFList = {k: v for k, v in sorted(PFList.items(), key=lambda x: len(orderOfItem[x[0]]), reverse=True)}
                PFList = prefixTree.createConditionalTree(PFList, self.minSup, self.maxPer, self.minPR, self.last)
            if PFList:
                obj = PFGrowth(prefixTree, prefix, PFList, self.minSup, self.maxPer, self.minPR, self.last)
                result1 = obj.run()
                result = result | result1
        return result


class GPFGrowth(partialPeriodicPatterns):
    """
    GPFGrowth is algorithm to mine the partial periodic frequent pattern in temporal database.

    ...
    Attributes:
    ----------
        inputFile : file
            Name of the input file to mine complete set of frequent pattern
        minSup : float
            The user defined minSup
        maxPer : float
            The user defined maxPer
        minPR : float
            The user defined minPR
        finalPatterns : dict
            it represents to store the pattern
        runTime : float
            storing the total runtime of the mining process
        memoryUSS : float
            storing the total amount of USS memory consumed by the program
        memoryRSS : float
            storing the total amount of RSS memory consumed by the program

    Methods:
    -------
        startMine()
            Mining process will start from here
        getPatterns()
            Complete set of patterns will be retrieved with this function
        savePatterns(outputFile)
            Complete set of frequent patterns will be loaded in to a output file
        getPatternsAsDataFrame()
            Complete set of frequent patterns will be loaded in to a output file
        getMemoryUSS()
            Total amount of USS memory consumed by the mining process will be retrieved from this function
        getMemoryRSS()
            Total amount of RSS memory consumed by the mining process will be retrieved from this function
        getRuntime()
            Total amount of runtime taken by the mining process will be retrieved from this function

    Format: 
    -------
        python3 GPFGrowth.py <inputFile> <outputFile> <minSup> <maxPer> <minPR>
        
        Examples: 
            python3 GPFGrowth.py sampleDB.txt patterns.txt 10 10 0.5

    Sample run of the importing code:
    ------------
        from PAMI.partialPeriodicFrequentPattern.basic import GPFGrowth as alg
    
        obj = alg.GPFGrowth(inputFile, outputFile, minSup, maxPer, minPR)
    
        obj.startMine()
        
        partialPeriodicFrequentPatterns = obj.getPatterns()

        print("Total number of partial periodic Patterns:", len(partialPeriodicFrequentPatterns))
    
        obj.savePatterns(oFile)
    
        Df = obj.getPatternAsDf()
    
        memUSS = obj.getMemoryUSS()
        
        print("Total Memory in USS:", memUSS)
    
        memRSS = obj.getMemoryRSS()
    
        print("Total Memory in RSS", memRSS)
    
        run = obj.getRuntime()
    
        print("Total ExecutionTime in seconds:", run)
    
    Credits:
    -------
        The complete program was written S.Nakamura under the supervision of Professor RAGE Uday Kiran. \n
    """
    iFile = ' '
    oFile = ' '
    sep = ' '
    startTime = float()
    endTime = float()
    minSup = float()
    maxPer = float()
    minPR = float()
    finalPatterns = {}
    runTime = 0
    memoryUSS = float()
    memoryRSS = float()
    Database = []
    lno = 0
    
    def creatingItemSets(self):
        """
            Storing the complete transactions of the database/input file in a database variable


        """
        self.Database = []
        if isinstance(self.iFile, pd.DataFrame):
            timeStamp, data = [], []
            if self.iFile.empty:
                print("its empty..")
            i = self.iFile.columns.values.tolist()
            if 'timeStamps' in i:
                timeStamp = self.iFile['timeStamps'].tolist()
            if 'Transactions' in i:
                data = self.iFile['Transactions'].tolist()
            if 'Patterns' in i:
                data = self.iFile['Patterns'].tolist()
            for i in range(len(data)):
                tr = [timeStamp[i]]
                tr.append(data[i])
                self.Database.append(tr)
            self.lno = len(self.Database)
        if isinstance(self.iFile, str):
            if validators.url(self.iFile):
                data = urlopen(self.iFile)
                for line in data:
                    self.lno += 1
                    line = line.decode("utf-8")
                    temp = [i.rstrip() for i in line.split(self.sep)]
                    temp = [x for x in temp if x]
                    self.Database.append(temp)
            else:
                try:
                    with open(self.iFile, 'r', encoding='utf-8') as f:
                        for line in f:
                            self.lno += 1
                            temp = [i.rstrip() for i in line.split(self.sep)]
                            temp = [x for x in temp if x]
                            self.Database.append(temp)
                except IOError:
                    print("File Not Found")
                    quit()

    def startMine(self):
        startTime = time.time()
        self.finalPatterns = {}
        self.creatingItemSets()
        obj = generatePFListver2(self.Database, self.minSup, self.maxPer, self.minPR)
        tidList, last = obj.run()
        PFTree = generatePFTreever2(self.Database, tidList).run()
        obj2 = PFGrowth(PFTree, [], tidList, self.minSup, self.maxPer, self.minPR, last)
        self.finalPatterns = obj2.run()
        endTime = time.time()
        self.runTime = endTime - startTime
        process = psutil.Process(os.getpid())
        self.memoryUSS = float()
        self.memoryRSS = float()
        self.memoryUSS = process.memory_full_info().uss
        self.memoryRSS = process.memory_info().rss

    def getMemoryUSS(self):
        """Total amount of USS memory consumed by the mining process will be retrieved from this function
        :return: returning USS memory consumed by the mining process
        :rtype: float
        """

        return self.memoryUSS

    def getMemoryRSS(self):
        """Total amount of RSS memory consumed by the mining process will be retrieved from this function
        :return: returning RSS memory consumed by the mining process
        :rtype: float
        """

        return self.memoryRSS

    def getRuntime(self):
        """Calculating the total amount of runtime taken by the mining process
        :return: returning total amount of runtime taken by the mining process
        :rtype: float
        """

        return self.runTime

    def getPatternsAsDataFrame(self):
        """Storing final frequent patterns in a dataframe
        :return: returning frequent patterns in a dataframe
        :rtype: pd.DataFrame
        """

        dataframe = {}
        data = []
        for a, b in self.finalPatterns.items():
            data.append([a, b[0], b[1]])
            dataframe = pd.DataFrame(data, columns=['Patterns', 'Support', 'Periodicity'])
        return dataframe

    def savePatterns(self, outFile):
        """Complete set of frequent patterns will be loaded in to a output file
        :param outFile: name of the output file
        :type outFile: file
        """
        self.oFile = outFile
        writer = open(self.oFile, 'w+')
        for x, y in self.finalPatterns.items():
            s1 = str(x) + ":" + str(y)
            writer.write("%s \n" % s1)

    def getPatterns(self):
        """ Function to send the set of frequent patterns after completion of the mining process
        :return: returning frequent patterns
        :rtype: dict
        """
        return self.finalPatterns


if __name__ == '__main__':
    ap = str()
    if len(sys.argv) == 6 or len(sys.argv) == 7:
        if len(sys.argv) == 7:
            ap = GPFGrowth(sys.argv[1], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
        if len(sys.argv) == 6:
            ap = GPFGrowth(sys.argv[1], sys.argv[3], sys.argv[4], sys.argv[5])
        ap.startMine()
        Patterns = ap.getPatterns()
        print("Total number of Frequent Patterns:", len(Patterns))
        ap.savePatterns(sys.argv[2])
        memUSS = ap.getMemoryUSS()
        print("Total Memory in USS:", memUSS)
        memRSS = ap.getMemoryRSS()
        print("Total Memory in RSS", memRSS)
        run = ap.getRuntime()
        print("Total ExecutionTime in ms:", run)
    else:
        ap = GPFGrowth('https://www.u-aizu.ac.jp/~udayrage/datasets/temporalDatabases/temporal_T10I4D100K.csv',
                     9, 1000, 0.4)
        ap.startMine()
        Patterns = ap.getPatterns()
        for x, y in Patterns.items():
            print(x, y)
        print("Total number of Frequent Patterns:", len(Patterns))
        ap.savePatterns('/home/apiiit-rkv/Downloads/fp_pami/output')
        memUSS = ap.getMemoryUSS()
        print("Total Memory in USS:", memUSS)
        memRSS = ap.getMemoryRSS()
        print("Total Memory in RSS", memRSS)
        run = ap.getRuntime()
        print("Total ExecutionTime in ms:", run)
        print("Error! The number of input parameters do not match the total number of parameters provided")
