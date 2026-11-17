"""
Analizador semántico para Go (subconjunto).
Proyecto Lenguajes de Programación - ESPOL, avance 3.

Integrantes:
  - MALDONADO BONILLA DIEGO ALEJANDRO  (@dimaboni)
  - VILLARROEL BENITEZ VICTOR ADRIAN   (@vavillar)
  - FIERRO CARRION JUAN DIEGO          (@juandaxz)

Recorre el árbol que entrega el analizador sintáctico (parser.py) con una
tabla de símbolos (pila de ámbitos) y aplica las reglas semánticas de cada
integrante. Solo se ejecuta si no hay errores léxicos ni sintácticos.

Uso:
    python semantico.py algoritmos/algoritmoSemantico1.go [usuarioGit]

Genera un log en logs/ con el nombre:
    semantico-usuarioGit-dd-mm-aaaa-HHhMM.txt
"""
import os
import re
import sys
from datetime import datetime

import parser as sintactico  # parser.py del proyecto (analizador sintáctico)

USUARIO_GIT = "dimaboni"  # o se pasa como 2.º argumento

# ============================================================
# Árbol del parser con número de línea
# El parser guarda el árbol como tuplas sin línea; aquí se envuelve cada
# producción de yacc para anotarla (sin tocar las reglas de parser.py).
# ============================================================
LINEAS = {}  # id(nodo) -> línea donde empieza
_envuelto = False


def _anotar_lineas():
    global _envuelto
    if _envuelto:
        return
    _envuelto = True
    for prod in sintactico.parser.productions:
        original = getattr(prod, "callable", None)
        if original is None:
            continue

        def envuelta(p, _orig=original):
            _orig(p)
            r = p[0]
            if isinstance(r, tuple) and not any(r is p[i] for i in range(1, len(p))):
                LINEAS[id(r)] = p.lineno(1)

        prod.callable = envuelta


def obtener_arbol(codigo):
    """Devuelve (árbol, errores léxicos, errores sintácticos)."""
    _anotar_lineas()
    sintactico.errores_sintacticos.clear()
    lista = sintactico.lexico.tokenizar(codigo)
    lexicos = [m for _, _, m in sintactico.lexico.errores]
    flujo = sintactico._Flujo(lista)
    flujo.lineno, flujo.lexpos = 1, 0
    LINEAS.clear()
    arbol = sintactico.parser.parse(lexer=flujo, tracking=True)
    return arbol, lexicos, list(sintactico.errores_sintacticos)


# ============================================================
# Tipos de Go
# ============================================================
ENTEROS = {"int", "int8", "int16", "int32", "int64",
           "uint", "uint8", "uint16", "uint32", "uint64", "rune", "byte"}
NUMERICOS = ENTEROS | {"float32", "float64"}
RE_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def tipo_str(t):
    """("arreglo", 3, "int") -> "[3]int";  ("mapa", "string", "int") -> "map[string]int"."""
    if t is None or isinstance(t, str):
        return t
    if t[0] == "arreglo":
        return f"[{t[1]}]{tipo_str(t[2])}"
    if t[0] in ("slice", "variadico"):
        return "[]" + tipo_str(t[1])
    if t[0] == "mapa":
        return f"map[{tipo_str(t[1])}]{tipo_str(t[2])}"
    return None


def tipo_elemento(t):
    """Tipo de los elementos de un arreglo, slice o mapa ("[3]int" -> "int")."""
    if not t:
        return None
    if t.startswith("["):
        return t[t.index("]") + 1:]
    if t.startswith("map["):
        nivel = 0
        for i, c in enumerate(t):
            nivel += (c == "[") - (c == "]")
            if c == "]" and nivel == 0:
                return t[i + 1:]
    return "byte" if t == "string" else None


class Simbolo:
    def __init__(self, nombre, tipo, es_const, linea, sin_tipo):
        self.nombre, self.tipo, self.es_const = nombre, tipo, es_const
        self.linea, self.sin_tipo = linea, sin_tipo  # sin_tipo: const Pi = 3.14


