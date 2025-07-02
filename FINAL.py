from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import traceback
import os

# Configurar logging detallado
log_file = open("qa_automation_test_log.txt", "w", encoding="utf-8")

def log(mensaje):
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {mensaje}"
    print(formatted_msg)
    log_file.write(formatted_msg + "\n")
    log_file.flush()

def verificar_sesion_activa(driver):
    """Verifica si la sesión del driver sigue activa"""
    try:
        driver.current_url
        return True
    except WebDriverException:
        log(" Sesión del driver perdida")
        return False

def tomar_screenshot(driver, nombre):
    """Toma screenshot para documentar el progreso con manejo de errores mejorado"""
    try:
        if not verificar_sesion_activa(driver):
            log(" No se puede tomar screenshot - sesión inválida")
            return False
            
        driver.save_screenshot(f"screenshot_{nombre}.png")
        log(f" Screenshot guardado: screenshot_{nombre}.png")
        return True
    except Exception as e:
        log(f" Error al tomar screenshot: {e}")
        return False

def esperar_y_buscar_elemento(driver, by, valor, timeout=20, descripcion="elemento"):
    """Función helper para esperar y buscar elementos con mejor manejo de errores"""
    try:
        if not verificar_sesion_activa(driver):
            log(f" Sesión inválida al buscar {descripcion}")
            return None
            
        log(f"🔍 Buscando {descripcion}...")
        elemento = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, valor))
        )
        log(f" {descripcion} encontrado")
        return elemento
    except TimeoutException:
        log(f" Timeout al buscar {descripcion}")
        return None
    except Exception as e:
        log(f" Error al buscar {descripcion}: {e}")
        return None

def esperar_elemento_clickeable(driver, by, valor, timeout=20, descripcion="elemento"):
    """Espera a que un elemento sea clickeable"""
    try:
        if not verificar_sesion_activa(driver):
            return None
            
        log(f" Esperando que {descripcion} sea clickeable...")
        elemento = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, valor))
        )
        log(f" {descripcion} listo para click")
        return elemento
    except TimeoutException:
        log(f" Timeout esperando {descripcion} clickeable")
        return None
    except Exception as e:
        log(f" Error esperando {descripcion}: {e}")
        return None

def click_seguro(driver, elemento, descripcion="elemento"):
    """Realiza click con manejo de errores y scroll automático"""
    try:
        if not verificar_sesion_activa(driver):
            return False
            
        # Scroll al elemento
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elemento)
        time.sleep(1)
        
        # Intentar click normal
        try:
            elemento.click()
            log(f" Click exitoso en {descripcion}")
            return True
        except:
            # Si falla, usar JavaScript
            driver.execute_script("arguments[0].click();", elemento)
            log(f" Click con JavaScript en {descripcion}")
            return True
            
    except Exception as e:
        log(f" Error al hacer click en {descripcion}: {e}")
        return False

