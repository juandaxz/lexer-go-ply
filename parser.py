"""
Analizador sintáctico para Go (subconjunto) con PLY (yacc).
Proyecto Lenguajes de Programación - ESPOL, avance 2.

Integrantes:
- MALDONADO BONILLA DIEGO ALEJANDRO (@dimaboni)
- VILLARROEL BENITEZ VICTOR ADRIAN (@vavillar)
- FIERRO CARRION JUAN DIEGO (@juandaxz)

Uso:
    python parser.py algoritmos/algoritmoSintactico1.go [usuarioGit]

Genera un log en logs/ con el nombre:
    sintactico-usuarioGit-dd-mm-aaaa-HHhMM.txt
"""

import os
import sys
from datetime import datetime

import ply.yacc as yacc

import lexer as lexico
from lexer import tokens  # noqa: F401  (yacc los toma de este módulo)

USUARIO_GIT = "dimaboni"  # o se pasa como 2.º argumento

errores_sintacticos = []

# ============================================================
# BASE COMPARTIDA (la usan las reglas de los tres integrantes):
# estructura del programa, bloques, expresiones aritméticas y
# lógicas, asignación, impresión (fmt.Println) e ingreso por
# teclado (fmt.Scanln). Lo que le corresponde a otro integrante
# lleva un comentario con su nombre.
# ============================================================

# Precedencia, de menor a mayor (como en el informe del avance 1)
precedence = (
    ("left", "OR"),
    ("left", "AND"),
    ("nonassoc", "EQ", "NEQ", "LT", "LE", "GT", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "MOD"),
    ("right", "UMINUS", "NOT"),
)


def p_programa(p):
    """programa : PACKAGE ID SEMICOLON imports declaraciones"""
    p[0] = ("programa", p[2], p[4], p[5])


def p_imports(p):
    """imports : imports IMPORT CADENA SEMICOLON
    | empty"""
    p[0] = [] if len(p) == 2 else p[1] + [p[3]]


def p_declaraciones(p):
    """declaraciones : declaraciones declaracion
    | empty"""
    p[0] = [] if len(p) == 2 else p[1] + [p[2]]


# declaraciones globales:
#   decl_func -> Maldonado
#   Villarroel: agregar aquí  decl_var SEMICOLON
#   Fierro:     agregar aquí  decl_const SEMICOLON
def p_declaracion(p):
    """declaracion : decl_func SEMICOLON"""
    p[0] = p[1]


def p_empty(p):
    """empty :"""
    p[0] = None


def p_bloque(p):
    """bloque : LBRACE sentencias RBRACE"""
    p[0] = ("bloque", p[2])


def p_sentencias(p):
    """sentencias : sentencias sentencia
    | empty"""
    p[0] = [] if len(p) == 2 else p[1] + [p[2]]


# sentencia:
#   sent_simple, sent_for, sent_salto, sent_ret -> Maldonado
#   Villarroel: agregar aquí  decl_var SEMICOLON  y  sent_if SEMICOLON
#   Fierro:     agregar aquí  decl_const SEMICOLON  y  sent_switch SEMICOLON
def p_sentencia(p):
    """sentencia : sent_simple SEMICOLON
    | sent_for SEMICOLON
    | sent_salto SEMICOLON
    | sent_ret SEMICOLON"""
    p[0] = p[1]


def p_sentencia_error(p):
    """sentencia : error SEMICOLON"""
    # recuperación: se descartan tokens hasta el próximo ';' y se sigue
    p[0] = ("error",)


# --- expresiones aritméticas y condiciones con conectores lógicos ---
def p_expresion_binaria(p):
    """expresion : expresion PLUS expresion
    | expresion MINUS expresion
    | expresion TIMES expresion
    | expresion DIVIDE expresion
    | expresion MOD expresion
    | expresion EQ expresion
    | expresion NEQ expresion
    | expresion LT expresion
    | expresion LE expresion
    | expresion GT expresion
    | expresion GE expresion
    | expresion AND expresion
    | expresion OR expresion"""
    p[0] = ("binop", p[2], p[1], p[3])


def p_expresion_unaria(p):
    """expresion : MINUS expresion %prec UMINUS
    | NOT expresion"""
    p[0] = ("unop", p[1], p[2])


def p_expresion_grupo(p):
    """expresion : LPAREN expresion RPAREN"""
    p[0] = p[2]


# acceso y arreglo_lit -> Maldonado
#   Villarroel: agregar aquí  slice_lit
#   Fierro:     agregar aquí  mapa_lit
def p_expresion_atomo(p):
    """expresion : ID
    | ENTERO
    | FLOTANTE
    | CADENA
    | RUNA
    | TRUE
    | FALSE
    | NIL
    | llamada
    | conversion
    | acceso
    | arreglo_lit"""
    p[0] = p[1]


def p_conversion(p):
    """conversion : TIPO LPAREN expresion RPAREN"""
    p[0] = ("conversion", p[1], p[3])


