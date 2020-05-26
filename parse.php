<?php
ini_set('display_errors', 'stderr');
define("varRegex", "/[GLT]F@[a-zA-Z_\-$&%*!?][0-9a-zA-Z_\-$&%*!?]*/");
define("lineRegex", "/[^#]*/");
define("typeRegex", '/^(int|string|bool)$/');
define("labelRegex", "/^[a-zA-Z_\-$&%*!?][0-9a-zA-Z_\-$&%*!?]*$/");

define("nilRegex", "/^nil@nil$/");
define("intRegex", "/int@[+-]?\d+/");
define("boolRegex", "/bool@(true|false)/");
define("strRegex", "/^string@([^\s#\\\\]|(\\\\\d{3}))*$/"); // nemelo by tu byt + misto * ?

$instOrder = 1;
$opCode = "TEMP";
$xml = new SimpleXMLElement("<?xml version=\"1.0\" encoding=\"utf-8\" ?><program language=\"IPPcode20\"></program>");
$stats = false;
$fileName = "TEMP NAME";
$statArgs = array();
$loc = 0;
$comment = 0;
$labels = 0;
$jumps = 0;
$needStats = false;

// kontrola argumentu
function checkArgs($argc, $argv)
{   
    global $stats, $fileName, $statArgs;    

    if (in_array("--help", $argv)) {
        if ($argc == 2) {
            echo("Skript typu filtr (parse.php v jazyce PHP 7.4) načte ze standardního vstupu zdrojový kód v IPPcode20, zkontroluje lexikální a syntaktickou správnost kódu a vypíše na standardní výstup XML reprezentaci programu dle specifikace\n");
            echo("Tento skript bude pracovat s těmito parametry:\n");
            echo("• --help vypíše na standardní výstup nápovědu skriptu. Tento parametr nelze kombinovat s žádným dalším parametrem\n");
            echo("Chybové návratové kódy specifické pro analyzátor:\n");
            echo("• 21 - chybná nebo chybějící hlavička ve zdrojovém kódu zapsaném v IPPcode20\n");
            echo("• 22 - neznámý nebo chybný operační kód ve zdrojovém kódu zapsaném v IPPcode20;\n");
            echo("• 23 - jiná lexikální nebo syntaktická chyba zdrojového kódu zapsaného v IPPcode20.\n");
            exit(0);
        }
        else {
            fprintf(STDERR, "Byly zadany spatne argumenty\n");
            exit(10);
        }
    }

    foreach ($argv as $value) {
        if ($value != "parse.php") {
            $pieces = explode("=", $value);
            if ($pieces[0] == "--stats") {
                if (!$stats) {
                   $stats = true;
                   if ($pieces[1] != '') {
                       $fileName = $pieces[1];
                   }
                   else {
                       fprintf(STDERR, "Byl zadan  argument --stats bez =file\n");
                        exit(10);
                   }
                }
                else {
                    fprintf(STDERR, "Byl zadan vickrat argument --stats\n");
                    exit(10);
                }
            }
            else {
                if ($value == "--loc" or $value == "--jumps" or $value == "--labels" or $value == "--comments") {
                    $needStats = true;
                }
                array_push($statArgs, $value);
            }
        }
    }

    if ($needStats) {
        if (!$stats) {
            fprintf(STDERR, "Byl zadan --loc, --comments, --labels nebo --jumps, ale ne parametr --stats,\n");
            exit(10);
        }
    }    
}

function addArg($opcode)
{
    global $instOrder, $xml;

    $instruction = $xml->addChild('instruction');
    $instruction->addAttribute('order', $instOrder++);
    $instruction->addAttribute('opcode', $opcode);
}

function addArg1($opcode, $value1, $type1)
{
    global $instOrder, $xml;

    $instruction = $xml->addChild('instruction');
    $instruction->addAttribute('order', $instOrder++);
    $instruction->addAttribute('opcode', $opcode);

    $instruction->arg1[0] = $value1;
    $instruction->arg1->addAttribute('type', $type1);
}

function addArg2($opcode, $value1, $type1, $value2, $type2)
{
    global $instOrder, $xml;

    $instruction = $xml->addChild('instruction');
    $instruction->addAttribute('order', $instOrder++);
    $instruction->addAttribute('opcode', $opcode);

    $instruction->arg1[0] = $value1;
    $instruction->arg1->addAttribute('type', $type1);
    $instruction->arg2[0] = $value2;
    $instruction->arg2->addAttribute('type', $type2);    
}