def analizar_dom_pagina(driver):
    """Analiza el DOM de la página para identificar elementos de filtro disponibles"""
    try:
        log(" Analizando DOM de la página actual...")
        
        # Obtener todos los elementos input y select
        inputs = driver.find_elements(By.TAG_NAME, "input")
        selects = driver.find_elements(By.TAG_NAME, "select")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        
        log(f" Elementos encontrados: {len(inputs)} inputs, {len(selects)} selects, {len(buttons)} buttons")
        
        # Analizar inputs
        log(" Analizando campos INPUT:")
        for i, input_elem in enumerate(inputs[:10]):  # Limitar a 10 para evitar spam
            try:
                input_type = input_elem.get_attribute("type") or "no-type"
                input_id = input_elem.get_attribute("id") or "no-id"
                input_name = input_elem.get_attribute("name") or "no-name"
                input_placeholder = input_elem.get_attribute("placeholder") or "no-placeholder"
                input_class = input_elem.get_attribute("class") or "no-class"
                
                log(f"   Input {i+1}: type='{input_type}', id='{input_id}', name='{input_name}', placeholder='{input_placeholder}'")
                
                if input_type in ["text", "search"]:
                    log(f"    Campo de texto potencial para filtro encontrado: {input_id}")
                    
            except Exception as e:
                log(f"   ❌ Error analizando input {i}: {e}")
        
        # Analizar selects
        log(" Analizando campos SELECT:")
        for i, select_elem in enumerate(selects[:5]):  # Limitar a 5
            try:
                select_id = select_elem.get_attribute("id") or "no-id"
                select_name = select_elem.get_attribute("name") or "no-name"
                select_class = select_elem.get_attribute("class") or "no-class"
                
                log(f"   Select {i+1}: id='{select_id}', name='{select_name}', class='{select_class}'")
                
                # Obtener opciones
                try:
                    select_obj = Select(select_elem)
                    options = [opt.text.strip() for opt in select_obj.options if opt.text.strip()]
                    log(f"    Opciones: {options[:5]}")  # Solo mostrar primeras 5
                except Exception as e:
                    log(f"    No se pudieron obtener opciones: {e}")
                    
            except Exception as e:
                log(f"    Error analizando select {i}: {e}")
        
        return {
            "inputs": inputs,
            "selects": selects, 
            "buttons": buttons
        }
        
    except Exception as e:
        log(f" Error en análisis DOM: {e}")
        return None

