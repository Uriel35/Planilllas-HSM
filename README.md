# Planillas PDF

Ejecutar `main.py` desde PyCharm. Requiere Python 3.10 o posterior, Tkinter y las dependencias de `requirements.txt`.

Para distribuirla como aplicación en **Windows 10/11 x64**, ver [la guía de Windows](docs/WINDOWS.md). El repositorio incluye la configuración de PyInstaller y un flujo de GitHub Actions para compilar y probar el ejecutable en Windows. Los usuarios del ejecutable no necesitan instalar Python.

1. Elegí tu perfil profesional o seleccioná **Registrar profesional**, completá tus datos y pulsá **Guardar e ingresar**. Después buscá una planilla por nombre (ignora tildes y mayúsculas).
2. Seleccionala y completá sus campos. Usá la barra lateral del formulario para desplazarte.
3. Pulsá **Guardar PDF** (o **Ctrl+S**) para generar `output/planilla_llena.pdf` y actualizar el visor integrado. **Abrir PDF (Ctrl+O)** abre el último archivo guardado en el visor externo, sin volver a generarlo.

El PDF conserva el diseño de la plantilla y fija los datos para visualizar e imprimir. La plantilla original se conserva. Los formularios recuperan los borradores guardados; si no hay datos previos, comienzan vacíos.

## Organización del proyecto

```text
main.py                 Entrada de la aplicación (ejecutar desde PyCharm)
app/
  application.py        Ventana principal y generación de PDFs
  paths.py              Rutas compartidas, independientes del directorio de ejecución
  forms/                Definiciones de campos y formularios específicos
  ui/                   Tema, casillas, atajos, buscadores, diálogos y visor
  services/             Datos del paciente, profesionales, firmas y guardado
resources/
  templates/            PDFs rellenables utilizados por la aplicación
  originals/            PDFs base, respaldos originales y planillas aún sin configurar
  fields/               Definiciones de campos en JSON
scripts/                Herramientas para construir las plantillas
packaging/              Configuración del ejecutable de PyInstaller
.github/workflows/      Compilación y pruebas automáticas en Windows
docs/                   Guía de distribución para Windows
tests/                 Pruebas automáticas
data/                   Borradores, perfiles y firmas locales
output/                 PDFs generados
```

Para iniciar, seguí ejecutando `main.py`; la lógica principal está en `app/application.py`. El PDF generado se guarda en `output/planilla_llena.pdf`. Los borradores y perfiles existentes se trasladaron a `data/` conservando su contenido.

Desde la raíz del proyecto, con su intérprete Python:

```bash
python main.py
python -m unittest discover -s tests -v
python -m scripts.build_cisticercosis_fields
python -m scripts.form_tools --help
```

Los generadores se ejecutan como módulos (`python -m scripts.nombre_del_script`). En una configuración de PyCharm, elegir **Module name** y escribir, por ejemplo, `scripts.build_cisticercosis_fields`, con la raíz del proyecto como directorio de trabajo. Los generadores de hidatidosis y PCR producen el JSON de campos; `scripts.form_tools add` permite aplicarlo al PDF correspondiente.

`data/`, `output/`, el entorno virtual y las cachés están excluidos de Git. Para trasladar el proyecto conservando perfiles y borradores, copiar también `data/`.

Las carpetas `build/` y `dist/` y las antiguas ubicaciones de datos personales también están excluidas. Estas reglas no retiran archivos que ya estuvieran versionados: comprobar la lista de archivos preparados antes del primer push. La configuración del ejecutable tampoco incluye datos personales. En la aplicación empaquetada para Windows, los archivos modificables se guardan en `%LOCALAPPDATA%\PlanillasPDF`; las rutas locales de esta guía corresponden a la ejecución desde el código fuente.

## Ingreso del profesional

El ingreso identifica un perfil local, sin contraseña ni autenticación. Los perfiles se guardan en `data/profesionales.json`. Apellido y nombre son obligatorios; matrícula, especialidad, contacto y establecimiento son opcionales. Podés registrar varios profesionales y usar **Cambiar / editar profesional** desde la barra lateral.

Se autocompletan los campos profesionales equivalentes de hidatidosis, toxoplasmosis y PCR de virus. El contacto institucional de PCR se carga separado del contacto personal. Matrícula y especialidad se conservan en el perfil para futuras plantillas; las actuales no tienen campos específicos para ellos. Orden de internación y Film Array no tienen equivalencias de texto profesional configuradas, pero admiten insertar la firma PNG.

