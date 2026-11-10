package main

import "fmt"

// Algoritmo de prueba (Maldonado Bonilla Diego Alejandro): estadisticas de un arreglo con ciclos for

func cuadrado(n int) int {
	return n * n
}

func esPar(n int) bool {
	return n%2 == 0
}

func main() {
	notas := [6]int{8, -3, 15, 4, -1, 12}
	suma := 0
	contados := 0
	var promedio float64 = 0

	/* suma solo los positivos,
	   salta los negativos y corta al pasar de 25 */
	for i := 0; i < 6; i++ {
		if notas[i] < 0 {
			continue
		}
		suma += notas[i]
		contados++
		if suma > 25 {
			break
		}
	}
	if contados > 0 {
		promedio = float64(suma) / float64(contados)
	}

	pares := 0
	sumaCuadrados := 0
	for _, v := range notas {
		if esPar(v) {
			pares++
			sumaCuadrados += cuadrado(v)
		}
	}

	pasos := 0
	n := suma
	for n > 1 {
		n = n / 2
		pasos++
	}

	fmt.Println("Suma:", suma, "Promedio:", promedio)
	fmt.Println("Pares:", pares, "Suma de cuadrados:", sumaCuadrados)
	fmt.Println("Divisiones entre 2:", pasos)
}