// Algoritmo de prueba del analizador sintáctico - FIERRO CARRION JUAN DIEGO (@juandaxz)
// Cubre: const, switch (case/default/fallthrough), map[K]V y función con argumentos variables,
// más impresión, ingreso por teclado, expresiones aritméticas, condiciones lógicas y asignaciones.
package main

import "fmt"

const Pi = 3.14159
const Saludo = "Bienvenido"

// función con argumentos variables
func sumar(nums ...int) int {
	total := 0
	for _, n := range nums {
		total += n
	}
	return total
}

func main() {
	// ingreso de datos por teclado
	dia := 0
	fmt.Println("Ingrese un dia (1-7):")
	fmt.Scanln(&dia)

	// switch con case, fallthrough y default
	switch dia {
	case 1, 7:
		fmt.Println("Fin de semana")
	case 2:
		fmt.Println("Lunes")
		fallthrough
	case 3:
		fmt.Println("Entre semana")
	default:
		fmt.Println("Otro dia")
	}

	// mapa
	edades := map[string]int{"Ana": 20, "Luis": 22}
	edades["Marta"] = 25
	vacio := map[string]int{}
	fmt.Println(Saludo, edades["Ana"], vacio)

	// expresiones aritméticas y condiciones con conectores lógicos
	radio := 5
	area := Pi * float64(radio) * float64(radio)
	resto := (dia+3)*2 - dia%4
	for dia > 0 && dia < 8 || !(resto == 0) {
		fmt.Println("Area:", area)
		break
	}

	// llamada con argumentos variables y expansión
	numeros := [3]int{1, 2, 3}
	total := sumar(4, 5, 6)
	total += sumar(numeros...)
	fmt.Println("Total:", total)
}