# ============================================================
# Recorrido del árbol + tabla de símbolos (base compartida)
# ============================================================
# nodo -> posiciones de sus hijos que son expresiones
HIJOS = {"asigna": (2, 3), "incdec": (2,), "asigna_indice": (1, 2, 3), "llamada": (2,),
         "ref": (1,), "expandido": (1,), "binop": (2, 3), "unop": (2,), "conversion": (2,),
         "acceso": (1, 2), "arreglo_lit": (2,), "slice_lit": (2,), "return": (1,)}


class Analizador:
    def __init__(self, reglas):
        self.reglas = reglas
        self.errores = []        # (línea, texto)
        self.ambitos = [{}]      # pila de ámbitos: global, función, bloque
        self.funciones = {}      # nombre -> lista de tipos que devuelve
        self.contexto = []       # pila: "func", "for", "switch"
        self.funcion_actual = None
        self.linea = 0

    # ---------- utilidades que usan las reglas ----------
    def error(self, categoria, mensaje):
        self.errores.append((self.linea, f"Error semántico [{categoria}] línea {self.linea or '?'}: {mensaje}"))

    def buscar(self, nombre):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    def declarar(self, nombre, tipo, es_const=False, sin_tipo=False):
        if nombre != "_":
            self.ambitos[-1][nombre] = Simbolo(nombre, tipo, es_const, self.linea, sin_tipo)

    def dentro_de(self, *tipos):
        """True si, sin salir de la función actual, hay un contexto de esos tipos."""
        for c in reversed(self.contexto):
            if c == "func":
                return False
            if c in tipos:
                return True
        return False

    def es_identificador(self, v):
        return isinstance(v, str) and RE_ID.match(v) is not None and v not in ("true", "false", "nil")

    def es_sin_tipo(self, e):
        """Constante sin tipo: literal numérico/rune o expresión hecha solo de ellas."""
        if isinstance(e, (int, float)):
            return True
        if isinstance(e, str):
            s = self.buscar(e) if self.es_identificador(e) else None
            return bool(s.sin_tipo) if s else e.startswith("'")
        if isinstance(e, tuple) and e[0] == "binop" and e[1] in ("+", "-", "*", "/", "%"):
            return self.es_sin_tipo(e[2]) and self.es_sin_tipo(e[3])
        if isinstance(e, tuple) and e[0] == "unop" and e[1] == "-":
            return self.es_sin_tipo(e[2])
        return False

    def tipo_de(self, e):
        """Tipo de una expresión como texto, o None si no se puede saber."""
        if isinstance(e, int):
            return "int"
        if isinstance(e, float):
            return "float64"
        if isinstance(e, str):
            if e in ("true", "false"):
                return "bool"
            if e == "nil":
                return "nil"
            if e[:1] in ('"', "`"):
                return "string"
            if e[:1] == "'":
                return "rune"
            s = self.buscar(e)
            return s.tipo if s else None
        if not isinstance(e, tuple):
            return None
        k = e[0]
        if k == "binop":
            if e[1] in ("==", "!=", "<", "<=", ">", ">=", "&&", "||"):
                return "bool"
            tl, tr = self.tipo_de(e[2]), self.tipo_de(e[3])
            if tl is None or tr is None:
                return tl or tr
            sl, sr = self.es_sin_tipo(e[2]), self.es_sin_tipo(e[3])
            if sl and not sr:
                return tr
            if sr and not sl:
                return tl
            return "float64" if sl and sr and "float64" in (tl, tr) else tl
        if k == "unop":
            return "bool" if e[1] == "!" else self.tipo_de(e[2])
        if k == "conversion":
            return tipo_str(e[1])
        if k == "acceso":
            s = self.buscar(e[1])
            return tipo_elemento(s.tipo) if s else None
        if k in ("arreglo_lit", "slice_lit", "mapa_lit"):
            return tipo_str(e[1])
        if k == "llamada":
            r = self.funciones.get(e[1])
            return r[0] if r and len(r) == 1 else None
        return None

    def compatible(self, destino, expr):
        """¿Se puede asignar 'expr' a algo de tipo 'destino'? (reglas de asignación de Go)"""
        origen = self.tipo_de(expr)
        if destino is None or origen is None or destino == origen:
            return True
        if origen == "nil":
            return destino.startswith("[]") or destino.startswith("map[")
        if self.es_sin_tipo(expr):  # una constante numérica entra en cualquier tipo numérico
            if origen in ("int", "rune"):
                return destino in NUMERICOS
            if origen == "float64":
                entero = isinstance(expr, float) and expr.is_integer()
                return destino in NUMERICOS if entero else destino in ("float32", "float64")
        return False

    # ---------- recorrido ----------
    def visitar(self, nodo):
        if not isinstance(nodo, tuple) or not nodo:
            return
        previa = self.linea
        self.linea = LINEAS.get(id(nodo)) or self.linea
        for regla in self.reglas:
            regla(self, nodo)
        metodo = getattr(self, "_v_" + str(nodo[0]), None)
        if metodo:
            metodo(nodo)
        for i in HIJOS.get(nodo[0], ()):
            if i < len(nodo):
                self.visitar_expr(nodo[i])
        self.linea = previa

    def visitar_expr(self, e):
        if isinstance(e, tuple):
            self.visitar(e)
        elif isinstance(e, list):
            for x in e:
                self.visitar_expr(x)
        elif self.es_identificador(e):  # cada identificador usado se ofrece a las reglas
            for regla in self.reglas:
                regla(self, ("id", e))

    def sentencias(self, lista):
        for s in lista or []:
            self.visitar(s)

    def _retornos(self, tipo_ret):
        if tipo_ret is None:
            return []
        if isinstance(tipo_ret, tuple) and tipo_ret[0] == "tipos":
            return [tipo_str(t) for t in tipo_ret[1]]
        return [tipo_str(tipo_ret)]

    def _v_programa(self, nodo):
        decls = [d for d in nodo[3] or [] if isinstance(d, tuple)]
        for d in decls:  # las funciones se conocen antes de recorrer el código
            if d[0] == "func":
                self.funciones[d[1]] = self._retornos(d[3])
        for d in decls:  # primero var / const globales, luego las funciones
            if d[0] in ("var", "const"):
                self.visitar(d)
        for d in decls:
            if d[0] == "func":
                self.visitar(d)

    def _v_func(self, nodo):
        _, nombre, params, tipo_ret, bloque = nodo
        self.ambitos.append({})
        self.contexto.append("func")
        anterior, self.funcion_actual = self.funcion_actual, (nombre, self._retornos(tipo_ret))
        for pnombre, ptipo in params or []:
            self.declarar(pnombre, tipo_str(ptipo))
        self.sentencias(bloque[1])
        self.funcion_actual = anterior
        self.contexto.pop()
        self.ambitos.pop()

    def _v_bloque(self, nodo):
        self.ambitos.append({})
        self.sentencias(nodo[1])
        self.ambitos.pop()

    def _v_var(self, nodo):
        _, nombre, tipo, expr = nodo
        self.visitar_expr(expr)
        self.declarar(nombre, tipo_str(tipo) if tipo else self.tipo_de(expr))

    def _v_const(self, nodo):
        self.visitar_expr(nodo[2])
        self.declarar(nodo[1], self.tipo_de(nodo[2]), es_const=True, sin_tipo=self.es_sin_tipo(nodo[2]))

    def _v_declara_corta(self, nodo):
        self.visitar_expr(nodo[2])
        self.declarar(nodo[1], self.tipo_de(nodo[2]))

    def _v_declara_multiple(self, nodo):
        self.visitar_expr(nodo[2])
        e = nodo[2]
        tipos = self.funciones.get(e[1], []) if isinstance(e, tuple) and e[0] == "llamada" else []
        if len(tipos) != len(nodo[1]):
            tipos = [None] * len(nodo[1])
        for n, t in zip(nodo[1], tipos):
            self.declarar(n, t)

    def _v_mapa_lit(self, nodo):
        for clave, valor in nodo[2] or []:
            self.visitar_expr(clave)
            self.visitar_expr(valor)

    def _cuerpo_for(self, bloque):
        self.contexto.append("for")
        self.visitar(bloque)
        self.contexto.pop()

    def _v_for_clasico(self, nodo):
        self.ambitos.append({})
        self.visitar(nodo[1])
        self.visitar_expr(nodo[2])
        self._cuerpo_for(nodo[4])
        self.visitar(nodo[3])
        self.ambitos.pop()

    def _v_for_condicion(self, nodo):
        self.visitar_expr(nodo[1])
        self._cuerpo_for(nodo[2])

    def _v_for_infinito(self, nodo):
        self._cuerpo_for(nodo[1])

    def _v_for_range(self, nodo):
        self.ambitos.append({})
        self.visitar_expr(nodo[3])
        t = self.tipo_de(nodo[3])
        clave = t[4:t.index("]")] if t and t.startswith("map[") else "int"
        self.declarar(nodo[1], clave)
        self.declarar(nodo[2], tipo_elemento(t))
        self._cuerpo_for(nodo[4])
        self.ambitos.pop()

    def _v_if(self, nodo):
        self.visitar_expr(nodo[1])
        self.visitar(nodo[2])
        self.visitar(nodo[3])

    def _v_switch(self, nodo):
        self.visitar_expr(nodo[1])
        self.contexto.append("switch")
        for caso in nodo[2] or []:
            self.ambitos.append({})
            if caso[0] == "case":
                self.visitar_expr(caso[1])
            self.sentencias(caso[2] if caso[0] == "case" else caso[1])
            self.ambitos.pop()
        self.contexto.pop()