Podés corregir los datos en cada formulario sin modificar el perfil. Al ingresar, cambiar o editar al profesional, se actualizan los campos profesionales de los borradores con el perfil elegido, incluidos los valores vacíos. Los datos del paciente y sus borradores son compartidos en este equipo, no se separan por profesional. **Reiniciar datos** limpia el paciente y vuelve a completar los datos del profesional activo; conserva todos los perfiles.

Los cambios se guardan al presionar Enter, Tab o Shift+Tab en los campos del formulario, al cambiar de planilla, al guardar el PDF y al cerrar, en `data/datos_formularios.json`. No hay un temporizador de guardado. Incluye datos compartidos, textos, casillas y la última planilla seleccionada. No hace falta generar un PDF para conservar los datos. Si falla el guardado al cerrar, la ventana permanece abierta y muestra el error. Si el JSON está dañado, el programa informa el problema y conserva el archivo sin sobrescribirlo.

Incluye hidatidosis, toxoplasmosis, orden de internación, PCR de virus, Film Array y GenXpert, si sus archivos están disponibles. Para agregar otra planilla, primero debe tener campos PDF configurados y luego agregarse a `TEMPLATES` en `app/application.py`. Copiar un PDF escaneado a `resources/originals/` no configura automáticamente sus casilleros.

### GenXpert

`resources/originals/GenXpert_planilla.pdf` conserva la primera página y reemplaza el instructivo de la segunda por una hoja con el título «Resumen de historia clinica». El original se conserva en `resources/originals/GenXpert_planilla_original.pdf`.

La aplicación usa `resources/templates/GenXpert_planilla_rellenable.pdf`: incluye los datos de la institución y del paciente, muestras, antecedentes, solicitud, firma PNG y un campo amplio para el resumen de historia clínica. Las preguntas sobre cultivo solicitado y tratamiento previo usan Sí / No / Sin indicar. El resumen puede dejarse vacío para completarlo a mano. Los datos equivalentes del paciente y del profesional se reutilizan entre planillas; el documento se carga como tipo y número.

Las posiciones y rótulos están en `app/forms/genxpert_fields.py`. `python -m scripts.build_genxpert_fields` permite regenerar ambos PDFs y conserva la copia original existente.

### Cisticercosis — envío de muestras

Incluye las dos páginas de `resources/originals/cisticercosis_planilla.pdf`: eventos sospechados, muestras, paciente, clínica, laboratorio, imágenes, epidemiología, sección de triquinosis y médico tratante. Comparte los datos equivalentes del paciente y profesional, guarda borradores y permite insertar la firma PNG. Las preguntas Sí/No permiten dejarlas sin indicar. Los estadios hepáticos elegidos se rodean con un círculo en el PDF.

Los campos están en `app/forms/cisticercosis_fields.py`. Ejecutar `python -m scripts.build_cisticercosis_fields` regenera `resources/templates/cisticercosis_planilla_rellenable.pdf` sin modificar el original.

### TBC — cultivo

Disponible en el selector como **TBC — cultivo**. `resources/templates/TBC_cultivo_rellenable.pdf` conserva el escaneo de `resources/originals/TBC_cultivo.pdf` y agrega los datos del paciente, derivación, baciloscopía, cultivo, prueba de sensibilidad y firma PNG. Reutiliza los datos personales equivalentes y el nombre del profesional. Sexo y tratamiento previo permiten dejar la respuesta sin indicar. Las posiciones y rótulos están en `app/forms/tbc_cultivo_fields.py`; `python -m scripts.build_tbc_cultivo_fields` regenera la versión rellenable sin modificar el original.

### TARV — recetario

Ingresá nombre(s), apellido(s), sexo M/F y fecha de nacimiento (DD/MM/AAAA). El código se calcula automáticamente: sexo + primeras dos letras del primer nombre + primeras dos letras del apellido + nacimiento en DDMMYYYY, en mayúsculas y sin tildes. Por ejemplo, Juan Carlos Pérez, M, 03/07/1985 produce **MJUPE03071985**. Estos datos se guardan y se comparten con los campos equivalentes de las demás planillas. El código aparece como solo lectura; si faltan datos o la fecha es inválida, se indica qué completar. Los nombres completos se conservan en el borrador; en el PDF se imprime el código.

Código y DNI se comparten entre las dos recetas; el DNI también se reutiliza con las planillas equivalentes. Con **Son iguales** activado, se copia la medicación, otros medicamentos y las casillas de la primera receta a la segunda, cuya fecha es un mes calendario posterior. Si el día no existe en el mes siguiente, se usa el último día de ese mes. La fecha se ingresa como DD/MM/AAAA; si se deja vacía, ambas fechas quedan vacías.

