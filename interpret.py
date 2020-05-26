import re
import getopt
import sys
import xml.etree.ElementTree as ET

class MyInstruction:
    def __init__(self, order, opcode, argcount, arg1val = None, arg1type = None, arg2val = None, arg2type = None,arg3val = None, arg3type = None):
        self.order = order
        self.opcode = opcode
        self.argcount = argcount
        self.arg1val = arg1val
        self.arg1type = arg1type
        self.arg2val = arg2val
        self.arg2type = arg2type
        self.arg3val = arg3val
        self.arg3type = arg3type

    def printAll(obj):
        print('order: ', obj.order)
        print('opcode: ', obj.opcode)
        print('argcount: ', obj.argcount)
        print('arg1type: ', obj.arg1type)
        print('arg1val: ', obj.arg1val)
        print('arg2type: ', obj.arg2type)
        print('arg2val: ', obj.arg2val)
        print('arg3type: ', obj.arg3type)
        print('arg3val: ', obj.arg3val)
        print('\n')

class MyVar:
    def __init__(self, id, type = None, value = None):
        self.id = id
        self.type = type
        self.value = value
    
    def print(self):
        print("id:", self.id)
        print("type:", self.type)
        print("value:", self.value)

class MyLabel:
    def __init__(self, id, position):
        self.id = id
        self.position = position
    
    def print(self):
        print("id: ", self.id)
        print("position: ", self.position)

def printHelp():
    print("Program načte XML reprezentaci programu a tento program s využitím vstupu dle parametrů příkazové řádky interpretuje a generuje výstup.")
    print()
    print("Tento skript bude pracovat s těmito parametry:")
    print("--help Napise napovedu (napise toto)")
    print("--source=file vstupní soubor s XML reprezentací zdrojového kódu")
    print("--input=file soubor se vstupy pro samotnou interpretaci zadaného zdrojového kódu.")
    print("Alespoň jeden z parametrů (--source nebo --input) musí být vždy zadán. Pokud jeden z nich chybí, tak jsou odpovídající data načítána ze standardního vstupu")
    print()
    print("Chybové návratové kódy specifické pro interpret:")
    print("31 - chybný XML formát ve vstupním souboru")
    print("32 - neočekávaná struktura XML či lexikální nebo syntaktická chyba textových elementů a atributů ve vstupním XML souboru")

def parseConst(arg): # Rozdeli konstantu nebo promennou podle @ na dva stringy
    data = arg.split("@")
    return data[0], data[1]

def saveVar(var, type = None, value = None):
    frame, id = parseConst(var)
    if frame == "GF":
        for obj in globalFrame:
            if obj.id == id:
                obj.type = type
                obj.value = value
                break       
        else:
            raise ValueError("List argument missing terminal flag.")
    elif frame == "LF":
        if not LFflag:
            raise NameError

        topLocal = localFrame.pop()        

        for obj in topLocal:
            if obj.id == id:
                obj.type = type
                obj.value = value
                localFrame.append(topLocal)
                break       
        else:
            raise ValueError("List argument missing terminal flag.")
    elif frame == "TF":
        if not TFflag:
            raise NameError

        for obj in tempFrame:
            if obj.id == id:
                obj.type = type
                obj.value = value
                break       
        else:
            raise ValueError("List argument missing terminal flag.")
    else:
        pass
 
def findVar(var): # vrati typ a hodnotu hledane promenne, pokud nenalezne, vyhodi vyjimku
    frame, id = parseConst(var)
    if frame == "GF":
        for obj in globalFrame:
            if obj.id == id:
                return obj.type, str(obj.value)
        else:
            raise ValueError("Prommena v ramci neni")
    elif frame == "LF":
        if not LFflag:
            raise NameError("neni inicializovany dany ramec")

        topLocal = localFrame.pop()
        localFrame.append(topLocal)

        for obj in topLocal:
            if obj.id == id:
                return obj.type, str(obj.value)
        else:
            raise ValueError("Prommena v ramci neni")        
        
    elif frame == "TF":
        if not TFflag: # ramec neexistuje
            raise NameError("neni inicializovany dany ramec")

        for obj in tempFrame:
            if obj.id == id:
                return obj.type, str(obj.value)
        else:
            raise ValueError("Prommena v ramci neni")
    else:
        exit(32)

