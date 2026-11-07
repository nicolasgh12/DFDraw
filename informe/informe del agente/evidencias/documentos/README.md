# Verificación de Word y PDF

Microsoft Word 16.0 abrió el DOCX en modo editable y registró 24 páginas, cinco tablas nativas y siete figuras. El PDF se exportó desde ese mismo documento. Se reabrió una copia del DOCX y se realizó una segunda exportación para comparar.

Poppler renderizó las dos exportaciones a 144 ppp. Los 24 pares de PNG coincidieron byte a byte y el texto extraído coincidió página a página. La inspección visual de las 24 páginas comprobó la legibilidad de tablas, listados y figuras y la ausencia de páginas en blanco involuntarias. La comparación de canales de color confirmó el uso de escala de grises.

El DOCX incluye seis SVG y siete PNG. La figura S03B utiliza PNG para preservar las etiquetas HTML. Word incorporó las siete figuras como imágenes en el PDF. Las fuentes Mermaid y los SVG de ejecución se conservan por separado. Se intentó el renderizador de LibreOffice, que requiere `soffice.exe`. La verificación se realizó con Word y Poppler.

Los recuentos y SHA-256 están en [comparacion.json](comparacion.json). El registro del exportador está en [word-export.json](word-export.json).
