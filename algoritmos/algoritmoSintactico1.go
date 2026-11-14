package main

import "fmt"

// Algoritmo de prueba sintactico (Maldonado Bonilla Diego Alejandro):
// declaracion corta, arreglo, ciclos for y funciones con un valor de retorno

func cuadrado(n int) int {
	return n * n
}

func saludar() {
	fmt.Println("Hola")
}

func main() {
	notas := [5]int{8, -3, 15, 4, 12}
	suma := 0
	pasos := 0
	pares := 0
	notas[1] = 10
	for i := 0; i < 5; i++ {
		suma += notas[i]
		if_ := notas[i] % 2 == 0 && suma > 0 || !(suma < 3)
		pares += cuadrado(notas[i]) - 1
		fmt.Println(if_)
	}
	for _, v := range notas {
		suma = suma + v*2 - (v / 2)
		continue
	}
	n := suma
	for n > 1 {
		n = n / 2
		pasos++
		break
	}
	for {
		break
	}
	fmt.Scanln(&n)
	saludar()
	fmt.Println("Suma:", suma, "Pasos:", pasos, pares)
}