# --- llamadas, impresión (fmt.Println) e ingreso por teclado (fmt.Scanln) ---
def p_llamada(p):
    """llamada : ID LPAREN args RPAREN
    | ID DOT ID LPAREN args RPAREN"""
    p[0] = ("llamada", p[1] if len(p) == 5 else f"{p[1]}.{p[3]}")


def p_args(p):
    """args : args COMMA arg
    | arg
    | empty"""
    p[0] = [] if p[1] is None else ([p[1]] if len(p) == 2 else p[1] + [p[3]])


# Fierro: agregar aquí  expresion ELLIPSIS  (sumar(xs...), argumentos variables)
def p_arg(p):
    """arg : expresion
    | AMPERSAND ID"""
    p[0] = p[1] if len(p) == 2 else ("ref", p[2])


def p_lista_expr(p):
    """lista_expr : lista_expr COMMA expresion
    | expresion"""
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]


# --- asignación (=, +=, -=, *=, /=, %=) e incremento/decremento ---
def p_sent_simple_asigna(p):
    """sent_simple : ID ASSIGN expresion
    | ID PLUS_ASSIGN expresion
    | ID MINUS_ASSIGN expresion
    | ID TIMES_ASSIGN expresion
    | ID DIVIDE_ASSIGN expresion
    | ID MOD_ASSIGN expresion"""
    p[0] = ("asigna", p[2], p[1], p[3])


def p_sent_simple_incdec(p):
    """sent_simple : ID INCREMENTO
    | ID DECREMENTO"""
    p[0] = ("incdec", p[2], p[1])


def p_sent_simple_llamada(p):
    """sent_simple : llamada"""
    p[0] = p[1]


# tipos: TIPO y tipo_arreglo [n]T -> Maldonado
#   Villarroel: agregar aquí  tipo_slice  ([]T)
#   Fierro:     agregar aquí  tipo_mapa   (map[K]V)
def p_tipo(p):
    """tipo : TIPO
    | tipo_arreglo"""
    p[0] = p[1]


# ============================================================
# INICIO aporte: MALDONADO BONILLA DIEGO ALEJANDRO (@dimaboni)
# Declaración corta (:=), ciclo for, arreglo [n]T y
# función con un valor de retorno (+ break / continue)
# ============================================================

# --- declaración corta:  edad := 20 ---
def p_sent_simple_declara(p):
    """sent_simple : ID DEFINE expresion"""
    p[0] = ("declara_corta", p[1], p[3])


# --- ciclo for (las tres formas del informe + for infinito) ---
def p_sent_for_clasico(p):
    """sent_for : FOR sent_simple SEMICOLON expresion SEMICOLON sent_simple bloque"""
    p[0] = ("for_clasico", p[2], p[4], p[6], p[7])


def p_sent_for_condicion(p):
    """sent_for : FOR expresion bloque"""
    p[0] = ("for_condicion", p[2], p[3])


def p_sent_for_infinito(p):
    """sent_for : FOR bloque"""
    p[0] = ("for_infinito", p[2])


def p_sent_for_range(p):
    """sent_for : FOR ID COMMA ID DEFINE RANGE expresion bloque"""
    p[0] = ("for_range", p[2], p[4], p[7], p[8])


# break y continue -> Maldonado
#   Fierro: agregar aquí  FALLTHROUGH  (va con su switch)
def p_sent_salto(p):
    """sent_salto : BREAK
    | CONTINUE"""
    p[0] = (p[1],)


# --- arreglo:  notas := [3]int{8, 9, 10}  /  notas[0]  /  notas[0] = 5 ---
def p_tipo_arreglo(p):
    """tipo_arreglo : LBRACKET ENTERO RBRACKET TIPO"""
    p[0] = ("arreglo", p[2], p[4])


def p_arreglo_lit(p):
    """arreglo_lit : tipo_arreglo LBRACE lista_expr RBRACE"""
    p[0] = ("arreglo_lit", p[1], p[3])


def p_acceso(p):
    """acceso : ID LBRACKET expresion RBRACKET"""
    p[0] = ("acceso", p[1], p[3])


def p_sent_simple_asigna_indice(p):
    """sent_simple : ID LBRACKET expresion RBRACKET ASSIGN expresion"""
    p[0] = ("asigna_indice", p[1], p[3], p[6])


# --- función con un valor de retorno:  func cuadrado(n int) int { ... } ---
def p_decl_func(p):
    """decl_func : FUNC ID LPAREN params RPAREN tipo_ret bloque"""
    p[0] = ("func", p[2], p[4], p[6], p[7])


def p_params(p):
    """params : params COMMA param
    | param
    | empty"""
    p[0] = [] if p[1] is None else ([p[1]] if len(p) == 2 else p[1] + [p[3]])


# Fierro: agregar aquí  ID ELLIPSIS tipo  (nums ...int, argumentos variables)
def p_param(p):
    """param : ID tipo"""
    p[0] = (p[1], p[2])