def jumpToFind(number): # vrati index instrukce v listu instrukci (ten nemusi odpovidat parametru order)
    for temp in my_instructions:
        if temp.order == number:
            index = my_instructions.index(temp)
            return index
    else:
        pass

def auxjump(value): # skoci na instrukci na danem indexu
    order = 0
    for target in labelList:
        if target.id == value:
            order = target.position
            break
    else:
        exit(52)
    startPosition = jumpToFind(order)
    iterate(startPosition)

def preProcess(): # projde XML a ulozi vsechny labely. Detekuje take neznamy opcode
    for obj in my_instructions:
        if obj.opcode.upper() == "LABEL":
            for target in labelList:
                if target.id == obj.arg1val:
                    exit(52)

            label = MyLabel(obj.arg1val ,obj.order)
            labelList.append(label)
        elif obj.opcode.upper() in opcodeList:
            pass
        else:
            exit(32)

def iterate(number = 0): # vlastni interpretace
    if number >= len(my_instructions):
        exit(0)
    for obj in my_instructions[int(number):]:
        global instructionIndex
        global TFflag
        global LFflag
        instructionIndex += 1
        global localFrame
        global tempFrame
       
        if obj.opcode.upper() == "MOVE": # podle opcodu spadne do spravne instrukce
            if obj.arg3type != None: # kotrola, zda instrukce nema vic argumentsu, nez ma mit
                exit(32)

            try:
                if obj.arg2type == "var":
                    typ, value = parseConst(obj.arg1val)            
                    saveVar(obj.arg1val, "var", value)
                elif obj.arg2type == "string":
                    saveVar(obj.arg1val, "string", obj.arg2val)
                elif obj.arg2type == "int":
                    saveVar(obj.arg1val, "int", obj.arg2val)
                elif obj.arg2type == "bool":
                    saveVar(obj.arg1val, "bool", obj.arg2val)
                elif obj.arg2type == "nil":
                    saveVar(obj.arg1val, "nil", obj.arg2val)
                else:
                    exit(32)
            except ValueError:
                exit(54)
            except NameError:
                exit(55)
            except:
                exit(32)

        elif obj.opcode.upper() == "CREATEFRAME":
            if obj.arg1type != None:
                exit(32)

            TFflag = True
            tempFrame.clear()

        elif obj.opcode.upper() == "PUSHFRAME":
            if obj.arg1type != None:
                exit(32)           

            if TFflag:
                LFflag = True
                localFrame.append(tempFrame[:]) # append kopie tempFrame, ne referenci
                TFflag = False
            else:
                exit(55)
        elif obj.opcode.upper() == "POPFRAME": 
            if obj.arg1type != None:
                exit(32)

            if localFrame:
                TFflag = True
                tempFrame = localFrame.pop()                
            else:
                exit(55)           

        elif obj.opcode.upper() == "DEFVAR":
            if obj.arg2type != None:
                exit(32)

            try:
                frame, id = parseConst(obj.arg1val)
            except:
                exit(32)
            

            if frame == 'GF':
                for var in globalFrame: #Opakovaná definice proměnné již existující v daném rámci vede na chybu 52.
                    if var.id == id:
                        exit(52)

                var = MyVar(id)
                globalFrame.append(var)
            elif frame == "LF":
                if not LFflag:
                    exit(55)

                topLocal = localFrame.pop()

                for var in topLocal: #Opakovaná definice proměnné již existující v daném rámci vede na chybu 52.
                    if var.id == id:
                        exit(52) # zapis do LF, ten ale neni vytvoren

                var = MyVar(id)
                topLocal.append(var)
                localFrame.append(topLocal)
                    
            elif frame == "TF":
                if not TFflag:
                    exit(55) # zapis do TF, ten ale neni vytvoren

                for var in tempFrame: #Opakovaná definice proměnné již existující v daném rámci vede na chybu 52.
                    if var.id == id:
                        exit(52)

                var = MyVar(id)
                tempFrame.append(var)
            else:
                exit(32)

        elif obj.opcode.upper() == "CALL":
            if obj.arg2type != None:
                exit(32)

            callStack.append(jumpToFind(obj.order) + 1)
            auxjump(obj.arg1val)
        elif obj.opcode.upper() == "RETURN":
            if obj.arg1type != None:
                exit(32)

            if callStack: # kontrola, zda v zasobniku volani je nejaka hodnota
                temp = callStack.pop()
                iterate(temp)
            else:
                exit(56)            

        elif obj.opcode.upper() == "PUSHS":
            if obj.arg2type != None:
                exit(32)

            var = MyVar("ID", obj.arg1type, obj.arg1val)
            dataStack.append(var)
        elif obj.opcode.upper() == "POPS":
            if obj.arg2type != None:
                exit(32)

            if dataStack: # kontrola, zda na datovem zasobniku je nejaka hodnota
                var = dataStack.pop()
                saveVar(obj.arg1val, var.type, var.value)
            else:
                exit(56)
        elif obj.opcode.upper() in aritList: # priprava hodnot je shodna pro vsechny aritmeticke instrukce
            op1 = None
            op2 = None

            if obj.arg2type == "int":
                if obj.arg3type == "int":
                    op1 = obj.arg2val
                    op2 = obj.arg3val
                elif obj.arg3type == "var":
                    op1 = obj.arg2val
                    typ, op2 = findVar(obj.arg3val)
                    if typ != "int":
                        exit(53)                    
                else:
                    exit(53)
            elif obj.arg2type == "var":
                if obj.arg3type == "int":                    
                    op2 = obj.arg3val
                    typ, op1 = findVar(obj.arg2val)
                    if typ != "int":
                        exit(53)
                elif obj.arg3type == "var":
                    typ1, op1 = findVar(obj.arg2val)
                    if typ1 != "int":
                        exit(53)                    
                    typ2, op2 = findVar(obj.arg3val)
                    if typ2 != "int":
                        exit(53)
                else:
                    exit(53)
            else:
                exit(53)

            if obj.arg1type != "var":
                exit(53)

            try:
                op1 = int(op1)
                op2 = int(op2)
            except:
                exit(32)
            
            if obj.opcode.upper() == "ADD": # z pripravencyh hodnot dokoncime spravnou instrukci
                saveVar(obj.arg1val, "int", op1 + op2)
            elif obj.opcode.upper() == "SUB":
                saveVar(obj.arg1val, "int", op1 - op2)  
            elif obj.opcode.upper() == "MUL":
                saveVar(obj.arg1val, "int", op1 * op2)
            elif obj.opcode.upper() == "IDIV":
                if op2 == 0:
                    exit(57)
                saveVar(obj.arg1val, "int", op1 / op2)

        elif obj.opcode.upper() == "LT" or obj.opcode.upper() == "GT" or obj.opcode.upper() == "EQ":
            # priprava hodnot pro relacni funkce je stejna
            nilFlag = False

            if obj.arg2type == "var":
                typ1, op1 = findVar(obj.arg2val)
            else:
                typ1 = obj.arg2type
                op1 = obj.arg2val

            if obj.arg3type == "var":
                typ2, op2 = findVar(obj.arg3val)
            else:
                typ2 = obj.arg3type
                op2 = obj.arg3val

            if typ1 == "nil" or typ2 == "nil":
                nilFlag = True

            if not nilFlag:
                if typ1 != typ2:
                    exit(53)             
            
            # dokoncime pouze zadanou instrukci
            if obj.opcode.upper() == "LT":
                if nilFlag:
                    exit(53)                
                saveVar(obj.arg1val, "bool", str(op1 < op2).lower())
                
            elif obj.opcode.upper() == "GT":
                if nilFlag:
                    exit(53)
                saveVar(obj.arg1val, "bool", str(op1 > op2).lower())
                
            elif obj.opcode.upper() == "EQ":
                saveVar(obj.arg1val, "bool", str(op1 == op2).lower())

        elif obj.opcode.upper() == "AND" or obj.opcode.upper() == "OR":
            # AND a OR maji taky stejnou pripravu hodnot
            if obj.arg2type == "var":
                if obj.arg3type == "var":
                    typ1, value1 = findVar(obj.arg2val)
                    if typ1 == "bool":
                        if value1.lower() == "true":
                            op1 = True
                        else:
                            op1 = False
                    else:
                        pass

                    typ2, value2 = findVar(obj.arg3val)
                    if typ2 == "bool":
                        if value2.lower() == "true":
                            op2 = True
                        else:
                            op2 = False
                    else:
                        pass
                    
                elif obj.arg3type == "bool":
                    typ1, value1 = findVar(obj.arg2val)
                    if typ1 == "bool":
                        if value1.lower() == "true":
                            op1 = True
                        else:
                            op1 = False
                    else:
                        pass

                    if obj.arg3val.lower() == "true":
                        op2 = True
                    else:
                        op2 = False
                else:
                    pass
            elif obj.arg2type == "bool":
                if obj.arg3type == "var":
                    if obj.arg2type.lower() == "true":
                        op1 = True
                    else:
                        op1 = False

                    typ, value = findVar(obj.arg3val)
                    if typ == "bool":
                        if value.lower() == "true":
                            op2 = True
                        else:
                            op2 = False
                    else:
                        pass
                    
                elif obj.arg3type == "bool":
                    if obj.arg2val.lower() == "true":
                        op1 = True
                    else:
                        op1 = False

                    if obj.arg3val.lower() == "true":
                        op2 = True
                    else:
                        op2 = False
                else:
                    pass
            else:
                pass

            if obj.opcode.upper() == "OR":
                saveVar(obj.arg1val, "bool", str(op1 or op2).lower())
            else:
                saveVar(obj.arg1val, "bool", str(op1 and op2).lower())

        elif obj.opcode.upper() == "NOT": # NOT ma pouze 2 operandy
            if obj.arg3type != None:
                exit(32)

            if obj.arg2type == "bool":
                if obj.arg2val.lower() == "true":
                    op1 = True
                else:
                    op1 = False
            elif obj.arg2type == "var":
                typ1, value1 = findVar(obj.arg2val)
                if typ1 == "bool":
                    if value1.lower() == "true":
                        op1 = True
                    else:
                        op1 = False
                else:
                    pass            
            else:
                pass

            saveVar(obj.arg1val, "bool", str(not op1).lower())

        elif obj.opcode.upper() == "INT2CHAR":
            if obj.arg3type != None:
                exit(32)

            if obj.arg2type == "int":
                try:
                    temp = chr(int(obj.arg2val))
                except:
                    exit(58)

                saveVar(obj.arg1val, "string", temp)
            
            elif obj.arg2type == "var":
                typ1, value1 = findVar(obj.arg2val)
                if typ1 == "int":
                    try:
                        temp = chr(int(value1))
                    except:
                        exit(58)

                    saveVar(obj.arg1val, "string", temp)
                else:
                    pass           

            
        elif obj.opcode.upper() == "STRI2INT":
            if obj.arg2type == "string":
                string = obj.arg2val
            elif obj.arg2type == "var":
                typ1, value1 = findVar(obj.arg2val)
                if typ1 == "string":
                    string = value1
                else:
                    pass
            else:
                pass

            if obj.arg3type == "int":
                position = obj.arg3val
            elif obj.arg3type == "var":
                typ1, value1 = findVar(obj.arg3val)
                if typ1 == "int":
                    position = value1
                else:
                    pass

            try:
                temp = ord(string[int(position)])
            except:
                exit(58)

            saveVar(obj.arg1val, "int", str(temp))

        elif obj.opcode.upper() == "READ":
            if obj.arg3type != None:
                exit(32)

            sys.stdin = input_file
            temp = input()
            sys.stdin = backup_stdin

            if obj.arg2val == "int":
                saveVar(obj.arg1val, "int", temp )
            elif obj.arg2val == "string":
                saveVar(obj.arg1val, "string", temp)
            elif obj.arg2val == "bool":
                if temp.upper()  ==  "TRUE":
                    saveVar(obj.arg1val, "bool", "true")
                else:
                    saveVar(obj.arg1val, "bool", "false")                
            else:
                saveVar(obj.arg1val, "nil")
            
        elif obj.opcode.upper() == "WRITE":
            if obj.arg2type != None:
                exit(32)

            if obj.arg1type == "var":
                try:
                    typ, val = findVar(obj.arg1val)
                except ValueError:
                    exit(54) # ramec exituje, ale prommena ne
                except NameError:
                    exit(55) # neexituje ramec
                
                if typ == "int":
                    print(int(float(val)), end='')
                else:
                    print(val, end='')

            elif obj.arg1type == "string":
                matches = re.split(r'(\\\d{3})', obj.arg1val) # rozdeleni na string a escape sekvence
                for match in matches:
                    if match == "":
                        pass
                    elif match[0] == "\\":
                        temp = int(match[1:]) # escape sekvenci musime prevest pomoci chr()
                        print(chr(temp), end = '')
                    else: # string zapiseme primo
                        print(match, end = '')
            elif obj.arg1type == "int" or obj.arg1type == "bool": # int a bool mozeme napsat primo
                print(obj.arg1val, end = '')
            elif obj.arg1type == "nil": # nil se vypise jako prazdny string
                print("", end= '')
            else:
                exit(32)

        elif obj.opcode.upper() == "CONCAT":
            if obj.arg2type == "string":
                if obj.arg3type == "string":
                    op1 = obj.arg2val
                    op2 = obj.arg3val
                elif obj.arg3type == "var":
                    op1 = obj.arg2val
                    typ1, value1 = findVar(obj.arg3val)
                    if typ1 == "string":
                        op2 = value1
                    else:
                        pass
                else:
                    pass

            elif obj.arg2type == "var":
                if obj.arg3type == "string":
                    op2 = obj.arg3val
                    typ1, value1 = findVar(obj.arg2val)
                    if typ1 == "string":
                        op1 = value1
                    else:
                        pass

                elif obj.arg3type == "var":
                    typ1, value1 = findVar(obj.arg2val)
                    if typ1 == "string":
                        op1 = value1
                    else:
                        pass
                    typ2, value2 = findVar(obj.arg3val)
                    if typ2 == "string":
                        op2 = value2
                    else:
                        pass
                else:
                    pass

            saveVar(obj.arg1val, "string", str(op1 + op2))

        elif obj.opcode.upper() == "STRLEN":
            if obj.arg3type != None:
                exit(32)

            if obj.arg2type == "string":
                op1 = obj.arg2val
            elif obj.arg2type == "var":
                typ1, value1 = findVar(obj.arg2val)
                if typ1 == "string":
                    op1 = value1
                else:
                    pass
            else:
                pass

            saveVar(obj.arg1val, "int", str(len(op1)))

        elif obj.opcode.upper() == "GETCHAR":
            if obj.arg2type == "string":
                string = obj.arg2val
            elif obj.arg2type == "var":
                typ1, value1 = findVar(obj.arg2val)
                if typ1 == "string":
                    string = value1
                else:
                    pass
            else:
                pass

            if obj.arg3type == "int":
                position = obj.arg3val
            elif obj.arg3type == "var":
                typ1, value1 = findVar(obj.arg3val)
                if typ1 == "int":
                    position = value1
                else:
                    pass
                   
            try:
                temp = string[int(position)]
            except:
                exit(58)

            saveVar(obj.arg1val, "string", temp)

        elif obj.opcode.upper() == "SETCHAR":
            typ, value = findVar(obj.arg1val)
            if typ == "string":
                string = value
            else:
                pass

            if obj.arg2type == "int":
                position = obj.arg2val
            elif obj.arg2type == "var":
                typ, value = findVar(obj.arg2val)
                if typ == "int":
                    position = value
                else:
                    pass
            else:
                pass

            if obj.arg3type == "string":
                char = obj.arg3val
            elif obj.arg3type == "var":
                typ, value = findVar(obj.arg2val)
                if typ == "string":
                    char = value
                else:
                    pass

            if len(char) < 1:
                exit(58)
            
            if len(char) > 1:
                char = char[0]          

            position = int(position)

            newString = string[:position] + char + string[position +1:]
            saveVar(obj.arg1val, "string", newString)

        elif obj.opcode.upper() == "TYPE":
            if obj.arg2type == "var":
                typ, val = parseConst(obj.arg2val)
                try:
                    typ, val = findVar(val)
                    saveVar(obj.arg1val, "string" ,typ)
                except:
                    saveVar(obj.arg1val, "string" ,"")
            elif obj.arg2type == "int":
                saveVar(obj.arg1val, "string" ,"int")
            elif obj.arg2type == "bool":
                saveVar(obj.arg1val, "string" ,"bool")
            elif obj.arg2type == "string":
                saveVar(obj.arg1val, "string" ,"string")
            elif obj.arg2type == "nil":
                saveVar(obj.arg1val, "string" ,"nil")
            else:
                pass
    
        elif obj.opcode.upper() == "LABEL":
            if obj.arg2type != None:
                exit(32)
            else:
                pass # deklarace uz bude ignorovana (byla zpracovana pomoci funkce preProcess)

        elif obj.opcode.upper() == "JUMP":
            if obj.arg2type != None:
                exit(32)

            auxjump(obj.arg1val)
            break #pri navratu ze skoku uz nesmime pokracovat i interpretaci, vsechno jsme uz provedli
        elif obj.opcode.upper() == "JUMPIFEQ":
            jumped = False
            if obj.arg2type == "var":
                if obj.arg3type == "var": # oba jsou "var"
                    typ2, val2 = findVar(obj.arg2val)
                    typ3, val3 = findVar(obj.arg3val)
                    if typ2 == typ3:
                        if val2 == val3:
                            jumped = True
                            auxjump(obj.arg1val)
                        else: # nejsou stejne hodnoty
                            pass
                    else: # nejsou stejne typy
                        pass
                else: # jenom jeden je "var"
                    typ, val = findVar(obj.arg2val)
                    if typ == obj.arg3type:
                        if val == obj.arg3val:
                            jumped = True
                            auxjump(obj.arg1val)
                        else: # nejsou stejne hodnoty
                            pass
                    else: # nejsou stejne typy
                        pass

            elif obj.arg3type == "var":
                if obj.arg2type == "var": # oba jsou "var"
                    typ2, val2 = findVar(obj.arg2val)
                    typ3, val3 = findVar(obj.arg3val)
                    if typ2 == typ3:
                        if val2 == val3:
                            jumped = True
                            auxjump(obj.arg1val)
                        else: # nejsou stejne hodnoty
                            pass
                    else: # nejsou stejne typy
                        pass
                else: # jenom jeden je "var"
                    typ, val = findVar(obj.arg3val)
                    if typ == obj.arg2type:
                        if val == obj.arg2val:
                            jumped = True
                            auxjump(obj.arg1val)
                        else: # nejsou stejne hodnoty
                            pass
                    else: # nejsou stejne typy
                        pass

            elif obj.arg2type == "nil":
                jumped = True
                auxjump(obj.arg1val)
            elif obj.arg3type == "nil":
                jumped = True
                auxjump(obj.arg1val)
                
            elif obj.arg2type == obj.arg3type:
                if obj.arg2val == obj.arg3val:
                    jumped = True
                    auxjump(obj.arg1val)                    
                else:
                    pass
            else:
                exit(32)

            if jumped:
                break

        elif obj.opcode.upper() == "JUMPIFNEQ":
            jumped = False
            if obj.arg2type == "var":
                if obj.arg3type == "var": # oba jsou "var"
                    typ2, val2 = findVar(obj.arg2val)
                    typ3, val3 = findVar(obj.arg3val)
                    if typ2 == typ3:
                        if val2 == val3:
                            pass
                        else: # nejsou stejne hodnoty
                            jumped = True
                            auxjump(obj.arg1val)
                    else: # nejsou stejne typy
                        pass
                else: # jenom jeden je "var"
                    typ, val = findVar(obj.arg2val)
                    if typ == obj.arg3type:
                        if val == obj.arg3val:
                            pass
                        else: # nejsou stejne hodnoty
                            jumped = True
                            auxjump(obj.arg1val)
                    else: # nejsou stejne typy
                        pass

            elif obj.arg3type == "var":
                if obj.arg2type == "var": # oba jsou "var"
                    typ2, val2 = findVar(obj.arg2val)
                    typ3, val3 = findVar(obj.arg3val)
                    if typ2 == typ3:
                        if val2 == val3:
                            pass
                        else: # nejsou stejne hodnoty
                            jumped = True
                            auxjump(obj.arg1val)
                    else: # nejsou stejne typy
                        pass
                else: # jenom jeden je "var"
                    typ, val = findVar(obj.arg3val)
                    if typ == obj.arg2type:
                        if val == obj.arg2val:
                            pass
                        else: # nejsou stejne hodnoty
                            jumped = True
                            auxjump(obj.arg1val)
                    else: # nejsou stejne typy
                        pass
                    
            elif obj.arg2type == "nil":
                jumped = True
                auxjump(obj.arg1val)
            elif obj.arg3type == "nil":
                jumped = True
                auxjump(obj.arg1val)
            elif obj.arg2type == obj.arg3type:
                if obj.arg2val == obj.arg3val:
                    pass
                else:
                    jumped = True
                    auxjump(obj.arg1val)
            else:
                exit(32) 

            if jumped:
                break

        elif obj.opcode.upper() == "EXIT":
            if obj.arg2type != None:
                exit(32)

            if obj.arg1type == "var":
                typ, value = findVar(obj.arg1type)
                if typ == "int":
                    try:
                        exit_code = int(value)
                    except:
                        exit(53) #spatne typy operandu

                    if 0 <= exit_code <= 49:                   
                        exit(exit_code)                    
                    else:
                        exit(57) #mimo rozsah         
                else:
                    exit(53)
            elif obj.arg1type == "int":
                try:
                    exit_code = int(obj.arg1val)
                except:
                    exit(53) #spatne typy operandu

                if 0 <= exit_code <= 49:                   
                    exit(exit_code)                    
                else:
                    exit(57) #mimo rozsah            
            else:
                exit(53)

        elif obj.opcode.upper() == "DPRINT": #nedelam (zatim) nic
            if obj.arg2type != None:
                exit(32)
            else:
                pass
        elif obj.opcode.upper() == "BREAK": #nedelam (zatim) nic 
            if obj.arg1type != None:
                exit(32)
            else:
                pass    
        else:
            exit(32)           

