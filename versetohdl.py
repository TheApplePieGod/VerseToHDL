import json
from tkinter import Tk
from tkinter.filedialog import askopenfilename

class Chip:
    def __init__(self, hdlName, id, inputNames, outputNames, bitDepth):
        self.hdlName = hdlName
        self.id = id
        self.inputNames = inputNames
        self.outputNames = outputNames
        self.bitDepth = bitDepth
    def __str__(self):
        return "Chip: [name: %s, id: %d, inputNames: %s, outputNames: %s, bitDepth: %d]" % (self.hdlName, self.id, str(self.inputNames), str(self.outputNames), self.bitDepth)

class Node:
    traversed = False
    parsed = False
    def __init__(self, label, chipId, id, outputIds, inputIds, bitDepth):
        self.label = label
        self.chipId = chipId
        self.id = id
        self.outputIds = outputIds
        self.inputIds = inputIds
        self.bitDepth = bitDepth
    def __str__(self):
        return "Node: [label: %s, chipId: %d, id: %d, outputIds: %s, inputIds: %s, bitDepth: %d]" % (self.label, self.chipId, self.id, str(self.outputIds), str(self.inputIds), self.bitDepth)

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

Tk().withdraw()
filename = askopenfilename()

entrypointName = input("Name of the circuit to parse (Enter nothing for Main)? ")
smartNaming = input("Smart naming (y/n)? ") == "y"

file = open(filename)
root = json.load(file)
scopes = root['scopes']
file.close()

# Chip dictionary
chips = []
chips.append(Chip("And", 0, ['a', 'b'], ['out'], 1))
chips.append(Chip("Or", 1, ['a', 'b'], ['out'], 1))
chips.append(Chip("Not", 2, ['in'], ['out'], 1))
chips.append(Chip("Nand", 3, ['a', 'b'], ['out'], 1))
chips.append(Chip("Nor", 4, ['a', 'b'], ['out'], 1))
chips.append(Chip("Xor", 5, ['a', 'b'], ['out'], 1))
chips.append(Chip("Splitter", 6, [], [], 1))
chips.append(Chip("Mux", 7, ['a', 'b', 'sel'], ['out'], 1))
chips.append(Chip("Mux4Way", 8, ['a', 'b', 'c', 'd', 'sel'], ['out'], 1))
chips.append(Chip("Mux8Way", 9, ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'sel'], ['out'], 1))
chips.append(Chip("Out", 10, [], [], 1))
# ------------------------------------

gateNames = {
    'AndGate': 0,    
    'OrGate': 1,
    'NotGate': 2,
    'NandGate': 3,
    'NorGate': 4,
    'XorGate': 5,
    'Splitter': 6,
    'Mux': 7,
    'Mux4Way': 8,
    'Mux8Way': 9
}

allScopes = []

def getScopeIdFromId(id):
    for i in range(0, len(allScopes)):
        if allScopes[i].scopeData['id'] == id:
            return i
    return -1

def getScopeIdFromName(name):
    for i in range(0, len(allScopes)):
        if allScopes[i].scopeData['name'] == name:
            return i
    return -1

def getChipIdFromScope(scopeId):
    scopeName = allScopes[scopeId].scopeData['name']
    for i in range(0, len(chips)):
        if chips[i].hdlName == scopeName:
            return i
    return -1

def findConnection(scopeId, nodeId):
    for i in range(0, len(allScopes[scopeId].connections)):
        if allScopes[scopeId].connections[i].toId == nodeId:
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
        elif 'outputs' in wireData:
            outputs.extend(wireData['outputs'])
    elif 'outputNodes' in gate:
        outputs.extend(gate['outputNodes'])
    return outputs

