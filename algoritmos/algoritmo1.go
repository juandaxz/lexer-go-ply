package main
 
import "fmt"
 
// Algoritmo de prueba (Fierro Carrion Juan Diego): conteo de calificaciones con mapas
func main() {
	notas := map[string]int{"Ana": 20, "Luis": 15}
	var total int = 0
	const minimo = 0x0A
	const limite = 100
	var edades map[string]int
	/* recorre el mapa
	   y suma las notas */
	for nombre, nota := range notas {
		if nota >= minimo && nombre != "" {
			total += nota
		}
	}
	switch limite {
	case 100:
		total += 1
	default:
		total--
	}
	promedio := float64(total) / 2.5e0
	letra := 'A'
	resultado := 5 @ 3
	fmt.Println("Promedio:", promedio, letra, resultado, edades)
}