def getOrder(label):
    for target in labelList:
        if target.id == obj.arg1val:
            return target.position            
    else:
        exit(52)

debug = 0

globalFrame = []

TFflag = False
LFflag = False
tempFrame = []
localFrame = []

orderList = []
labelList = []
dataStack = []
callStack = []
opcodeList = ["MOVE", "CREATEFRAME", "PUSHFRAME", "POPFRAME", "DEFVAR", "CALL", "RETURN", "PUSHS", "POPS", "ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "NOT", "INT2CHAR", "STRI2INT", "READ", "WRITE", "CONCAT", "STRLEN", "GETCHAR", "SETCHAR", "TYPE", "LABEL", "JUMP", "JUMPIFEQ", "JUMPIFNEQ", "EXIT", "DPRINT", "BREAK"]
aritList = ["ADD", "SUB", "MUL", "IDIV"]

instructionIndex = -1 # zacina pocitat od -1, protoze prvni insrukce pak bude na indexu 0
my_instructions = []

options, remainder = getopt.getopt(sys.argv[1:], '', ['source=', 'help', 'input=',])

help = False
sourceFlag = False
inputFlag = False

source_filename = sys.stdin
input_file = sys.stdin
backup_stdin = sys.stdin

for opt, arg in options:
    if opt == '--help':        
        help = True        
    elif opt == '--source':
        if help:
            exit(10)
        else:
            source_filename = arg
            sourceFlag = True        
    elif opt == '--input':
        if help:
            exit(10)
        else:
            input_file = open(arg)
            inputFlag = True

if help:
    printHelp()
    exit(0)

if not sourceFlag and not inputFlag:
    exit(10) # nezadany ani sourceFlag ani inputFlag

try:
    root = ET.parse(source_filename).getroot()
except:
    exit(31)

if root.tag != "program":
    exit(32)

for child in root:
    if child.tag != "instruction":
        exit(32)

    order = child.get('order')

    try:
        orderInt = int(order)
    except: # order neni cislo
        exit(32)    

    if orderInt <= 0: # zaporny, nebo nulovy order
        exit(32)
    
    if order in orderList: # duplicitni order
        exit(32)

    orderList.append(order)

    opcode = child.get('opcode')

    if opcode == None:
        exit(32)

    argcount = len(child)
    my_args = []
    arglist = []

    for arg in child:
        if arg.tag in arglist: # opakovany argument v instrukci
            exit(32)            

        arglist.append(arg.tag)
        oneArg = (arg.tag, arg.get("type"), arg.text)
        my_args.append(oneArg)

    my_args.sort()
    
    if argcount == 0:
        instruction = MyInstruction(order, opcode, argcount)
    elif argcount == 1:
        if my_args[0][0] != "arg1":
            exit(32)
        instruction = MyInstruction(order, opcode, argcount, my_args[0][2], my_args[0][1])
    elif argcount == 2:
        if my_args[0][0] != "arg1":
            exit(32)
        if my_args[1][0] != "arg2":
            exit(32)
        instruction = MyInstruction(order, opcode, argcount, my_args[0][2], my_args[0][1], my_args[1][2], my_args[1][1])
    elif argcount == 3:
        if my_args[0][0] != "arg1":
            exit(32)
        if my_args[1][0] != "arg2":
            exit(32)
        if my_args[2][0] != "arg3":
            exit(32)
        instruction = MyInstruction(order, opcode, argcount, my_args[0][2], my_args[0][1], my_args[1][2], my_args[1][1], my_args[2][2], my_args[2][1])
    else:
        exit(32) # spatny pocet argumentu

    my_instructions.append(instruction)

my_instructions.sort(key=lambda x: int(x.order), reverse=False)

preProcess()
iterate()