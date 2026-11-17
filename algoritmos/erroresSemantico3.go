package main

import "fmt"

// Prueba de errores semanticos (Villarroel Benitez Victor Adrian):
// operaciones no permitidas y errores en el retorno de funciones

func dividir(a int, b int) (int, int) {
	return a / b
}

func nombre() string {
	return 25
}

func doble(n int) int {
	x := n * 2
	fmt.Println(x)
}

func operaciones() {
	edad := 20
	precio := 9.5
	texto := "hola"
	a := texto - 3
	b := edad && true
	c := precio % 2
	d := edad / 0
	e := edad + precio
	f := !texto
	g := texto == edad
	fmt.Println(a, b, c, d, e, f, g)
}

func main() {
	x, y := nombre()
	fmt.Println(x, y, doble(4))
	operaciones()
}