function addArg3($opcode, $value1, $type1, $value2, $type2, $value3, $type3)
{
    global $instOrder, $xml;

    $instruction = $xml->addChild('instruction');
    $instruction->addAttribute('order', $instOrder++);
    $instruction->addAttribute('opcode', $opcode);
    
    $instruction->arg1[0] = $value1;
    $instruction->arg1->addAttribute('type', $type1);
    $instruction->arg2[0] = $value2;
    $instruction->arg2->addAttribute('type', $type2);
    $instruction->arg3[0] = $value3;
    $instruction->arg3->addAttribute('type', $type3);    
}

function checkSymb($input1, $input2, $firstType, $firstValue)
{
    global $opCode;
    
    if (preg_match(varRegex, $input1)) {
        if (preg_match(varRegex, $input2)) { // je to promenna
            addArg3($opCode, $firstValue, $firstType, $input1, "var", $input2, "var");
        }
        elseif (preg_match(intRegex, $input2)) { // je to int
            addArg3($opCode, $firstValue, $firstType, $input1, "var", splitAfterAt($input2), "int");
        }
        elseif (preg_match(boolRegex, $input2)) { // je to bool
            addArg3($opCode, $firstValue, $firstType, $input1, "var", splitAfterAt($input2), "bool");
        }
        elseif (preg_match(nilRegex, $input2)) { // je to nil
            addArg3($opCode, $firstValue, $firstType, $input1, "var", splitAfterAt($input2), "nil");
        }
        elseif (preg_match(strRegex, $input2)) { // je to string
            addArg3($opCode, $firstValue, $firstType, $input1, "var", splitAfterAt($input2), "string");
        }
        else {
            exit(23);
        }
    }
    elseif (preg_match(intRegex, $input1)) {
        if (preg_match(varRegex, $input2)) { // je to promenna
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "int", $input2, "var");
        }
        elseif (preg_match(intRegex, $input2)) { // je to int
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "int", splitAfterAt($input2), "int");
        }
        elseif (preg_match(boolRegex, $input2)) { // je to bool
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "int", splitAfterAt($input2), "bool");
        }
        elseif (preg_match(nilRegex, $input2)) { // je to nil
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "int", splitAfterAt($input2), "nil");
        }
        elseif (preg_match(strRegex, $input2)) { // je to string
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "int", splitAfterAt($input2), "string");
        }
        else {
            exit(23);
        }
    }
    elseif (preg_match(boolRegex, $input1)) {
        if (preg_match(varRegex, $input2)) { // je to promenna
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "bool", $input2, "var");
        }
        elseif (preg_match(intRegex, $input2)) { // je to int
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "bool", splitAfterAt($input2), "int");
        }
        elseif (preg_match(boolRegex, $input2)) { // je to bool
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "bool", splitAfterAt($input2), "bool");
        }
        elseif (preg_match(nilRegex, $input2)) { // je to nil
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "bool", splitAfterAt($input2), "nil");
        }
        elseif (preg_match(strRegex, $input2)) { // je to string
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "bool", splitAfterAt($input2), "string");
        }
        else {
            exit(23);
        }
    }
    elseif (preg_match(nilRegex, $input1)) {
        if (preg_match(varRegex, $input2)) { // je to promenna
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "nil", $input2, "var");
        }
        elseif (preg_match(intRegex, $input2)) { // je to int
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "nil", splitAfterAt($input2), "int");
        }
        elseif (preg_match(boolRegex, $input2)) { // je to bool
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "nil", splitAfterAt($input2), "bool");
        }
        elseif (preg_match(nilRegex, $input2)) { // je to nil
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "nil", splitAfterAt($input2), "nil");
        }
        elseif (preg_match(strRegex, $input2)) { // je to string
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "nil", splitAfterAt($input2), "string");
        }
        else {
            exit(23);
        }
    }
    elseif (preg_match(strRegex, $input1)) {
        if (preg_match(varRegex, $input2)) { // je to promenna
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "string", $input2, "var");
        }
        elseif (preg_match(intRegex, $input2)) { // je to int
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "string", splitAfterAt($input2), "int");
        }
        elseif (preg_match(boolRegex, $input2)) { // je to bool
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "string", splitAfterAt($input2), "bool");
        }
        elseif (preg_match(nilRegex, $input2)) { // je to nil
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "string", splitAfterAt($input2), "nil");
        }
        elseif (preg_match(strRegex, $input2)) { // je to string
            addArg3($opCode, $firstValue, $firstType, splitAfterAt($input1), "string", splitAfterAt($input2), "string");
        }
        else {
            exit(23);
        }
    }
    else {
        exit(23);
    }            
}
function splitAfterAt($uid) // inspirace viz https://stackoverflow.com/questions/26274259/php-splitting-a-string-after-a-specific-string
{    
    $split = explode("@",$uid);
    return $split[1];
}

