package main

import "fmt"

// Algoritmo de prueba (Fierro Carrión Juan Diego): conteo de calificaciones con mapas
func main() {
	notas := map[string]int{"Ana": 20, "Luis": 15}
	var total int = 0
	const minimo = 0x0A
	/* recorre el mapa
	   y suma las notas */
	for nombre, nota := range notas {
		if nota >= minimo && nombre != "" {
			total += nota
		}
	}
	promedio := float64(total) / 2.5e0
	letra := 'A'
	crudo := `texto
crudo`
	total++
	fmt.Println("Promedio:", promedio, letra, crudo)
}