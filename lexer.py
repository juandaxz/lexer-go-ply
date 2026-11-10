"""
Analizador léxico para Go (subconjunto) con PLY.
Proyecto Lenguajes de Programación - ESPOL, I Parcial.

Integrantes:
  - MALDONADO BONILLA DIEGO ALEJANDRO  (@dimaboni)
  - VILLARROEL BENITEZ VICTOR ADRIAN   (@vavillar)
  - FIERRO CARRION JUAN DIEGO          (@juandaxz)

Uso:
    python lexer.py algoritmos/algoritmo1.go [usuarioGit]

Genera un log en logs/ con el nombre:
    lexico-usuarioGit-dd-mm-aaaa-HHhMM.txt
"""
import os
import sys
from datetime import datetime

import ply.lex as lex

USUARIO_GIT = "juandaxz"  # cada integrante usa su usuario (o lo pasa como 2.º argumento)

# ============================================================
# Estado compartido
# ============================================================
errores = []

# Tokens tras los cuales un salto de línea inserta ';' (regla de Go)
TOKENS_PUNTO_COMA = {
    "ID", "ENTERO", "FLOTANTE", "CADENA", "RUNA", "TRUE", "FALSE", "NIL", "TIPO",
    "BREAK", "CONTINUE", "RETURN", "FALLTHROUGH",
    "INCREMENTO", "DECREMENTO", "RPAREN", "RBRACKET", "RBRACE",
}

# ============================================================
# Palabras reservadas: las 25 de Go, repartidas entre los integrantes
# ============================================================
# --- MALDONADO BONILLA DIEGO ALEJANDRO (@dimaboni) ---
reservadas_maldonado = {k: k.upper() for k in
    ["for", "range", "break", "continue", "goto", "fallthrough", "defer"]}
# --- VILLARROEL BENITEZ VICTOR ADRIAN (@vavillar) ---
reservadas_villarroel = {k: k.upper() for k in
    ["var", "if", "else", "return", "func", "package", "import"]}
# --- FIERRO CARRION JUAN DIEGO (@juandaxz) ---
reservadas_fierro = {k: k.upper() for k in
    ["const", "switch", "case", "default", "map", "chan", "interface",
     "select", "struct", "type", "go"]}

reservadas = {**reservadas_maldonado, **reservadas_villarroel, **reservadas_fierro}
predeclarados = {"true": "TRUE", "false": "FALSE", "nil": "NIL"}
tipos_datos = {t: "TIPO" for t in [
    "int", "int8", "int16", "int32", "int64",
    "uint", "uint8", "uint16", "uint32", "uint64",
    "float32", "float64", "string", "bool", "rune", "byte",
]}

# ============================================================
# Lista de tokens (cada integrante agrega los suyos)
# ============================================================
tokens_maldonado = [
    "ID", "TIPO", "DEFINE",
    "LPAREN", "RPAREN", "LBRACE", "RBRACE", "LBRACKET", "RBRACKET",
    "COMMA", "SEMICOLON", "COLON", "DOT", "NEWLINE", "ERROR",
]

tokens_villarroel = [
    "SLICE_TIPO",
    "PLUS", "MINUS", "TIMES", "DIVIDE", "MOD",
    "EQ", "NEQ", "LT", "LE", "GT", "GE",
    "AND", "OR", "NOT", "CADENA", "RUNA",
]


tokens_fierro = [
    "ASSIGN", "PLUS_ASSIGN", "MINUS_ASSIGN", "TIMES_ASSIGN",
    "DIVIDE_ASSIGN", "MOD_ASSIGN",
    "INCREMENTO", "DECREMENTO", "AMPERSAND", "ELLIPSIS",
    "ENTERO", "FLOTANTE",
]

tokens = list(dict.fromkeys(
    ["NEWLINE", "ERROR"] + tokens_maldonado + tokens_villarroel + tokens_fierro
    + list(reservadas.values()) + list(predeclarados.values())
))

t_ignore = " \t\r"


def _columna(t):
    inicio = t.lexer.lexdata.rfind("\n", 0, t.lexpos) + 1
    return t.lexpos - inicio + 1


def _error(t, mensaje):
    msg = f"Error léxico (línea {t.lexer.lineno}, columna {_columna(t)}): {mensaje}"
    errores.append((t.lexer.lineno, _columna(t), msg))
    t.type = "ERROR"
    t.value = msg
    return t


def t_error(t):
    errores.append((t.lexer.lineno, _columna(t),
                    f"Error léxico (línea {t.lexer.lineno}, columna {_columna(t)}): "
                    f"el carácter '{t.value[0]}' no es válido en Go."))
    t.lexer.skip(1)


# ============================================================
# INICIO aporte: MALDONADO BONILLA DIEGO ALEJANDRO (@dimaboni)
# ============================================================
def t_ID(t):
    r"[A-Za-z_][A-Za-z0-9_]*"
    if t.value in reservadas:
        t.type = reservadas[t.value]
    elif t.value in predeclarados:
        t.type = predeclarados[t.value]
    elif t.value in tipos_datos:
        t.type = "TIPO"
    return t


def t_COMENTARIO_LINEA(t):
    r"//[^\n]*"
    pass  # se descarta


def t_COMENTARIO_BLOQUE(t):
    r"/\*(.|\n)*?\*/"
    saltos = t.value.count("\n")
    t.lexer.lineno += saltos
    if saltos:  # un comentario con saltos de línea actúa como un salto de línea
        t.type = "NEWLINE"
        return t


def t_COMENTARIO_BLOQUE_ERROR(t):
    r"/\*(.|\n)*"
    tok = _error(t, "comentario de bloque sin cerrar.")
    t.lexer.lineno += t.value.count("\n")
    return tok


