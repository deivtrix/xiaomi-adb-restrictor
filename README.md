# 📱 Xiaomi/MIUI & HyperOS Background App Restrictor (ADB)

Un panel de control gráfico optimizado para computadoras que te permite gestionar el ahorro de batería y las restricciones de segundo plano de las aplicaciones en teléfonos **Xiaomi, Redmi y POCO** (con MIUI o HyperOS) utilizando comandos ADB a máxima velocidad.

La aplicación cuenta con un asistente inteligente de arranque que **instala de manera automática todas las dependencias (Python y ADB) si no se encuentran en el sistema**, haciendo que sea 100% portable y fácil de usar por cualquier persona con un solo clic.

---

## ⚡ Características Principales

* **🔍 Búsqueda y Filtro en Tiempo Real**: Filtra instantáneamente la lista de aplicaciones de tu celular escribiendo su nombre real o su identificador de paquete (ID).
* **📊 Visualizador de Estados en Vivo**: Consulta directamente del teléfono el modo de ahorro de energía de cada aplicación y lo muestra con badges de colores idénticos a los del sistema:
  * `Sin restricciones` (Verde)
  * `Ahorro de batería (recomendado)` (Gris)
  * `Cerrar tras 10 min` (Naranja)
  * `Restringir en segundo plano` (Morado)
* **🚀 Automatización por Coordenadas (Modo Ultra Rápido)**: Olvídate de esperar clics lentos. El script detecta la resolución física del móvil y realiza toques instantáneos basados en porcentajes de pantalla para configurar cada app en menos de 1.5 segundos.
* **📦 Auto-Instalación de Dependencias**:
  * Si el usuario no tiene Python instalado, `INICIAR.bat` lo descarga e instala de forma silenciosa mediante Winget.
  * Si falta el ejecutable de ADB, el script lo descarga y extrae automáticamente desde los servidores oficiales de Google.
* **🛡️ Control de PowerKeeper**: Activa o restringe el servicio de control térmico de Xiaomi (`com.miui.powerkeeper`) con un solo botón en la barra superior.
* **⚙️ Accesos Directos Individuales**: Haz doble clic en cualquier aplicación de la lista o presiona su icono de engranaje (`⚙️`) para abrir su pantalla de detalles de batería directamente en la pantalla de tu móvil.
* **🎨 Tema Claro Moderno**: Interfaz gráfica limpia y minimalista, optimizada con animaciones al pasar el cursor sobre los botones y tarjetas.

---

## 🛠️ Requisitos previos en el Celular (Xiaomi/MIUI/HyperOS)

Para que el programa pueda realizar toques y configurar los estados automáticamente, debes habilitar los permisos de desarrollo en tu celular:

1. Ve a **Ajustes > Sobre el teléfono** y toca 7 veces seguidas en **"Versión MIUI"** o **"Versión de OS"** para activar las Opciones de Desarrollador.
2. Ve a **Ajustes adicionales > Opciones de desarrollador**.
3. Activa las siguientes opciones:
   * **Depuración USB** (Permite enviar comandos).
   * **Depuración USB (Ajustes de seguridad)** (Permite simular toques de pantalla por código). *Nota: Requiere cuenta Mi activa en algunos modelos.*

---

## 🚀 Cómo usar el Optimizador

1. Conecta tu celular Xiaomi/Redmi/POCO a la computadora mediante un cable USB.
2. Asegúrate de que la pantalla de tu celular esté encendida y desbloqueada.
3. Haz doble clic en el archivo **`INICIAR.bat`** en la carpeta raíz.
4. Si es la primera vez que lo abres en esa PC:
   * Si no tienes Python, el script se instalará automáticamente en unos segundos. Vuelve a hacer doble clic en `INICIAR.bat` al finalizar.
   * Acepta el mensaje emergente de **"Permitir depuración USB"** que aparecerá en la pantalla de tu celular.
5. ¡Listo! Las aplicaciones se listarán solas.
   * Filtra las apps que desees con el buscador.
   * Selecciona las aplicaciones haciendo clic en ellas (se marcarán con un círculo verde `●`).
   * Pulsa el botón de la acción que deseas aplicar en la zona inferior (ej. **`⏳ CERRAR TRAS 10 MIN`**).
   * Verás cómo el celular realiza los pasos de forma automática y la app se tacha en tu pantalla cuando finaliza con éxito.

---

## 📁 Estructura del Proyecto

El repositorio está organizado de forma limpia para facilitar su distribución:

```
├── 📄 INICIAR.bat            # Script de arranque y auto-instalador de Python
└── 📁 recursos               # Contenedor de todos los archivos del sistema
    ├── 📁 adb                # Herramientas ADB de Google (se auto-descarga si falta)
    ├── 📁 src                # Código fuente del script principal (Python)
    ├── 📁 data               # Caché local de nombres de apps (app_names_cache.json)
    ├── 📁 drivers            # Instaladores de drivers USB
    ├── 📁 assets             # Capturas de pantalla e imágenes explicativas
    └── 📄 DKMA_GUI.bat       # Servidor secundario de utilidad de depuración
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Siéntete libre de modificarlo, compartirlo y adaptarlo a tus necesidades.