def valores_return(nodo):
    """Lista de expresiones de un return (el parser puede dar lista, una expresión o None)."""
    v = nodo[1]
    return [] if v is None else (v if isinstance(v, list) else [v])


# ============================================================
# REGLAS SEMÁNTICAS
# Cada regla es una función regla(ctx, nodo): se llama en cada nodo del
# árbol (sentencias, expresiones y ("id", nombre) por cada identificador
# usado). Si detecta un problema llama a ctx.error(categoría, mensaje).
# ============================================================


# ============================================================
# INICIO aporte: MALDONADO BONILLA DIEGO ALEJANDRO (@dimaboni)
# Asignación de tipo y Estructuras de control
# ============================================================

# --- Regla 1 [Asignación de tipo]: el valor asignado debe ser del tipo con el
#     que se declaró la variable.
#     Ejemplo con error:  var edad int = "veinte"
def regla_asignacion_tipo(ctx, nodo):
    if nodo[0] == "var" and nodo[2] is not None and nodo[3] is not None:
        destino = tipo_str(nodo[2])
        if not ctx.compatible(destino, nodo[3]):
            ctx.error("Asignación de tipo",
                      f"no se puede asignar un valor de tipo '{ctx.tipo_de(nodo[3])}' "
                      f"a la variable '{nodo[1]}' declarada como '{destino}'.")
    elif nodo[0] == "asigna" and nodo[1] == "=":
        s = ctx.buscar(nodo[2])
        if s and s.tipo and not ctx.compatible(s.tipo, nodo[3]):
            ctx.error("Asignación de tipo",
                      f"no se puede asignar un valor de tipo '{ctx.tipo_de(nodo[3])}' "
                      f"a la variable '{nodo[2]}' de tipo '{s.tipo}'.")