Al desactivar **Son iguales**, aparece el formulario de la segunda receta con su propia fecha, motivo y medicación. Ese borrador se conserva al volver a activar la opción y al cerrar la aplicación. **Reiniciar datos** vacía ambas recetas y activa nuevamente **Son iguales**.

**Inicio**, **Cambio de tratamiento**, **Continuación** y **Excepción al PUCO** son botones de selección única. Con recetas iguales, Inicio y Cambio de tratamiento pasan a Continuación en las siguientes recetas; Continuación y Excepción al PUCO se mantienen.

**Meses** indica el total de recetas: 2 genera una hoja, 4 genera dos, 6 genera tres, 8 genera cuatro, 10 genera cinco y 12 genera seis. Las fechas se calculan desde la fecha original para conservar el día cuando existe en el mes correspondiente. Con recetas diferentes, cada hoja adicional repite las dos medicaciones y suma dos meses a sus fechas; Inicio y Cambio pasan a Continuación en las hojas siguientes. El borrador conserva la selección de meses; reiniciar vuelve a 2.

Cada fila de medicación tiene un buscador por nombre o dosis: escribí, seleccioná un resultado con clic o con ↓ y Enter, y usá **Agregar medicamento** para otra fila. **Quitar** desmarca el medicamento. No se permiten selecciones duplicadas dentro de una receta; escribir una búsqueda sin elegir un resultado no cambia la selección previa.

Los medicamentos elegidos se marcan con **X** en la columna «Comprimidos/mes» de la receta correspondiente. La presentación impresa se muestra como referencia; no se calculan cantidades ni dosis. Los cuatro renglones de **Otros medicamentos** permiten cargar medicamento, dosis diaria y días de tratamiento. Las selecciones se guardan en el borrador, se recuperan al volver y se eliminan con **Reiniciar datos**. La firma PNG se inserta en cada receta de todas las hojas, ampliada y desplazada sobre el rótulo «Firma y sello del médico», que conserva su ubicación original.

`python -m scripts.build_tarv_fields` genera `resources/templates/TARV_recetario_rellenable.pdf` a partir de `resources/originals/TARV_recetario.pdf`, sin modificar el original. El catálogo y las posiciones están en `app/forms/tarv_fields.py`.

### HIV — carga viral y CD4/CD8

Incluye institución, documento, código automático, diagnóstico o seguimiento, gestación, carga viral, CD4/CD8, datos de laboratorio, observaciones, fecha y firma PNG. El código usa la misma regla de TARV y se imprime separado en los cuatro casilleros del PDF. Nombre(s), apellido(s), sexo, nacimiento y DNI se comparten con las planillas equivalentes. La región sanitaria predeterminada es **XI** y el establecimiento **Hospital San Martin de La Plata**; ambos se pueden editar. Diagnóstico/seguimiento y gestante sí/no usan botones de selección única. El correo se calcula automáticamente: **resultadoshivsanmartin@gmail.com** para diagnóstico y **seguimientohivhsm@gmail.com** para seguimiento; queda vacío sin selección. El perfil profesional no reemplaza estos valores. Carga viral y CD4/CD8 se pueden marcar juntos. Los campos de laboratorio pueden dejarse vacíos.

`python -m scripts.build_hiv_fields` genera `resources/templates/planilla_HIV_carga_viral_CD4_rellenable.pdf` a partir de `resources/originals/planilla_HIV_carga_viral_CD4.pdf` sin modificar el original. Los campos están en `app/forms/hiv_fields.py`.

Al elegir **Seguimiento**, aparecen **IUA carga viral** e **IUA CD4** junto a cada estudio. Admiten códigos numéricos, conservan ceros iniciales y se imprimen junto a la determinación como «IUA carga viral: 12345678» o «IUA CD4: 12345678». Son opcionales. En Diagnóstico se ocultan y no se imprimen; sus valores se conservan en el borrador por si volvés a Seguimiento.

Revisá el PDF generado antes de utilizarlo, especialmente textos extensos en casilleros pequeños. Podés insertar una imagen de firma o firmar a mano; no se realiza firma digital criptográfica.

## Visor integrado

