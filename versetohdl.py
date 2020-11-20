import json
from tkinter import Tk
from tkinter.filedialog import askopenfilename

class Chip:
    def __init__(self, hdlName, id, inputNames, outputNames):
        self.hdlName = hdlName
        self.id = id
        self.inputNames = inputNames
        self.outputNames = outputNames
    def __str__(self):
        return "Chip: [name: %s, id: %d, inputNames: %s, outputNames: %s]" % (self.hdlName, self.id, str(self.inputNames), str(self.outputNames))

class Node:
    traversed = False
    parsed = False
    def __init__(self, label, chipId, id, outputIds, inputIds):
        self.label = label
        self.chipId = chipId
        self.id = id
        self.outputIds = outputIds
        self.inputIds = inputIds
    def __str__(self):
        return "Node: [label: %s, chipId: %d, id: %d, outputIds: %s, inputIds: %s" % (self.label, self.chipId, self.id, str(self.outputIds), str(self.inputIds))

class Connection:
    def __init__(self, fromId, toId, inputId, outputId):
        self.fromId = fromId
        self.toId = toId
        self.inputId = inputId
        self.outputId = outputId
    def __str__(self):
        return "Connection: [fromId: %d, toId: %d, inputId: %d, outputId: %d]" % (self.fromId, self.toId, self.inputId, self.outputId)

class Scope:
    inputNodes = []
    outputNodes = []
    nodes = []
    connections = []
    def __init__(self, scopeData, parsed):
        self.scopeData = scopeData
        self.parsed = parsed
        self.inputNodes = []
        self.outputNodes = []
        self.nodes = []
        self.connections = []


#Tk().withdraw()
#filename = askopenfilename()
filename = 'C:/Users/Evan/Desktop/project01.txt'

file = open(filename)
root = json.load(file)
scopes = root['scopes']
file.close()

# Chip dictionary
chips = []
chips.append(Chip("And", 0, ['a', 'b'], ['out']))
chips.append(Chip("Or", 1, ['a', 'b'], ['out']))
chips.append(Chip("Not", 2, ['in'], ['out']))
chips.append(Chip("Nand", 3, ['a', 'b'], ['out']))
chips.append(Chip("Nor", 4, ['a', 'b'], ['out']))
chips.append(Chip("Xor", 5, ['a', 'b'], ['out']))
chips.append(Chip("Out", 6, [], []))
# ------------------------------------

gateNames = {
    'AndGate': 0,    
    'OrGate': 1,
    'NotGate': 2,
    'NandGate': 3,
    'NorGate': 4,
    'XorGate': 5
}

allScopes = []

def getScopeIdFromId(id):
    for i in range(0, len(allScopes)):
        if allScopes[i].scopeData['id'] == id:
            return i
    return -1

def getChipIdFromScope(scopeId):
    scopeName = allScopes[scopeId].scopeData['name']
    for i in range(0, len(chips)):
        if chips[i].hdlName == scopeName:
            return i
    return -1

def traverseWires(wireId, fromWireId, allWires, outputIds):
    connections = allWires[wireId]['connections']
    if len(connections) == 1 and connections[0] == fromWireId:
        outputIds.append(wireId)
    else:
        for connection in connections:
            if connection != fromWireId:
                traverseWires(connection, wireId, allWires, outputIds)

def createConnections(scopeId, fromNode, allWires):
    if not fromNode.traversed:
        fromNode.traversed = True
        for o in range(0, len(fromNode.outputIds)):
            outputIds = []
            traverseWires(fromNode.outputIds[o], -1, allWires, outputIds)

            for node in allScopes[scopeId].nodes:
                if node.id != fromNode.id:
                    hasConnection = False
                    for i in range(0, len(node.inputIds)):
                        if node.inputIds[i] in outputIds:
                            hasConnection = True
                            allScopes[scopeId].connections.append(Connection(fromNode.id, node.id, i, o))
                    if hasConnection:
                        createConnections(scopeId, node, allWires)

def getNodeFromId(scopeId, nodeId):
    for node in allScopes[scopeId].nodes:
        if node.id == nodeId:
            return node
    return None

def getInputIds(gate):
    inputs = []
    if 'customData' in gate:
        wireData = gate['customData']['nodes']
        if 'inp' in wireData:
            inputs.extend(wireData['inp'])
        elif 'inp1' in wireData:
            inputs.append(wireData['inp1'])
    elif 'inputNodes' in gate:
        inputs.extend(gate['inputNodes'])
    return inputs

def getOutputIds(gate):
    outputs = []
    if 'customData' in gate:
        wireData = gate['customData']['nodes']
        if 'output' in wireData:
            outputs.extend(wireData['output'])
        elif 'output1' in wireData:
            outputs.append(wireData['output1'])
    elif 'outputNodes' in gate:
        outputs.extend(gate['outputNodes'])
    return outputs

