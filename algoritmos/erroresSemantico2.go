package main

import "fmt"

// Prueba de errores semanticos (Fierro Carrion Juan Diego):
// identificadores sin declarar y constantes que se intentan modificar

const limite = 100
const Saludo = "Notas"

func identificadoresSinDeclarar() {
	total := 10
	total = total + bono
	fmt.Println(total, descuento)
	resultado := calcular(3)
	fmt.Println(resultado)
}

func fueraDeAmbito() {
	if true {
		interno := 1
		fmt.Println(interno)
	}
	fmt.Println(interno)
}

func constantesModificadas() {
	const maximo = 5
	maximo = 6
	maximo += 2
	maximo++
	limite = 200
	limite--
	Saludo = "Hola"
	fmt.Println(maximo, limite, Saludo)
}

func main() {
	identificadoresSinDeclarar()
	fueraDeAmbito()
	constantesModificadas()
}
