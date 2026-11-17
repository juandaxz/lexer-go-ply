package main

import "fmt"

// Prueba semantica sin errores (Villarroel Benitez Victor Adrian):
// operaciones permitidas y retorno de funciones

func dividir(a int, b int) (int, int) {
	return a / b, a % b
}

func signo(n int) string {
	if n >= 0 {
		return "positivo"
	} else {
		return "negativo"
	}
}

func promedio(notas []float64) float64 {
	var suma float64 = 0.0
	for _, n := range notas {
		suma = suma + n
	}
	return suma / 3.0
}

func main() {
	c, r := dividir(17, 5)
	total := c*2 + r - (c / 3)
	precio := 9.5
	descuento := precio * 0.1
	saludo := "Hola " + "Victor"
	activo := total > 10 && r != 0 || !(c < 1)
	notas := []float64{8.5, 9.0, 7.5}
	fmt.Println(c, r, total, descuento, saludo, activo, signo(total), promedio(notas))
}