A la derecha se muestra la plantilla de referencia al seleccionar un formulario. Al pulsar **Guardar PDF**, el visor muestra el archivo generado. Enter y Tab guardan únicamente los datos: no generan ni actualizan el PDF. Los cambios de profesional o firma tampoco actualizan el visor hasta guardar el PDF. Todas las páginas se muestran una debajo de otra y se recorren con scroll; **+**, **−** y **Ajustar** controlan el zoom. Arrastrá el divisor para distribuir el espacio. Cada panel se desplaza por separado.

El visor lee directamente la plantilla o el PDF guardado. **Guardar PDF** no abre ventanas externas; usá **Abrir PDF (Ctrl+O)** cuando lo necesites.

## Firma PNG

En **Cambiar / editar profesional**, usá **Cargar PNG de firma** y después **Guardar e ingresar**. Podés ver, reemplazar o quitar la imagen desde el mismo perfil. El PNG se guarda dentro de `data/profesionales.json`, por lo que no depende de conservar el archivo original en su ubicación. Admite hasta 2 MB y 16 millones de píxeles; conviene usar una imagen recortada alrededor de la firma, con fondo transparente.

La opción **Incluir firma PNG en el PDF** permite generar cada PDF con o sin la imagen. Al ingresar o cambiar de profesional, se activa si ese perfil tiene una firma. Se inserta conservando sus proporciones en hidatidosis, PCR, las dos copias de la orden de internación y el casillero del profesional solicitante de Film Array. El casillero de autorización de Film Array se deja libre. Toxoplasmosis no tiene un espacio de firma y la opción queda deshabilitada. En PCR se conserva el campo de aclaración y la imagen se coloca debajo.

Reiniciar los datos del paciente conserva la firma del perfil. Las plantillas originales no se modifican.

## Atajos de teclado

- **Ctrl+F**: enfocar el buscador y seleccionar su texto.
- **Ctrl+A**: seleccionar todo el texto del campo activo, incluidos campos de varias líneas, buscadores, diálogos y campos creados dinámicamente.
- **Ctrl+← / Ctrl+→**: mover el cursor palabra por palabra en todos los campos de texto, incluidos buscadores y diálogos.
- **Ctrl+Shift+← / Ctrl+Shift+→**: seleccionar texto por palabras.
- **Ctrl+R**: reiniciar todos los datos de los formularios y del JSON guardado.
- **↓** desde el buscador: entrar a los resultados; **↑ / ↓** para recorrerlos.
- **Enter** desde el buscador o la lista: comenzar a completar el formulario.
- **Esc** en el buscador: limpiar la búsqueda.
- **Tab / Shift+Tab**: campo siguiente / anterior; el formulario se desplaza para mostrar el campo enfocado.
- **Espacio**: marcar o desmarcar la casilla enfocada.
- **Enter** en un campo de varias líneas: insertar una nueva línea.
- **Enter** en un campo de una línea: guardar los datos y avanzar como con Tab. Tab y Shift+Tab también guardan; Enter en campos de varias líneas guarda después de insertar el salto.
- **Ctrl+S**: guardar PDF.
- **Ctrl+O**: abrir el último PDF guardado en el visor externo.
- **Ctrl+Q**: guardar los datos y cerrar.
- **F1**: mostrar la ayuda de atajos.

## Datos compartidos del paciente

Los datos personales se reutilizan al cambiar de planilla, incluso antes de guardar. Las equivalencias están en `app/services/patient_data.py`: hidatidosis, toxoplasmosis, PCR de virus y orden de internación comparten los campos identificados como equivalentes. Film Array mantiene su borrador independiente.

Film Array muestra los rótulos del PDF y se organiza por secciones. El tratamiento antibiótico se carga en una tabla de tres filas; el tratamiento inmunosupresor usa botones Sí / No / Sin indicar, y los paneles y tipos de muestra usan casillas. Las correspondencias están en `app/forms/film_array_fields.py`, conservando las claves originales para recuperar borradores anteriores. Al exportar también se corrigen los valores antiguos incrustados en los campos de fecha, nombre y DNI de la plantilla.

Los campos que combinan apellido y nombres se muestran como dos entradas: **Apellido(s)** y **Nombre(s)**. Se unen al generar el PDF. Las correcciones y los borrados se transmiten a las demás planillas al abrirlas; los datos clínicos y otros campos particulares conservan su propio borrador.

**Reiniciar datos**, junto a Guardar, vacía todos los borradores, los datos compartidos y las casillas para iniciar un nuevo paciente. También actualiza el JSON para que el paciente anterior no reaparezca al abrir. Reiniciar no borra el PDF ya generado; el próximo guardado lo reemplaza.
