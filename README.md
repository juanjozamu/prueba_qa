# Automatización QA para FacturaZen 

Este repositorio contiene una prueba automatizada de QA (Quality Assurance) diseñada para la plataforma **FacturaZen**, como parte del proceso de evaluación técnica proporcionado por Centauro.

## Objetivo

Automatizar el proceso de creación de un filtro en la sección de clientes del sistema FacturaZen utilizando Selenium WebDriver en Python.

## Herramientas utilizadas

- Lenguaje: Python 3
- Automatización: Selenium WebDriver
- Browser Driver: ChromeDriver
- Evidencias: Capturas de pantalla y archivo de log

## Archivos incluidos

- `FINAL.py`: Script principal que ejecuta toda la automatización.
- `qa_automation_test_log.txt`: Archivo de log generado con los pasos y resultados de la ejecución.
- `screenshot_01_login_page.png`: Pantalla de login.
- `screenshot_02_post_login.png`: Captura post-login.
- `screenshot_03_dashboard.png`: Pantalla principal (dashboard).
- `screenshot_clientes_seccion.png`: Vista de la sección de clientes.
- `screenshot_filtros_resultado_final.png`: Resultados del filtro aplicado.

## Funcionalidades del script

1. Accede a FacturaZen usando las credenciales de prueba.
2. Navega automáticamente a la sección de "Clientes".
3. Detecta posibles campos de filtro (inputs, selects).
4. Aplica filtros usando valores como:
   - Nombre: "Ruben"
   - Estado: "Activo" u opción similar
5. Valida los resultados y toma screenshots.
6. Guarda logs detallados del proceso.

## Credenciales de prueba

- Usuario: `ventas-demo@centaurosolutions.com`
- Contraseña: `Prueba123`
- URL demo: [https://csl-tst.outsystemsenterprise.com/FacturaZen](https://csl-tst.outsystemsenterprise.com/FacturaZen)

## 📝 Notas adicionales

- El script verifica que los elementos existan, sean visibles y clickeables.
- En caso de errores, genera mensajes descriptivos y continúa con estrategias alternativas (fallback).
- Se recomienda tener instalado `chromedriver.exe` en `C:/drivers/`.

## Autor

Juan Jose Vargas Zumaria  
Prueba técnica para Centauro 