# Villarroel: agregar aquí  LPAREN lista_tipos RPAREN  (varios valores de retorno)
def p_tipo_ret(p):
    """tipo_ret : tipo
    | empty"""
    p[0] = p[1]


# Villarroel: ampliar a varios valores (RETURN lista_expr)
def p_sent_ret(p):
    """sent_ret : RETURN expresion
    | RETURN"""
    p[0] = ("return", p[2] if len(p) == 3 else None)


# FIN aporte: MALDONADO BONILLA DIEGO ALEJANDRO
# ============================================================


# ============================================================
# INICIO aporte: VILLARROEL BENITEZ VICTOR ADRIAN (@vavillar)
# Declaración con var, if / else, slice []T y
# función con varios valores de retorno (return a, b)
#
# Todo: decl_var, sent_if, tipo_slice,
# slice_lit, lista_tipos, a, b := f()) y se enlazan en los puntos
# marcados con su nombre más arriba (declaracion, sentencia,
# expresion, tipo, tipo_ret, sent_ret).
# ============================================================


# FIN aporte: VILLARROEL BENITEZ VICTOR ADRIAN
# ============================================================


# ============================================================
# INICIO aporte: FIERRO CARRION JUAN DIEGO (@juandaxz)
# Constante, switch, mapa map[K]V y
# función con argumentos variables (nums ...int)
#
# Todo: decl_const, sent_switch, casos,
# tipo_mapa, mapa_lit, pares y se enlazan en los puntos marcados
# con su nombre más arriba (declaracion, sentencia, expresion,
# tipo, sent_salto, param, arg).
# ============================================================


# FIN aporte: FIERRO CARRION JUAN DIEGO
# ============================================================


def p_error(p):
    if p is None:
        msg = "Error sintáctico: fin de archivo inesperado."
        errores_sintacticos.append((0, msg))
        return
    msg = (f"Error sintáctico (línea {p.lineno}): se encontró '{p.value}' "
           f"({p.type}) y no es válido en esa posición.")
    errores_sintacticos.append((p.lineno, msg))


class _Flujo:
    """Adapta la lista de tokens del lexer (con ';' automático) a yacc."""

    def __init__(self, lista):
        # el lexer deja NEWLINE sueltos y tokens ERROR: el parser no los usa
        self.lista = [t for t in lista if t.type not in ("NEWLINE", "ERROR")]
        self.i = 0

    def token(self):
        if self.i >= len(self.lista):
            return None
        t = self.lista[self.i]
        self.i += 1
        return t

    def input(self, _):
        pass


class _LogSinAvisosDeTokens(yacc.PlyLogger):
    """Oculta solo el aviso de tokens del lexer que la gramática no usa
    (chan, defer, go, ...). Los conflictos de la gramática sí se siguen mostrando."""

    def warning(self, msg, *args, **kwargs):
        if "defined, but not used" in msg or "unused token" in msg:
            return
        super().warning(msg, *args, **kwargs)


parser = yacc.yacc(debug=False, write_tables=False,
                   errorlog=_LogSinAvisosDeTokens(sys.stderr))


def analizar(codigo):
    """Devuelve (árbol, errores léxicos, errores sintácticos)."""
    errores_sintacticos.clear()
    lista = lexico.tokenizar(codigo)
    lexicos = [m for _, _, m in lexico.errores]
    arbol = parser.parse(lexer=_Flujo(lista))
    return arbol, lexicos, list(errores_sintacticos)


def escribir_log(archivo_fuente, usuario, lexicos, sintacticos):
    os.makedirs("logs", exist_ok=True)
    ahora = datetime.now()
    nombre = f"sintactico-{usuario}-{ahora.strftime('%d-%m-%Y-%Hh%M')}.txt"
    ruta = os.path.join("logs", nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"Analisis sintactico de: {archivo_fuente}\n")
        f.write(f"Usuario: {usuario} Fecha: {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write("=" * 60 + "\n")
        f.write(f"ERRORES LEXICOS ({len(lexicos)})\n")
        f.write("=" * 60 + "\n")
        for m in lexicos:
            f.write(m + "\n")
        if not lexicos:
            f.write("(sin errores)\n")
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"ERRORES SINTACTICOS ({len(sintacticos)})\n")
        f.write("=" * 60 + "\n")
        for _, m in sintacticos:
            f.write(m + "\n")
        if not sintacticos:
            f.write("(sin errores)\n")
    return ruta


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python parser.py archivo.go [usuarioGit]")
        sys.exit(1)
    fuente = sys.argv[1]
    usuario = sys.argv[2] if len(sys.argv) > 2 else USUARIO_GIT
    with open(fuente, encoding="utf-8") as f:
        codigo = f.read()
    _, lex_err, sin_err = analizar(codigo)
    ruta = escribir_log(fuente, usuario, lex_err, sin_err)
    print(f"{len(lex_err)} errores léxicos, {len(sin_err)} sintácticos -> {ruta}")