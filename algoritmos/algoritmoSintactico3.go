package main

import "fmt"

// Algoritmo de prueba sintactico (Villarroel Benitez Victor Adrian):
// retorno de varios valores (return a, b) y declaracion multiple (a, b := f())

func dividir(a int, b int) {
	return a / b, a % b
}

func main() {
	nombre := ""
	fmt.Scanln(&nombre)
	c, r := dividir(17, 5)
	total := c * 2 + r - (c / 3)
	activo := total > 10 && r != 0 || !(c < 1)
	fmt.Println(nombre, c, r, total, activo)
}