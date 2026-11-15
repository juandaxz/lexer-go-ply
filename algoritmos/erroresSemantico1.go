package main

import "fmt"

// Prueba de errores semanticos (Maldonado Bonilla Diego Alejandro):
// asignacion de tipo y break / continue fuera de un ciclo

func tipoEnAsignacion() {
	edad := 20
	edad = "veinte"
	nombre := "Ana"
	nombre = 5
	precio := 9.5
	precio = true
	fmt.Println(edad, nombre, precio)
}

func tipoEnVar() {
	var edad int = "veinte"
	var talla float64 = true
	fmt.Println(edad, talla)
}

func saltosFueraDeCiclo() {
	x := 4
	if x > 3 {
		continue
	}
	break
}

func continueEnSwitch() {
	x := 1
	switch x {
	case 1:
		continue
	}
}

func main() {
	tipoEnAsignacion()
	tipoEnVar()
	saltosFueraDeCiclo()
	continueEnSwitch()
}