# --- Regla 2 [Estructuras de control]: break y continue solo pueden aparecer
#     dentro de un for (break también dentro de un switch).
#     Ejemplo con error:  if x > 3 { continue }   (fuera de un for)
def regla_salto_en_ciclo(ctx, nodo):
    if nodo[0] == "break" and not ctx.dentro_de("for", "switch"):
        ctx.error("Estructuras de control", "'break' solo puede usarse dentro de un for o un switch.")
    elif nodo[0] == "continue" and not ctx.dentro_de("for"):
        ctx.error("Estructuras de control", "'continue' solo puede usarse dentro de un for.")

# FIN aporte: MALDONADO BONILLA DIEGO ALEJANDRO
# ============================================================


# ============================================================
# INICIO aporte: VILLARROEL BENITEZ VICTOR ADRIAN (@vavillar)
# Operaciones permitidas y Retorno de funciones
# ============================================================

# Villarroel: aquí van sus reglas semánticas (Operaciones permitidas y
# Retorno de funciones). Cada regla es una función regla(ctx, nodo) y se
# agrega a reglas_villarroel más abajo. Nodos útiles: ("binop", op, izq, der),
# ("unop", op, e), ("return", valores); ctx.funcion_actual = (nombre, tipos).

ARITMETICOS = ("+", "-", "*", "/", "%")
LOGICOS = ("&&", "||")
ORDEN = ("<", "<=", ">", ">=")