def buscar_filtros_inteligente(driver):
    """Busca filtros usando estrategias inteligentes basadas en análisis DOM"""
    log(" Iniciando búsqueda inteligente de filtros...")
    
    # Analizar DOM primero
    elementos = analizar_dom_pagina(driver)
    if not elementos:
        return False
    
    filtros_aplicados = []
    
    # Estrategia 1: Buscar campo de nombre/texto
    log("🔍 Estrategia 1: Buscando campo de texto para nombre...")
    nombre_aplicado = False
    
    for input_elem in elementos["inputs"]:
        try:
            input_type = input_elem.get_attribute("type")
            input_id = input_elem.get_attribute("id") or ""
            input_placeholder = input_elem.get_attribute("placeholder") or ""
            input_name = input_elem.get_attribute("name") or ""
            
            # Verificar si es un campo de texto relevante
            if input_type in ["text", "search"]:
                # Buscar indicadores de que es un campo de nombre
                indicadores_nombre = ["name", "nombre", "client", "cliente", "search", "buscar", "filter", "filtro"]
                
                texto_completo = f"{input_id} {input_placeholder} {input_name}".lower()
                
                if any(indicador in texto_completo for indicador in indicadores_nombre):
                    try:
                        # Verificar que el elemento esté visible y habilitado
                        if input_elem.is_displayed() and input_elem.is_enabled():
                            log(f" Campo de nombre encontrado: id='{input_id}', placeholder='{input_placeholder}'")
                            
                            # Limpiar y enviar texto
                            input_elem.clear()
                            time.sleep(0.5)
                            input_elem.send_keys("Ruben")
                            time.sleep(1)
                            
                            log(" Filtro por nombre 'Ruben' aplicado exitosamente")
                            filtros_aplicados.append("Nombre: Ruben")
                            nombre_aplicado = True
                            break
                            
                    except Exception as e:
                        log(f" Error aplicando filtro en campo {input_id}: {e}")
                        continue
                        
        except Exception as e:
            log(f" Error procesando input: {e}")
            continue
    
    if not nombre_aplicado:
        # Fallback: intentar con el primer campo de texto visible
        log(" Fallback: Intentando con primer campo de texto visible...")
        for input_elem in elementos["inputs"]:
            try:
                if (input_elem.get_attribute("type") in ["text", "search"] and 
                    input_elem.is_displayed() and input_elem.is_enabled()):
                    
                    input_elem.clear()
                    input_elem.send_keys("Ruben")
                    log(" Filtro por nombre aplicado en primer campo disponible")
                    filtros_aplicados.append("Nombre: Ruben (fallback)")
                    nombre_aplicado = True
                    break
            except:
                continue
    
    # Estrategia 2: Buscar dropdown de estado
    log("🔍 Estrategia 2: Buscando dropdown de estado...")
    estado_aplicado = False
    
    for select_elem in elementos["selects"]:
        try:
            select_id = select_elem.get_attribute("id") or ""
            select_name = select_elem.get_attribute("name") or ""
            select_class = select_elem.get_attribute("class") or ""
            
            # Buscar indicadores de estado
            indicadores_estado = ["status", "estado", "state", "condition", "condicion"]
            texto_completo = f"{select_id} {select_name} {select_class}".lower()
            
            if any(indicador in texto_completo for indicador in indicadores_estado):
                try:
                    if select_elem.is_displayed() and select_elem.is_enabled():
                        log(f" Dropdown de estado encontrado: id='{select_id}'")
                        
                        select_obj = Select(select_elem)
                        options = [opt.text.strip() for opt in select_obj.options if opt.text.strip()]
                        log(f"📋 Opciones disponibles: {options}")
                        
                        # Buscar opción "Activo" o similar
                        opcion_seleccionada = None
                        for option_text in options:
                            if any(palabra in option_text.lower() for palabra in ["activo", "active", "habilitado", "enabled"]):
                                select_obj.select_by_visible_text(option_text)
                                opcion_seleccionada = option_text
                                break
                        
                        if not opcion_seleccionada and len(options) > 1:
                            # Seleccionar segunda opción como fallback
                            select_obj.select_by_index(1)
                            opcion_seleccionada = options[1]
                        
                        if opcion_seleccionada:
                            log(f" Estado '{opcion_seleccionada}' seleccionado")
                            filtros_aplicados.append(f"Estado: {opcion_seleccionada}")
                            estado_aplicado = True
                            break
                            
                except Exception as e:
                    log(f" Error aplicando filtro de estado: {e}")
                    continue
                    
        except Exception as e:
            log(f" Error procesando select: {e}")
            continue
    
    # Aplicar filtros (buscar botón o presionar Enter)
    if filtros_aplicados:
        log(" Aplicando filtros...")
        
        # Buscar botón de aplicar
        aplicado = False
        for button in elementos["buttons"]:
            try:
                button_text = button.text.lower() if button.text else ""
                button_value = (button.get_attribute("value") or "").lower()
                button_id = (button.get_attribute("id") or "").lower()
                
                if any(palabra in f"{button_text} {button_value} {button_id}" 
                       for palabra in ["aplicar", "apply", "buscar", "search", "filtrar", "filter"]):
                    
                    if button.is_displayed() and button.is_enabled():
                        if click_seguro(driver, button, "botón aplicar filtros"):
                            aplicado = True
                            break
                            
            except Exception as e:
                continue
        
        # Si no hay botón, presionar Enter en el último campo modificado
        if not aplicado and nombre_aplicado and elementos["inputs"]:
            try:
                elementos["inputs"][0].send_keys(Keys.RETURN)
                log(" Filtros aplicados con Enter")
                aplicado = True
            except:
                pass
        
        time.sleep(3)  # Esperar a que se procesen los filtros
    
    return filtros_aplicados

