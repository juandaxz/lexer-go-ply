package main

import "fmt"

// Algoritmo de prueba semantico (Maldonado Bonilla Diego Alejandro):
// asignacion de tipo y break / continue solo dentro de ciclos (sin errores)

func cuadrado(n int) int {
	return n * n
}

func main() {
	var tope int = 4
	var factor float64 = 2
	suma := 0
	promedio := 0.0
	nombre := "Diego"
	activo := true
	letra := 'a'
	suma = suma + 2
	promedio = 7.5
	nombre = "Alex"
	activo = suma > 10 && !activo
	letra = 'b'
	for i := 0; i < tope; i++ {
		suma = suma + cuadrado(i)
		if i == 2 {
			continue
		}
		if suma > 50 {
			break
		}
	}
	for _, v := range [3]int{8, 9, 10} {
		suma = suma + v
		break
	}
	n := suma
	for n > 1 {
		n = n / 2
		switch n {
		case 1:
			break
		default:
			continue
		}
	}
	for {
		break
	}
	fmt.Println(suma, promedio, nombre, activo, letra, factor)
}