# --- Regla 1 [Operaciones permitidas]: cada operador solo se aplica a los
#     tipos que lo admiten y ambos operandos deben ser del mismo tipo.
#       * + - * /  -> numéricos del mismo tipo ('+' también string + string)
#       * %        -> solo enteros
#       * / y % entre la constante 0 -> división entre cero
#       * && || !  -> solo bool
#       * < <= > >= -> números o strings del mismo tipo;  == != -> mismo tipo
#     Ejemplos con error:  "hola" - 3   |   edad && true   |   precio % 2   |   x / 0
def regla_operaciones_permitidas(ctx, nodo):
    if nodo[0] == "binop":
        op, izq, der = nodo[1], nodo[2], nodo[3]
        if op in ("/", "%") and der == 0:
            ctx.error("Operaciones permitidas", f"división entre cero en la operación '{op}'.")
            return
        ti, td = ctx.tipo_de(izq), ctx.tipo_de(der)
        if ti is None or td is None:  # tipo desconocido: no se puede verificar
            return
        if op in LOGICOS:
            for t in (ti, td):
                if t != "bool":
                    ctx.error("Operaciones permitidas",
                              f"el operador '{op}' requiere operandos 'bool', se encontró '{t}'.")
                    return
            return
        if op in ARITMETICOS:
            permitido = NUMERICOS | ({"string"} if op == "+" else set())
            for t in (ti, td):
                if t not in permitido:
                    ctx.error("Operaciones permitidas",
                              f"el operador '{op}' no está definido para el tipo '{t}'.")
                    return
            if op == "%" and (ti not in ENTEROS or td not in ENTEROS):
                ctx.error("Operaciones permitidas",
                          f"el operador '%' solo se aplica a enteros, se encontró '{ti}' % '{td}'.")
                return
        if op in ORDEN:
            for t in (ti, td):
                if t not in NUMERICOS | {"string"}:
                    ctx.error("Operaciones permitidas",
                              f"el operador '{op}' no se puede usar con el tipo '{t}'.")
                    return
        # mismos tipos (una constante sin tipo, como 2 o 3.5, se adapta al otro lado)
        if ti != td and not (ctx.compatible(ti, der) or ctx.compatible(td, izq)) \
                and "nil" not in (ti, td):
            ctx.error("Operaciones permitidas",
                      f"tipos distintos en '{op}': '{ti}' y '{td}'.")
    elif nodo[0] == "unop":
        t = ctx.tipo_de(nodo[2])
        if t is None:
            return
        if nodo[1] == "!" and t != "bool":
            ctx.error("Operaciones permitidas", f"el operador '!' requiere 'bool', se encontró '{t}'.")
        elif nodo[1] == "-" and t not in NUMERICOS:
            ctx.error("Operaciones permitidas", f"el operador '-' no está definido para el tipo '{t}'.")


