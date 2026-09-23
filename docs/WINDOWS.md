# Planillas PDF para Windows

Objetivo de esta distribución: **Windows 10/11 de 64 bits (x64)**. Windows 7/8 y Windows de 32 bits no están contemplados en esta compilación. El ejecutable incluye Python, Tkinter, PyMuPDF y las plantillas; los destinatarios no necesitan instalar Python ni PyCharm.

## Usar la aplicación recibida

1. Extraer **todo** el ZIP a una carpeta.
2. Abrir `PlanillasPDF.exe`. Conservar junto a él la carpeta `_internal`; no copiar solamente el `.exe`.
3. Registrar el perfil profesional y completar las planillas.
4. Usar **Guardar PDF** y **Abrir PDF** como en la versión de desarrollo.

La vista previa funciona sin un visor externo. **Abrir PDF** utiliza el visor predeterminado de Windows.

El ejecutable guarda los datos de cada usuario en:

```text
%LOCALAPPDATA%\PlanillasPDF\data\datos_formularios.json
%LOCALAPPDATA%\PlanillasPDF\data\profesionales.json
%LOCALAPPDATA%\PlanillasPDF\output\planilla_llena.pdf
```

Podés pegar `%LOCALAPPDATA%\PlanillasPDF` en la barra del Explorador de archivos. No hacen falta permisos de administrador. Actualizar la carpeta del programa no reemplaza estos datos. Para hacer un respaldo, cerrar la aplicación y copiar su carpeta `data`. Una copia nueva del programa no incluye los perfiles ni pacientes del desarrollador.

Si el PDF está abierto y el visor impide reemplazarlo, cerrarlo y volver a guardar. Las pruebas automatizadas no sustituyen la comprobación visual de impresión, firma y escala de pantalla en los equipos de destino.

## Obtener el ZIP desde GitHub

El repositorio incluye `.github/workflows/windows.yml`. Al subirlo a GitHub, el flujo **Aplicación Windows** ejecuta las pruebas en `windows-2022` con Python 3.12 x64, construye el paquete y prueba el ejecutable. No publica una Release automáticamente.

1. Abrir **Actions → Aplicación Windows**.
2. Esperar a que la ejecución termine correctamente. También se puede iniciar con **Run workflow**.
3. Descargar el artefacto **PlanillasPDF-Windows-x64** desde la sección **Artifacts** de esa ejecución.
4. Compartir el ZIP completo. Los artefactos se conservan durante 14 días; conservar una copia si se necesita distribuirla después.

El flujo exige una pantalla Tk para las pruebas de teclado: no las omite silenciosamente en Windows. Además ejecuta `PlanillasPDF.exe --self-test informe.json` con datos sintéticos en una carpeta temporal y verifica las 12 variantes de formulario, guardado JSON, casillas y vista previa PDF.

## Compilar manualmente en Windows

Desde PowerShell, ubicado en la raíz del proyecto, con Python 3.12 x64 instalado:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean packaging/PlanillasPDF.spec
```

La carpeta para distribuir es `dist\PlanillasPDF`. Copiar también este documento dentro de ella y comprimirla completa. El `.spec` incluye únicamente `resources/templates` y `resources/fields`; excluye datos locales, PDFs completados, originales, ejemplos y pruebas.

Para verificar el paquete antes de compartirlo:

```powershell
$report = Join-Path $env:TEMP 'planillas-prueba.json'
$exe = (Resolve-Path '.\dist\PlanillasPDF\PlanillasPDF.exe').Path
$p = Start-Process $exe -ArgumentList @('--self-test', "`"$report`"") -Wait -PassThru
if ($p.ExitCode -ne 0) { throw 'Falló la prueba del ejecutable' }
Get-Content $report
```

El informe debe indicar `"ok": true` y `"templates": 12`.

## Estado de la compatibilidad

Se corrigieron las rutas de escritura para el ejecutable, la selección de fuente en Windows, los enlaces de rueda del mouse según el sistema de ventanas y el mensaje para PDFs bloqueados por un visor externo. La versión de desarrollo sigue usando `data/` y `output/` dentro del proyecto.

La comprobación local se hizo en Linux. La compatibilidad Windows queda pendiente hasta que el flujo termine correctamente y se haga una prueba manual en un equipo Windows 10/11. No se ha generado ni ejecutado un `.exe` de Windows en este entorno.

PyInstaller requiere compilar en el sistema de destino: [documentación oficial](https://www.pyinstaller.org/en/stable/). La separación entre recursos empaquetados y archivos del usuario sigue su [documentación de rutas en ejecución](https://pyinstaller.org/en/stable/runtime-information.html).