def t_NEWLINE(t):
    r"\n+"
    t.lexer.lineno += len(t.value)
    return t


t_DEFINE = r":="
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LBRACE = r"\{"
t_RBRACE = r"\}"
t_LBRACKET = r"\["
t_RBRACKET = r"\]"
t_COMMA = r","
t_SEMICOLON = r";"
t_COLON = r":"
t_DOT = r"\."
# FIN aporte: MALDONADO BONILLA DIEGO ALEJANDRO
# ============================================================


# ============================================================
# INICIO aporte: VILLARROEL BENITEZ VICTOR ADRIAN (@vavillar)
# ============================================================
t_SLICE_TIPO = r"\[\]"
t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_MOD = r"%"
t_EQ = r"=="
t_NEQ = r"!="
t_LE = r"<="
t_GE = r">="
t_LT = r"<"
t_GT = r">"
t_AND = r"&&"
t_OR = r"\|\|"
t_NOT = r"!"


def t_CADENA(t):
    r'"([^"\\\n]|\\.)*"'
    return t


def t_CADENA_CRUDA(t):
    r"`[^`]*`"
    t.type = "CADENA"
    t.lexer.lineno += t.value.count("\n")
    return t


def t_CADENA_SIN_CERRAR(t):
    r'"([^"\\\n]|\\.)*'
    return _error(t, "cadena sin cerrar.")


def t_RUNA(t):
    r"'([^'\\\n]|\\.)+'"
    return t


def t_RUNA_SIN_CERRAR(t):
    r"'([^'\\\n]|\\.)*"
    return _error(t, "literal de carácter sin cerrar.")
# FIN aporte: VILLARROEL BENITEZ VICTOR ADRIAN
# ============================================================


# ============================================================
# INICIO aporte: FIERRO CARRION JUAN DIEGO (@juandaxz)
#   Asignación, ++/--, &, ..., números (y su error) y escritura del log
#   (sus palabras reservadas están en reservadas_fierro)
# ============================================================
t_PLUS_ASSIGN = r"\+="
t_MINUS_ASSIGN = r"-="
t_TIMES_ASSIGN = r"\*="
t_DIVIDE_ASSIGN = r"/="
t_MOD_ASSIGN = r"%="
t_INCREMENTO = r"\+\+"
t_DECREMENTO = r"--"
t_ASSIGN = r"="
t_AMPERSAND = r"&"
t_ELLIPSIS = r"\.\.\."


def t_FLOTANTE(t):
    r"(\d+\.\d*([eE][+-]?\d+)?|\.\d+([eE][+-]?\d+)?|\d+[eE][+-]?\d+)(?![A-Za-z0-9_.])"
    t.value = float(t.value)
    return t


def t_ENTERO(t):
    r"(0[xX][0-9a-fA-F]+|0[bB][01]+|0[oO][0-7]+|\d+)(?![A-Za-z0-9_.])"
    t.value = int(t.value, 0) if t.value[:2].lower() in ("0x", "0b", "0o") else int(t.value)
    return t


def t_NUMERO_MAL_FORMADO(t):
    r"\d[A-Za-z0-9_.]*"
    return _error(t, f"número mal formado '{t.value}'.")


def escribir_log(tokens_lista, archivo_fuente, usuario):
    os.makedirs("logs", exist_ok=True)
    ahora = datetime.now()
    nombre = f"lexico-{usuario}-{ahora.strftime('%d-%m-%Y-%Hh%M')}.txt"
    ruta = os.path.join("logs", nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"Analisis lexico de: {archivo_fuente}\n")
        f.write(f"Usuario: {usuario}   Fecha: {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write("=" * 60 + "\n")
        f.write("TOKENS RECONOCIDOS\n")
        f.write("=" * 60 + "\n")
        for t in tokens_lista:
            if t.type != "ERROR":
                f.write(f"Linea {t.lineno:>3} | {t.type:<14} | {t.value!r}\n")
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"ERRORES LEXICOS ({len(errores)})\n")
        f.write("=" * 60 + "\n")
        for _, _, msg in errores:
            f.write(msg + "\n")
        if not errores:
            f.write("(sin errores)\n")
    return ruta
# FIN aporte: FIERRO CARRION JUAN DIEGO
# ============================================================

lexer = lex.lex()


def tokenizar(codigo):
    """Devuelve la lista de tokens, insertando ';' automático como Go."""
    errores.clear()
    lexer.lineno = 1
    lexer.input(codigo)
    ultimo = None
    resultado = []
    while True:
        tok = lexer.token()
        if tok is None:
            break
        if tok.type == "NEWLINE":
            if ultimo in TOKENS_PUNTO_COMA:
                tok.type, tok.value = "SEMICOLON", ";"
                resultado.append(tok)
            ultimo = None
            continue
        resultado.append(tok)
        if tok.type != "ERROR":
            ultimo = tok.type
    if ultimo in TOKENS_PUNTO_COMA:  # fin de archivo
        fin = lex.LexToken()
        fin.type, fin.value, fin.lineno, fin.lexpos = "SEMICOLON", ";", lexer.lineno, len(codigo)
        resultado.append(fin)
    return resultado


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python lexer.py archivo.go [usuarioGit]")
        sys.exit(1)
    fuente = sys.argv[1]
    usuario = sys.argv[2] if len(sys.argv) > 2 else USUARIO_GIT
    with open(fuente, encoding="utf-8") as f:
        codigo = f.read()
    lista = tokenizar(codigo)
    ruta = escribir_log(lista, fuente, usuario)
    print(f"{len(lista)} tokens, {len(errores)} errores -> {ruta}")