def buildHDL(scopeId, outputNode, toReplace): # farthest node in the chain (aka outputs first)
    finalOutput = ""
    if not outputNode.parsed and outputNode.chipId != -1: # input id
        outputNode.parsed = True

        chipData = chips[outputNode.chipId]
        outputText = chipData.hdlName + (str(outputNode.bitDepth) if outputNode.bitDepth > 1 else "") + '('
        outputConnections = []
        inputNames = []

        for connection in allScopes[scopeId].connections:
            if connection.toId == outputNode.id:
                finalOutput += buildHDL(scopeId, getNodeFromId(scopeId, connection.fromId), toReplace)
                if connection.inputId + 1 > len(chipData.inputNames):
                    outputText += chr(ord('a') + connection.inputId)
                else:
                    outputText += chipData.inputNames[connection.inputId]

                fromSplitter = False
                actualInputId = connection.fromId
                if chips[allScopes[scopeId].nodes[connection.fromId].chipId].hdlName == "Splitter": # if we are getting an input from a splitter, actually use the output of the splitter's input
                    fromSplitter = True
                    connectionId = findConnection(scopeId, connection.fromId)
                    if connectionId != -1:
                        actualInputId = allScopes[scopeId].connections[connectionId].fromId
                    
                if actualInputId in allScopes[scopeId].inputNodes:
                    inputNode = getNodeFromId(scopeId, actualInputId)
                    if inputNode.label != "":
                        outputText += '=' + inputNode.label
                        inputNames.append(inputNode.label)
                    else:
                        outputText += "=input" + str(actualInputId)
                        inputNames.append("input" + str(actualInputId))

                    if fromSplitter:
                        outputText += '[' + str(connection.outputId) + ']'
                        
                    outputText += ','
                else:
                    outputText += "=output" + str(actualInputId) + 'o' + str(connection.outputId)
                    inputNames.append("output" + str(actualInputId) + 'o' + str(connection.outputId))

                    if fromSplitter:
                        outputText += '[' + str(connection.outputId) + ']'
                    
                    outputText += ','
            elif connection.fromId == outputNode.id and connection.toId in allScopes[scopeId].outputNodes:
                outputConnections.append(connection)

        for i in range(0, len(outputNode.outputIds)):
            outText = ""
            if i + 1 > len(chipData.outputNames):
                outText = "out" + str(i) + '='
            else:
                outText = chipData.outputNames[i] + '='
            outputText += outText
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
            if found:
                outputText += outText
            outputName = "output" + str(outputNode.id) + 'o' + str(i)
            outputText += outputName + ','
            if smartNaming:
                replaceText = ""
                for name in inputNames:
                    replaceText += name
                replaceText += chipData.hdlName
                if i + 1 > len(chipData.outputNames):
                    replaceText += str(i)
                elif chipData.outputNames[i] != "out":
                    replaceText += chipData.outputNames[i]
                toReplace[outputName] = replaceText

        outputText = outputText[:-1]
        outputText += ");\n"

        if chipData.hdlName != "Out" and chipData.hdlName != "Splitter":
            finalOutput += outputText
    return finalOutput

globalOutput = "" 
def parseScope(scopeId):
    global globalOutput
    if not allScopes[scopeId].parsed:
        allScopes[scopeId].parsed = True

        scopeName = allScopes[scopeId].scopeData['name']

        uniqueId = 0
        for key in allScopes[scopeId].scopeData.keys():
            gateList = allScopes[scopeId].scopeData[key]     
            if key in gateNames:
                for gate in gateList:
                    bitDepth = 1
                    if key == "Splitter":
                        bitDepth = 0
                    elif key == "NotGate":
                        bitDepth = int(gate['customData']['constructorParamaters'][1])
                    else:
                        bitDepth = int(gate['customData']['constructorParamaters'][2])
                    allScopes[scopeId].nodes.append(Node(gate['label'], int(gateNames[key]), uniqueId, getOutputIds(gate), getInputIds(gate), bitDepth))
                    uniqueId += 1
            elif key == 'Multiplexer':
                for gate in gateList:
                    bitDepth = int(gate['customData']['constructorParamaters'][1])
                    inputIds = getInputIds(gate)
                    gateName = "Mux"

                    if len(inputIds) == 4:
                        gateName = "Mux4Way"
                    elif len(inputIds) == 8:
                        gateName = "Mux8Way"

                    inputIds.append(gate['customData']['nodes']['controlSignalInput'])
                    allScopes[scopeId].nodes.append(Node(gate['label'], int(gateNames[gateName]), uniqueId, getOutputIds(gate), inputIds, bitDepth))
                    uniqueId += 1
            elif key == 'Input':
                for gate in gateList:
                    allScopes[scopeId].nodes.append(Node(gate['label'], -1, uniqueId, getOutputIds(gate), [], int(gate['customData']['constructorParamaters'][1])))
                    allScopes[scopeId].inputNodes.append(uniqueId)
                    uniqueId += 1
            elif key == 'Output':
                for gate in gateList:
                    allScopes[scopeId].nodes.append(Node(gate['label'], 6, uniqueId, [], getInputIds(gate), int(gate['customData']['constructorParamaters'][1])))
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
                        allScopes[scopeId].nodes.append(Node("", chipId, uniqueId, getOutputIds(subcircuit), getInputIds(subcircuit), 1))
                        uniqueId += 1

        # create a new chip for this subcircuit
        newChip = Chip("", -1, [], [], 1)
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

        ioId = 0
        finalOutput = "Definition for " + scopeName + ":\n\n"
        toReplace = {}
        for output in allScopes[scopeId].outputNodes:
            outputNode = getNodeFromId(scopeId, output)
            finalOutput += buildHDL(scopeId, outputNode, toReplace)

            if outputNode.label == "":
                newChip.outputNames.append(chr(ord('a') + ioId))
            else:
                newChip.outputNames.append(outputNode.label)
            ioId += 1

        if smartNaming:
            for i in range(0, 2): # do it twice to make sure in/out both get replaced
                for replacing in toReplace.keys():
                    finalOutput = finalOutput.replace(replacing, toReplace[replacing])

        finalOutput += "\n\n"
        globalOutput += finalOutput

        chips.append(newChip)


for scope in scopes:
    allScopes.append(Scope(scope, False))

success = True
mainScopeId = 0
if entrypointName != "":
    mainScopeId = getScopeIdFromName(entrypointName)
else:
    mainScopeId = getScopeIdFromName("Main")

if mainScopeId == -1:
    success = False
    print("Circuit not found, ending program.")
else:
    parseScope(mainScopeId)

clear = '\n' * 100

if success: 
    print(clear)
    print(globalOutput)
