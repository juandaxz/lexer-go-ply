package main

import "fmt"

// Algoritmo de prueba semantico (Fierro Carrion Juan Diego):
// identificadores declarados y constantes que no se modifican (sin errores)

const limite = 100
const Saludo = "Notas"

func promedio(total int, cantidad int) float64 {
	return float64(total) / float64(cantidad)
}

func main() {
	notas := map[string]int{"Ana": 20, "Luis": 15}
	var suma int = 0
	contador := 0
	for nombre, nota := range notas {
		if nota < limite && nombre != "" {
			suma += nota
			contador++
		}
	}
	if contador > 0 {
		media := promedio(suma, contador)
		fmt.Println(Saludo, media)
	}
	// el nombre local oculta a la constante global, por eso se puede modificar
	limite := 5
	limite = limite + 1
	fmt.Println(suma, limite)
}
