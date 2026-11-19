# Guía de Marca — Cymbal Bank

*Estándar Oficial de Identidad Visual, Tipografía y Comunicación para Banca Corporativa y Gestión de Riesgos*

- **División:** Banca Corporativa y Gestión de Riesgos
- **Audiencia:** Directores Financieros (CFO) y Analistas de Riesgo
- **Estado:** Vigente
- **Fuente oficial en Google Drive:** [Guía de Marca - Cymbal Bank](https://docs.google.com/document/d/1ER4OtSPleHdrR3RNfLFFjhFzPdpBVK73MDoQVxlYLT8/edit) · [Kit de Diseño - Cymbal Bank](https://drive.google.com/drive/folders/1DMpr7CM3_KN6tAOxEwsUFH0ZO-vnFT3k)

> **Mandato de Cumplimiento:** Toda interfaz digital, presentación ejecutiva, tablero de métricas y correo electrónico producido para Cymbal Bank debe adherirse estrictamente a esta guía. La consistencia visual y verbal protege la credibilidad institucional ante comités financieros y directores financieros (CFO).

---

## 1. Identidad y Posicionamiento de Marca

Cymbal Bank opera en la intersección de la Banca Corporativa y la Gestión de Riesgos, atendiendo a tesorerías corporativas, comités de inversión y directores financieros que requieren visibilidad inmediata sobre capital, liquidez y exposición. Nuestra identidad refleja solidez fiduciaria, disciplina analítica y transparencia operativa: cada componente gráfico y cada enunciado debe facilitar decisiones financieras de alto impacto con mínima fricción cognitiva.

El sistema de diseño rechaza el exceso ornamental en favor de jerarquías limpias, contrastes rigurosos y señalización semántica inequívoca. Ya sea en un tablero de riesgo en modo oscuro, un reporte ejecutivo en superficie clara o una comunicación por correo electrónico, la audiencia debe reconocer de inmediato la precisión técnica y la sobriedad institucional propias de Cymbal Bank.

---

## 2. Paleta Cromática Oficial

La paleta de Cymbal Bank se compone de seis colores canónicos con responsabilidades estrictas de jerarquía, superficies y semaforización de riesgo. No se permite introducir tonos arbitrarios ni utilizar los colores de alerta con fines meramente decorativos.

| Token / Rol | Hex | Aplicación Principal | Reglas de Contraste |
| :--- | :---: | :--- | :--- |
| **Primario** | `#1A73E8` | Acciones principales, encabezados, enlaces y foco de navegación. | Texto `#FFFFFF` sobre este fondo; rol institucional central. |
| **Secundario** | `#0F9D58` | Indicadores positivos, métricas en rango, variaciones favorables y riesgo bajo. | Acompañar con signos (`+`/`-`) o etiquetas para accesibilidad. |
| **Riesgo Alto** | `#D93025` | Alertas críticas, incumplimientos de umbral, deterioro crediticio o liquidez crítica. | Reservado solo para severidad alta; prohibido como adorno. |
| **Riesgo Medio** | `#F9AB00` | Alertas preventivas, vigilancia activa, desviaciones moderadas y revisión pendiente. | Combinar con texto oscuro (`#12161F`) para contraste óptimo. |
| **Fondo Claro** | `#F8F9FA` | Superficie base en reportes, interfaces diurnas, tarjetas y presentaciones ejecutivas. | Combinar con texto oscuro (`#12161F` / `#202124`) y bordes sutiles. |
| **Fondo Oscuro** | `#12161F` | Modo oscuro de tableros de riesgo, portadas ejecutivas y barras de navegación. | Combinar con tipografía clara (`#F8F9FA` / `#FFFFFF`). |

**Semáforo de riesgo:** Bajo (`#0F9D58`) · Riesgo Medio (`#F9AB00`) · Riesgo Alto (`#D93025`)

Todas las combinaciones de texto y fondo deben cumplir al menos con el estándar de contraste **WCAG AA** (`4.5:1` para cuerpo y `3:1` para elementos gráficos grandes). En visualizaciones financieras sobre Fondo Claro (`#F8F9FA`) o Fondo Oscuro (`#12161F`), las series principales utilizan Primario (`#1A73E8`) y Secundario (`#0F9D58`), dejando Riesgo Medio (`#F9AB00`) y Riesgo Alto (`#D93025`) reservados exclusivamente para umbrales de tolerancia, brechas regulatorias y alertas de cartera.

---

## 3. Sistema Tipográfico y Números Tabulares

La arquitectura tipográfica de Cymbal Bank estandariza dos familias sans-serif de alta legibilidad: **Inter** (preferida en aplicaciones web, sistemas de diseño y tableros interactivos) y **Roboto** (alternativa oficial para presentaciones, documentos en Google Workspace y entornos donde Inter no esté disponible de forma nativa). Para cualquier métrica financiera, balance, tasa, porcentaje o tabla comparativa es obligatorio activar números tabulares (`tabular-nums`), asegurando que cada dígito ocupe el mismo ancho horizontal y permita comparar magnitudes en columna sin desplazamiento visual.

```css
/* Especificación CSS — Cymbal Bank */
body {
  font-family: 'Inter', 'Roboto', sans-serif;
  color: #12161F;
}

.financial-metric,
td.numeric {
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum" 1;
  text-align: right;
}
```

- **Titulares y KPIs destacados:** Peso SemiBold o Bold (`600–700`) en Inter o Roboto, con interlineado compacto y números tabulares para cifras monetarias de cabecera.
- **Cuerpo analítico y narrativo:** Peso Regular (`400`), tamaño de `11 pt` en documentos y `14–16 px` en web, siempre alineado a la izquierda para máxima velocidad de lectura.
- **Tablas financieras y reportes de riesgo:** Columnas numéricas alineadas a la derecha, número constante de decimales por columna, separadores de miles uniformes y moneda explícita (ej. `USD 14,250,000.00`).
- **Notas metodológicas y pies de página:** Tamaño reducido (`8–9 pt` en documentos, `12 px` en interfaces) reservado para fuentes de datos, fecha de corte y supuestos de cálculo.

---

## 4. Voz, Tono y Estándar de Comunicación para CFO

La comunicación de Cymbal Bank es ejecutiva, precisa y orientada a directores financieros (CFO). Cada mensaje debe estructurarse bajo el principio de **conclusión primero**: exponer el impacto financiero neto, el nivel de riesgo cuantificado y la recomendación accionable antes de profundizar en el detalle técnico.

- **SÍ — Precisión cuantitativa:** Sustentar cada afirmación con métricas verificables, puntos básicos (pbs), horizontes temporales y comparación frente a límites de apetito de riesgo.
- **SÍ — Claridad orientada a decisión:** Conectar la gestión de riesgos con liquidez, costo de capital, cobertura cambiaria y cumplimiento regulatorio mediante párrafos breves y directos.
- **NO — Lenguaje comercial o impreciso:** Evitar hipérboles, adjetivos subjetivos ("increíble", "revolucionario"), emojis decorativos en comunicaciones formales o fórmulas vagas sin respaldo numérico.
- **NO — Opacidad en alertas críticas:** Nunca suavizar exposiciones de Riesgo Alto (`#D93025`) ni relegar supuestos de estrés financiero a notas secundarias.

> *Ejemplo de redacción aprobada para CFO:* "Al cierre del 3T, la exposición neta a tasa variable asciende a USD 48.20M (18.4% de la deuda corporativa), superando en 340 pbs el umbral interno de Riesgo Medio. Recomendamos ejecutar una cobertura de tasa de interés a 24 meses antes del 15 de noviembre para fijar el costo financiero dentro del presupuesto anual."

---

## 5. Aplicación Obligatoria por Canal

| Canal / Entregable | Estándar Visual y Tipográfico | Estructura y Criterio de Tono |
| :--- | :--- | :--- |
| **Interfaces y Apps Web** | Base en Fondo Claro (`#F8F9FA`) o Fondo Oscuro (`#12161F`); acciones en Primario (`#1A73E8`); semáforo estricto (`#0F9D58`, `#F9AB00`, `#D93025`); Inter o Roboto con `tabular-nums` obligatorio en KPIs y tablas. | Lectura rápida de liquidez, exposición y alertas; etiquetas concisas, unidades explícitas y cero ruido visual. |
| **Presentaciones Ejecutivas** | Portadas y divisores sobrios en Fondo Oscuro (`#12161F`) o Fondo Claro (`#F8F9FA`); títulos en Roboto o Inter; gráficos alineados con la paleta oficial y cifras alineadas verticalmente. | Un hallazgo financiero por diapositiva, titular declarativo con conclusión y respaldo cuantitativo verificable. |
| **Correos Corporativos** | Diseño limpio sobre fondo claro, jerarquía en Inter o Roboto, acento moderado en `#1A73E8` y etiquetas de severidad coherentes con `#D93025` o `#F9AB00` cuando existan alertas. | Asunto cuantitativo y accionable; resumen ejecutivo dirigido al CFO en las primeras líneas; próximos pasos con responsables y fechas. |

---

*Cymbal Bank — Banca Corporativa y Gestión de Riesgos · Guía de Marca Oficial · Documento Normativo Interno*