def _termina(sentencias):
    """True si la lista de sentencias siempre termina en return (o en un for sin condición)."""
    if not sentencias:
        return False
    ultima = sentencias[-1]
    if not isinstance(ultima, tuple):
        return False
    if ultima[0] == "return" or ultima[0] == "for_infinito":
        return True
    if ultima[0] == "bloque":
        return _termina(ultima[1])
    if ultima[0] == "if":
        otro = ultima[3]
        if otro is None:
            return False
        return _termina(ultima[2][1]) and _termina([otro])
    return False


# --- Regla 2 [Retorno de funciones]:
#       * el return debe devolver tantos valores como tipos declara la función
#       * cada valor devuelto debe ser del tipo declarado en su posición
#       * una función con tipo de retorno debe terminar en return
#       * en  a, b := f()  f debe devolver exactamente 2 valores
#     Ejemplos con error:  func f() (int, int) { return 1 }
#                          func g() int { return "hola" }
#                          func h() int { x := 1 }
def regla_retorno_funciones(ctx, nodo):
    if nodo[0] == "return" and ctx.funcion_actual:
        nombre, tipos = ctx.funcion_actual
        valores = valores_return(nodo)
        if len(valores) != len(tipos):
            ctx.error("Retorno de funciones",
                      f"la función '{nombre}' debe devolver {len(tipos)} valor(es) "
                      f"y el return tiene {len(valores)}.")
            return
        for i, (t, v) in enumerate(zip(tipos, valores), start=1):
            if not ctx.compatible(t, v):
                ctx.error("Retorno de funciones",
                          f"el valor {i} del return en '{nombre}' es de tipo '{ctx.tipo_de(v)}' "
                          f"y la función declara '{t}'.")
    elif nodo[0] == "func":
        tipos = ctx._retornos(nodo[3])
        if tipos and not _termina(nodo[4][1]):
            ctx.error("Retorno de funciones",
                      f"a la función '{nodo[1]}' le falta un return al final "
                      f"(declara devolver {', '.join(tipos)}).")
    elif nodo[0] == "declara_multiple":
        e = nodo[2]
        if isinstance(e, tuple) and e[0] == "llamada" and e[1] in ctx.funciones:
            n = len(ctx.funciones[e[1]])
            if n != len(nodo[1]):
                ctx.error("Retorno de funciones",
                          f"se asignan {len(nodo[1])} variables pero '{e[1]}' devuelve {n} valor(es).")

# FIN aporte: VILLARROEL BENITEZ VICTOR ADRIAN
# ============================================================


# ============================================================
# INICIO aporte: FIERRO CARRION JUAN DIEGO (@juandaxz)
# Identificadores y Asignación de tipo (constantes)
# ============================================================

# Funciones de Go que se pueden llamar sin declararlas en el programa.
FUNCIONES_PREDEFINIDAS = {"len", "cap", "append", "copy", "delete", "make", "new",
                          "print", "println", "panic", "recover", "min", "max"}


# --- Regla 1 [Identificadores]: todo identificador debe estar declarado antes de
#     usarse. También se revisa que la función llamada exista.
#     Ejemplo con error:  total = total + bono   (bono no fue declarado)
def regla_identificador_declarado(ctx, nodo):
    if nodo[0] == "id":
        nombre = nodo[1]
        if nombre != "_" and ctx.buscar(nombre) is None and nombre not in ctx.funciones:
            ctx.error("Identificadores",
                      f"el identificador '{nombre}' se usa sin haber sido declarado.")
    elif nodo[0] == "llamada" and "." not in nodo[1]:  # fmt.Println y similares no se revisan
        nombre = nodo[1]
        if (nombre not in ctx.funciones and nombre not in FUNCIONES_PREDEFINIDAS
                and ctx.buscar(nombre) is None):
            ctx.error("Identificadores",
                      f"la función '{nombre}' se llama pero no está declarada.")