function checkRestArrs0($opCode)
{
    global $noArg;
    global $arg1symb;
    global $arg1var;
    global $arg1label;
    global $arg2vs;
    global $arg2vt;
    global $arg3vss;
    global $arg3lss;

    if (in_array(strtoupper($opCode), $arg1symb) or in_array(strtoupper($opCode), $arg1var) or in_array(strtoupper($opCode), $arg1label) or in_array(strtoupper($opCode), $arg2vs) or 
    in_array(strtoupper($opCode), $arg2vt) or in_array(strtoupper($opCode), $arg3vss) or in_array(strtoupper($opCode), $arg3lss)) {
        exit(23);
    }
    else {
        exit(22);
    }
}

function checkRestArrs1($opCode)
{
    global $noArg;
    global $arg1symb;
    global $arg1var;
    global $arg1label;
    global $arg2vs;
    global $arg2vt;
    global $arg3vss;
    global $arg3lss;

    if (in_array(strtoupper($opCode), $noArg)  or in_array(strtoupper($opCode), $arg2vs) or in_array(strtoupper($opCode), $arg2vt) or
    in_array(strtoupper($opCode), $arg3vss) or in_array(strtoupper($opCode), $arg3lss)) {
        exit(23);
    }
    else {
        exit(22);
    }
}

function checkRestArrs2($opCode)
{
    global $noArg;
    global $arg1symb;
    global $arg1var;
    global $arg1label;
    global $arg2vs;
    global $arg2vt;
    global $arg3vss;
    global $arg3lss;

    if (in_array(strtoupper($opCode), $noArg) or in_array(strtoupper($opCode), $arg1symb) or in_array(strtoupper($opCode), $arg1var) or in_array(strtoupper($opCode), $arg1label) or
    in_array(strtoupper($opCode), $arg3vss) or in_array(strtoupper($opCode), $arg3lss)) {
        exit(23);
    }
    else {
        exit(22);
    }
}

function checkRestArrs3($opCode)
{
    global $noArg;
    global $arg1symb;
    global $arg1var;
    global $arg1label;
    global $arg2vs;
    global $arg2vt;
    global $arg3vss;
    global $arg3lss;

    if (in_array(strtoupper($opCode), $noArg) or in_array(strtoupper($opCode), $arg1symb) or in_array(strtoupper($opCode), $arg1var) or in_array(strtoupper($opCode), $arg1label) or
    in_array(strtoupper($opCode), $arg2vs) or in_array(strtoupper($opCode), $arg2vt)) {
        exit(23);
    }
    else {
        exit(22);
    }
}

// main
checkArgs($argc, $argv);
$line = trim(fgets(STDIN));

while ($line[0] == '#' || $line[0] == '' ) {
    $line = trim(fgets(STDIN));
}

//  check prvni radek
preg_match("/[a-zA-Z0-9.]*/", $line, $firstLine);
$test=strcasecmp($firstLine[0], ".IPPcode20");

if ($test != 0) {
    exit(21);
}

