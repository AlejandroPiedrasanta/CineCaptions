# Dirección de diseño: Sonido

Fecha: 21 de octubre de 2026. Propuesta para CineCaptions 5.37, aplicación nativa PySide6.

## Trabajo principal

Escuchar el resultado de GO, encontrar el momento que requiere ajuste y dirigir su sonido sin perder de vista el video ni el destino en Resolve.

## Sistema visual

- Fondo de aplicación `#080C14`, superficie `#0D1627`, borde `#1E2A42`, texto `#E8F1FF`, acento `#4589FF`, atención `#F5B84B`. Son colores del `qt_kit` existente, con color secundario por tipo de pista únicamente en la línea temporal.
- Tipografía: familia de interfaz existente; en la demostración, Segoe UI y fuente de sistema. Título 26 px, sección 15 px, controles 13 px, metadatos 12 px. Números tabulares para tiempos.
- Conservar navegación superior de Inicio, Proyecto, Creativo y Sonido. Cabecera compacta con nombre completo del video y destino. Línea temporal como espacio central de trabajo; inspector a su derecha. Controles globales compactos debajo. Diagnóstico desplegable.
- La línea temporal es el elemento dominante. El score queda como diagnóstico secundario. Evitar repetir ocho tarjetas, introducir un mezclador técnico o competir con la navegación del resto de CineCaptions.

## Composición propuesta

```text
    CineCaptions           Inicio · Proyecto · Creativo · Sonido
    Sonido   [Director en GO]        video · tema · alcance
    [Original | Mezcla IA]     tramo A/B     [Aplicar a Resolve]
    ┌──────────────────────────────────┬─────────────────────┐
    │ Línea temporal                   │ Evento seleccionado │
    │ Video / Voz / Música / Ambiente  │ Por qué / material   │
    │ Sonidos IA / Motions             │ Escuchar / variar    │
    │                                  │ silenciar / bloquear │
    └──────────────────────────────────┴─────────────────────┘
    Dirección del sonido: seis controles con Auto explícito
    Pedidos compatibles: menos sonidos / priorizar voz / sin música
    Diagnóstico y bibliotecas (desplegable)
    Estado persistente: pendiente / aplicando / sincronizado / error
```

## Revisión antes de construir

Una propuesta genérica de estudio añadiría faders, medidores y una gran puntuación: no resuelven la tarea de este producto. Se conserva la dirección asistida por IA y se centra el diseño en eventos de captions y motions. Se baja el diagnóstico a un desplegable, se renombra Rediseñar como Crear otra versión, y Restaurar diseño IA sustituye al ambiguo Deshacer todo. No se añade un historial que todavía no existe.

## Interacciones y límites

La demostración usa datos de ejemplo explícitos, permite seleccionar eventos y ver el inspector, silenciar, bloquear, variar, cambiar dirección y simular el envío. No reproduce audio, no llama a Resolve ni modifica el programa. La preescucha real conservará los WAV A/B del motor; el zoom y el alcance por video requieren trabajo de implementación.

La opción propuesta de revisar antes de enviar cambia deliberadamente la política actual de envío automático. Su implementación requiere separar edición local y aplicación, validar la identidad del timeline destino y persistir controles por video.