def crear_filtro_clientes(driver):
    """Función principal para crear filtro de clientes con estrategias mejoradas"""
    
    log("=" * 50)
    log(" INICIANDO CREACIÓN DE FILTRO PARA CLIENTES")
    log("=" * 50)
    
    if not verificar_sesion_activa(driver):
        log(" Sesión no activa al iniciar filtros")
        return False
    
    # 1. Navegar a la sección de Clientes con múltiples estrategias
    clientes_encontrado = False
    
    # Estrategia 1: Buscar en menú lateral
    log(" Estrategia 1: Buscando menú de Clientes...")
    selectores_clientes = [
        "//span[contains(text(),'Clientes')]",
        "//a[contains(text(),'Clientes')]", 
        "//*[contains(@class,'menu') and contains(text(),'Clientes')]",
        "//li[contains(text(),'Clientes')]",
        "//*[@href*='Clientes' or @href*='clientes']",
        "//nav//a[contains(text(),'Clientes')]",
        "//*[contains(@id,'Clientes') or contains(@id,'clientes')]"
    ]
    
    for selector in selectores_clientes:
        try:
            log(f" Probando selector: {selector}")
            clientes_menu = driver.find_element(By.XPATH, selector)
            if clientes_menu and clientes_menu.is_displayed():
                if click_seguro(driver, clientes_menu, "menú Clientes"):
                    log(" Acceso a Clientes exitoso")
                    clientes_encontrado = True
                    time.sleep(5)  # Esperar carga de página
                    break
        except Exception as e:
            log(f" Selector {selector} falló: {e}")
            continue
    
    # Estrategia 2: Navegación directa por URL
    if not clientes_encontrado:
        try:
            log(" Estrategia 2: Navegación directa a Clientes...")
            urls_clientes = [
                "https://csl-tst.outsystemsenterprise.com/FacturaZen/Clientes",
                "https://csl-tst.outsystemsenterprise.com/FacturaZen/clientes",
                "https://csl-tst.outsystemsenterprise.com/FacturaZen/Customers"
            ]
            
            for url in urls_clientes:
                try:
                    driver.get(url)
                    time.sleep(5)
                    
                    # Verificar que llegamos a la página correcta
                    if ("clientes" in driver.current_url.lower() or 
                        "customers" in driver.current_url.lower() or
                        "clientes" in driver.title.lower()):
                        log(f" Navegación directa exitosa: {url}")
                        clientes_encontrado = True
                        break
                except Exception as e:
                    log(f"Error con URL {url}: {e}")
                    continue
                    
        except Exception as e:
            log(f" Error en navegación directa: {e}")
    
    if not clientes_encontrado:
        log(" No se pudo acceder a la sección de Clientes")
        return False
    
    tomar_screenshot(driver, "clientes_seccion")
    
    # 2. Esperar a que la página cargue completamente
    log(" Esperando carga completa de la página...")
    time.sleep(5)
    
    # 3. Aplicar filtros usando búsqueda inteligente
    filtros_aplicados = buscar_filtros_inteligente(driver)
    
    # 4. Verificar resultados
    log(" Verificando resultados...")
    time.sleep(3)
    
    try:
        # Buscar tabla o contenedor de resultados
        contenedores_resultado = [
            "//table",
            "//div[contains(@class,'table')]",
            "//div[contains(@class,'grid')]",
            "//div[contains(@class,'list')]",
            "//ul[contains(@class,'list')]"
        ]
        
        elementos_encontrados = 0
        for contenedor in contenedores_resultado:
            try:
                elementos = driver.find_elements(By.XPATH, contenedor)
                elementos_encontrados += len(elementos)
            except:
                continue
        
        log(f" Elementos de resultado encontrados: {elementos_encontrados}")
        
    except Exception as e:
        log(f" Error verificando resultados: {e}")
    
    # 5. Documentar resultados
    log("=" * 50)
    log(" RESUMEN DE FILTROS APLICADOS:")
    if filtros_aplicados:
        for i, filtro in enumerate(filtros_aplicados, 1):
            log(f"   {i}. {filtro}")
        log(f" Total de filtros aplicados: {len(filtros_aplicados)}")
        exito = True
    else:
        log("    No se aplicaron filtros específicos")
        exito = False
    log("=" * 50)
    
    tomar_screenshot(driver, "filtros_resultado_final")
    
    return exito

def configurar_chrome_driver():
    """Configura el driver de Chrome con opciones optimizadas"""
    chrome_options = Options()
    
    # Opciones básicas de estabilidad
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    # Opciones para evitar detección de automatización
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Configuración de ventana
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Configuración de logging para reducir ruido
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    return chrome_options