# --- Regla 2 [Constantes no modificables]: una constante no puede cambiar su valor
#     después de declararse (=, +=, -=, *=, /=, %=, ++ y --).
#     Ejemplo con error:  const limite = 100 ... limite = 200
def regla_constante_no_modificable(ctx, nodo):
    if nodo[0] in ("asigna", "incdec"):  # en ambos nodos el nombre está en la posición 2
        simbolo = ctx.buscar(nodo[2]) if ctx.es_identificador(nodo[2]) else None
        if simbolo is not None and simbolo.es_const:
            accion = f"asignar con '{nodo[1]}'" if nodo[0] == "asigna" else f"usar '{nodo[1]}' sobre"
            ctx.error("Constantes",
                      f"no se puede {accion} la constante '{nodo[2]}' "
                      f"(declarada en la línea {simbolo.linea}), su valor no puede cambiar.")

# FIN aporte: FIERRO CARRION JUAN DIEGO
# ============================================================


# ============================================================
# Reglas activas (cada integrante agrega las suyas en su lista)
# ============================================================
reglas_maldonado = [regla_asignacion_tipo, regla_salto_en_ciclo]  # Maldonado agrega aquí sus reglas
reglas_villarroel = []  # Villarroel agrega aquí sus reglas
reglas_fierro = [regla_identificador_declarado, regla_constante_no_modificable]  # Fierro agrega aquí sus reglas

REGLAS = reglas_maldonado + reglas_villarroel + reglas_fierro


# ============================================================
# Ejecución y log
# ============================================================
def analizar(codigo):
    """Devuelve (errores léxicos, errores sintácticos, errores semánticos)."""
    arbol, lexicos, sintacticos = obtener_arbol(codigo)
    if lexicos or sintacticos or arbol is None:
        return lexicos, sintacticos, []
    analizador = Analizador(REGLAS)
    analizador.visitar(arbol)
    return lexicos, sintacticos, [m for _, m in sorted(analizador.errores, key=lambda e: e[0])]


def escribir_log(archivo_fuente, usuario, lexicos, sintacticos, semanticos):
    os.makedirs("logs", exist_ok=True)
    ahora = datetime.now()
    ruta = os.path.join("logs", f"semantico-{usuario}-{ahora.strftime('%d-%m-%Y-%Hh%M')}.txt")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"Analisis semantico de: {archivo_fuente}\n")
        f.write(f"Usuario: {usuario} Fecha: {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write("=" * 60 + "\n")
        if lexicos or sintacticos:
            f.write("NO SE EJECUTO EL ANALISIS SEMANTICO: el codigo tiene errores previos\n")
            f.write(f"({len(lexicos)} lexicos, {len(sintacticos)} sintacticos). Corrigelos primero.\n")
        else:
            f.write(f"ERRORES SEMANTICOS ({len(semanticos)})\n")
            f.write("=" * 60 + "\n")
            for m in semanticos:
                f.write(m + "\n")
            if not semanticos:
                f.write("(sin errores)\n")
    return ruta


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python semantico.py archivo.go [usuarioGit]")
        sys.exit(1)
    fuente = sys.argv[1]
    usuario = sys.argv[2] if len(sys.argv) > 2 else USUARIO_GIT
    with open(fuente, encoding="utf-8") as f:
        codigo = f.read()
    lex_err, sin_err, sem_err = analizar(codigo)
    ruta = escribir_log(fuente, usuario, lex_err, sin_err, sem_err)
    if lex_err or sin_err:
        print(f"{len(lex_err)} errores léxicos, {len(sin_err)} sintácticos: no se ejecutó el semántico -> {ruta}")
    else:
        print(f"{len(sem_err)} errores semánticos -> {ruta}")