$noArg = array("CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK",);
$arg1symb = array("PUSHS", "WRITE", "EXIT", "DPRINT",);
$arg1var = array("DEFVAR", "POPS",);
$arg1label = array("CALL", "LABEL", "JUMP",);
$arg2vs = array("MOVE", "INT2CHAR", "NOT", "STRLEN", "TYPE",);
$arg2vt = array("READ",);
$arg3vss = array("ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "STRI2INT", "CONCAT", "GETCHAR", "SETCHAR",);
$arg3lss = array("JUMPIFEQ", "JUMPIFNEQ",);
$jumpsArr = array("JUMPIFEQ", "JUMPIFNEQ", "CALL", "LABEL", "JUMP",);
$usedlLabels = array();

while (!feof(STDIN)) {
    $line = trim(fgets(STDIN));
    
    if ($line === '') {
        continue;
    }

    preg_match(lineRegex, $line, $nocomment); // odstrani komentar
    if ($line != $nocomment[0]) { // pocita komentare
        $comment++;
    }
    if ($nocomment[0] === '') { // preskoci prazdny radek
        continue;
    }

    $matches = preg_split('/\s+/', $nocomment[0]);
    $opCode = strtoupper($matches[0]); // kvuli zachovani kompatibility se zbytkem kodu
    $loc++; // pocita radky kodu

    if (in_array($opCode, $jumpsArr)) { // pocita intrukce skoku
        $jumps++;
    }

    if ($opCode == "LABEL") { // pocita unikatni navesti
        if ($matches[1] != '') {
            if (!(in_array($matches[1], $usedlLabels))) {
                array_push($usedlLabels, $matches[1]);
                $labels++;
            }
        }
    }
    
    if ($matches[1] != '' and $matches[2] != '' and $matches[3] != '') { // instrukce ma tri operadny
        if (in_array(strtoupper($opCode), $arg3lss)) {    
            if (preg_match(labelRegex, $matches[1])) {                
                checkSymb($matches[2], $matches[3], "label", $matches[1]);
            }            
            else {
                exit(23);
            }
        }
        elseif (in_array(strtoupper($opCode), $arg3vss)) {
            if (preg_match(varRegex, $matches[1])) {
                checkSymb($matches[2], $matches[3], "var", $matches[1]);
            }
            else {
                exit(23);
            }
        }
        else {
            checkRestArrs3($opCode);
        }
    }
    elseif ($matches[1] != '' and $matches[2] != '' and $matches[3] == '') { // instrukce ma dva operandy
        if (in_array(strtoupper($opCode), $arg2vt)) {
            if (preg_match(varRegex, $matches[1]) && preg_match(typeRegex, $matches[2])) {                    
                addArg2($opCode, $matches[1],"var", $matches[2], "type");
            }
            else {
                exit(23);
            }            
        }
        elseif (in_array(strtoupper($opCode), $arg2vs)) {
            if (preg_match(varRegex, $matches[1])) {
                if (preg_match(varRegex, $matches[2])) { // je to promenna
                    addArg2($opCode, $matches[1],"var", $matches[2], "var");
                }
                elseif (preg_match(intRegex, $matches[2])) { // je to int
                    addArg2($opCode, $matches[1],"var", splitAfterAt($matches[2]), "int" );
                }
                elseif (preg_match(boolRegex, $matches[2])) { // je to bool
                    addArg2($opCode, $matches[1],"var", splitAfterAt($matches[2]), "bool");
                }
                elseif (preg_match(nilRegex, $matches[2])) { // je to nil
                    addArg2($opCode, $matches[1],"var", splitAfterAt($matches[2]), "nil");
                }
                elseif (preg_match(strRegex, $matches[2])) { // je to string
                    addArg2($opCode, $matches[1],"var", splitAfterAt($matches[2]), "string" );
                }
                else {
                    exit(23);
                }
            }
            else {
                exit(23);
            }
        }
        else {
            checkRestArrs2($opCode);
        }
    }
    elseif ($matches[1] != '' and $matches[2] == '' ) { // instrukce ma jeden operand
        if (in_array(strtoupper($opCode), $arg1label)) { // operand LABEL
            if (preg_match(labelRegex, $matches[1])) {
                addArg1($opCode, $matches[1],"label");
            }
            else {
                exit(23);
            }
        }
        elseif (in_array(strtoupper($opCode), $arg1var)) { // operand VAR
            if (preg_match(varRegex, $matches[1])) {
                addArg1($opCode, $matches[1],"var");
            }
            else {
                exit(23);
            }
        }
        elseif (in_array(strtoupper($opCode), $arg1symb)) { // operand SYMB
            if (preg_match(varRegex, $matches[1])) { // je to promenna
                addArg1($opCode, $matches[1],"var");
            }
            elseif (preg_match(intRegex, $matches[1])) { // je to int
                addArg1($opCode, splitAfterAt($matches[1]),"int"); 
            }
            elseif (preg_match(boolRegex, $matches[1])) { // je to bool
                addArg1($opCode, splitAfterAt($matches[1]),"bool");
            }
            elseif (preg_match(nilRegex, $matches[1])) { // je to nil
                addArg1($opCode, splitAfterAt($matches[1]),"nil");
            }
            elseif (preg_match(strRegex, $matches[1])) { // je to string
                addArg1($opCode, splitAfterAt($matches[1]),"string");
            }
            else {
                exit(23);
            }
        }
        else {
            checkRestArrs1($opCode);
        }
    }
    elseif ($matches[1] == '') { // instrukce nema operandy

        if (in_array(strtoupper($opCode), $noArg)) {
            addArg($opCode);
        }
        else {
            checkRestArrs0($opCode);
        }
    }
    else {
        checkRestArrs0($opCode);
    }
}

if ($stats) {
    $myfile = fopen($fileName, "w");
    foreach ($statArgs as $temp) {
        if ($temp == "--loc") {
            fwrite($myfile, $loc);
            fwrite($myfile, "\n");
        }
        elseif ($temp == "--comments") {
            fwrite($myfile, $comment);
            fwrite($myfile, "\n");
        }
        elseif ($temp == "--labels") {
            fwrite($myfile, $labels);
            fwrite($myfile, "\n");
        }
        elseif ($temp == "--jumps") {
            fwrite($myfile, $jumps);
            fwrite($myfile, "\n");
        }
    }
    fclose($myfile);
}

// Vypis XMLka
$dom = dom_import_simplexml($xml)->ownerDocument;
$dom->formatOutput = true;
echo $dom->saveXML();

exit(0);

?>