finalOutput = ""
def buildHDL(scopeId, outputNode): # farthest node in the chain (aka outputs first)
    global finalOutput
    if not outputNode.parsed and outputNode.chipId != -1: # input id
        outputNode.parsed = True

        chipData = chips[outputNode.chipId]
        outputText = chipData.hdlName + '('
        outputConnections = []

        for connection in allScopes[scopeId].connections:
            if connection.toId == outputNode.id:
                buildHDL(scopeId, getNodeFromId(scopeId, connection.fromId))
                if connection.inputId + 1 > len(chipData.inputNames):
                    outputText += chr(ord('a') + connection.inputId)
                else:
                    outputText += chipData.inputNames[connection.inputId]
                if connection.fromId in allScopes[scopeId].inputNodes:
                    inputNode = getNodeFromId(scopeId, connection.fromId)
                    if inputNode.label != "":
                        outputText += '=' + inputNode.label + ','
                    else:
                        outputText += "=input" + str(connection.fromId) + ','
                else:
                    outputText += "=output" + str(connection.fromId) + 'o' + str(connection.outputId) + ','
            elif connection.fromId == outputNode.id and connection.toId in allScopes[scopeId].outputNodes:
                outputConnections.append(connection)

        for i in range(0, len(outputNode.outputIds)):
            if i + 1 > len(chipData.outputNames):
                outputText += "out" + str(i) + '='
            else:
                outputText += chipData.outputNames[i] + '='
            found = False
            for connection in outputConnections:
                if connection.outputId == i:
                    found = True
                    foundNode = getNodeFromId(scopeId, connection.toId)
                    if foundNode.label != "":
                        outputText += foundNode.label + ','
                    else:
                        outputText += "out" + str(i) + ','
                    break
            if not found:
                outputText += "output" + str(outputNode.id) + 'o' + str(i) + ','

        outputText = outputText[:-1]
        outputText += ");\n"

        if chipData.hdlName != "Out":
            finalOutput += outputText

def parseScope(scopeId):
    global finalOutput
    if not allScopes[scopeId].parsed:
        allScopes[scopeId].parsed = True

        scopeName = allScopes[scopeId].scopeData['name']

        uniqueId = 0
        for key in allScopes[scopeId].scopeData.keys():
            gateList = allScopes[scopeId].scopeData[key]     
            if key in gateNames:
                for gate in gateList:
                    allScopes[scopeId].nodes.append(Node(gate['label'], int(gateNames[key]), uniqueId, getOutputIds(gate), getInputIds(gate)))
                    uniqueId += 1
            elif key == 'Input':
                for gate in gateList:
                    allScopes[scopeId].nodes.append(Node(gate['label'], -1, uniqueId, getOutputIds(gate), []))
                    allScopes[scopeId].inputNodes.append(uniqueId)
                    uniqueId += 1
            elif key == 'Output':
                for gate in gateList:
                    allScopes[scopeId].nodes.append(Node(gate['label'], 6, uniqueId, [], getInputIds(gate)))
                    allScopes[scopeId].outputNodes.append(uniqueId)
                    uniqueId += 1
            elif key == 'SubCircuit':
                for subcircuit in gateList:
                    subScopeId = getScopeIdFromId(int(subcircuit['id']))
                    if subScopeId == -1:
                        raise Exception("Scope not found")
                    else:
                        parseScope(subScopeId)

                    chipId = getChipIdFromScope(subScopeId)
                    if chipId == -1:
                        raise Exception("Subchip not found")
                    else:
                        allScopes[scopeId].nodes.append(Node("", chipId, uniqueId, getOutputIds(subcircuit), getInputIds(subcircuit)))
                        uniqueId += 1

        # create a new chip for this subcircuit
        newChip = Chip("", -1, [], [])
        newChip.hdlName = scopeName
        newChip.id = len(chips)

        ioId = 0
        for input in allScopes[scopeId].inputNodes:
            inputNode = getNodeFromId(scopeId, input)
            createConnections(scopeId, inputNode, scopes[scopeId]['allNodes'])
        
            if inputNode.label == "":
                newChip.inputNames.append(chr(ord('a') + ioId))
            else:
                newChip.inputNames.append(inputNode.label)
            ioId += 1

        finalOutput += "Definition for " + scopeName + ":\n\n"

        ioId = 0
        for output in allScopes[scopeId].outputNodes:
            outputNode = getNodeFromId(scopeId, output)
            buildHDL(scopeId, outputNode)

            if outputNode.label == "":
                newChip.outputNames.append(chr(ord('a') + ioId))
            else:
                newChip.outputNames.append(outputNode.label)
            ioId += 1

        finalOutput += "\n\n"
        
        chips.append(newChip)


for scope in scopes:
    allScopes.append(Scope(scope, False))

parseScope(7)

print(finalOutput)

#for chip in chips:
#    print(chip)