# EJECUCIÓN PRINCIPAL
driver = None
try:
    log(" INICIANDO PRUEBA DE QA AUTOMATION - FACTURAZEN")
    log("=" * 60)
    log(" Objetivo: Crear filtro para clientes con estrategias mejoradas")
    log("=" * 60)

    # Configuración mejorada del navegador
    log(" Configurando Chrome driver...")
    chrome_options = configurar_chrome_driver()
    
    # Verificar que el driver existe
    driver_path = "C:/drivers/chromedriver.exe"
    if not os.path.exists(driver_path):
        log(f" Error: No se encuentra chromedriver en {driver_path}")
        log(" Asegúrate de que chromedriver.exe esté en esa ruta")
        raise FileNotFoundError("ChromeDriver no encontrado")
    
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Configuración adicional post-inicialización
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.implicitly_wait(10)
    
    log(" Chrome driver configurado exitosamente")

    # 1. Acceso a la plataforma
    log(" Accediendo a FacturaZen...")
    driver.get("https://csl-tst.outsystemsenterprise.com/FacturaZen")
    time.sleep(5)
    tomar_screenshot(driver, "01_login_page")

    # 2. Login con verificación mejorada
    log(" Realizando login...")
    
    usuario_input = esperar_y_buscar_elemento(driver, By.ID, "b1-Input_Username", 15, "campo de usuario")
    if usuario_input:
        usuario_input.clear()
        usuario_input.send_keys("ventas-demo@centaurosolutions.com")
        log(" Usuario ingresado")
    else:
        log(" No se pudo encontrar el campo de usuario")
        raise Exception("Campo de usuario no encontrado")

    contrasena_input = esperar_y_buscar_elemento(driver, By.ID, "b1-Input_Password", 10, "campo de contraseña")
    if contrasena_input:
        contrasena_input.clear()
        contrasena_input.send_keys("Prueba123")
        log(" Contraseña ingresada")
    else:
        log(" No se pudo encontrar el campo de contraseña")
        raise Exception("Campo de contraseña no encontrado")

    btn_login = esperar_elemento_clickeable(driver, By.NAME, "LoginBTN", 10, "botón de login")
    if btn_login:
        if click_seguro(driver, btn_login, "botón de login"):
            log(" Login realizado")
            time.sleep(8)  # Tiempo adicional para carga post-login
            tomar_screenshot(driver, "02_post_login")
        else:
            raise Exception("No se pudo hacer click en el botón de login")
    else:
        log("No se pudo encontrar el botón de login")
        raise Exception("Botón de login no encontrado")

    # Verificar que el login fue exitoso
    if "dashboard" in driver.current_url.lower() or "facturazen" in driver.current_url.lower():
        log(" Login verificado exitosamente")
    else:
        log(" Login posiblemente no exitoso, continuando...")

    # 3. Navegar al dashboard
    log(" Navegando al dashboard...")
    dashboard_url = "https://csl-tst.outsystemsenterprise.com/FacturaZen/Dashboard"
    driver.get(dashboard_url)
    time.sleep(5)
    tomar_screenshot(driver, "03_dashboard")

    # 4. EJECUTAR LA PRUEBA PRINCIPAL: Crear filtro para clientes
    exito_filtro = crear_filtro_clientes(driver)
    
    # 5. Resultado final
    log("=" * 60)
    if exito_filtro:
        log("PRUEBA DE QA AUTOMATION COMPLETADA EXITOSAMENTE")
        log(" Se crearon filtros para clientes según los requerimientos")
    else:
        log(" PRUEBA PARCIALMENTE COMPLETADA")
        log(" Se accedió a la plataforma pero hubo issues con los filtros")
    log("=" * 60)

    # Pausa para revisión manual
    log(" Pausa para revisión manual - Presiona Enter para continuar...")
    input()

except Exception as e:
    log(" ERROR CRÍTICO EN LA PRUEBA:")
    log(str(e))
    log(traceback.format_exc())

finally:
    log(" Finalizando prueba...")
    try:
        if driver:
            time.sleep(2)
            driver.quit()
            log(" Navegador cerrado")
    except:
        log(" Error al cerrar navegador")
    
    log(" Logs guardados en: qa_automation_test_log.txt")
    log(" Screenshots guardados como: screenshot_*.png")
    log_file.close()
    
    print("\n" + "="*60)
    print(" PRUEBA DE QA AUTOMATION FINALIZADA")
    print(" Revisa los logs y screenshots para documentación completa")
    print("="*60)