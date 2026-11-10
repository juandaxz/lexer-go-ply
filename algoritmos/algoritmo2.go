package main

import "fmt"

// Algoritmo de prueba: estadísticas de un slice var, if/else, return, slice [], función con varios retornos  operadores aritméticos, 
// de comparación y lógicos, cadenas, cadenas crudas y runas.

func divmod(a int, b int) (int, int) {
	return a / b, a % b
}

func clasificar(n int) string {
	if n < 0 {
		return "negativo"
	} else if n == 0 {
		return "cero"
	} else {
		return "positivo"
	}
}

func main() {
	var numeros []int = []int{12, -4, 0, 7, 9}
	var nombre string = "Victor \"VV\"\n"
	var inicial rune = 'V'
	var salto rune = '\n'
	var suma int = 0
	for _, n := range numeros {
		if n > 0 && n%2 != 0 || n <= -4 {
			suma = suma + n*2 - 1
		}
		if !(n >= 10) {
			fmt.Println(n, clasificar(n))
		}
	}
	cociente, resto := divmod(suma, 3)
	ruta := `C:\go\bin`
	fmt.Println(nombre, inicial, salto, cociente, resto, ruta)
}
