param(
    [string]$Docx = (Join-Path $PSScriptRoot 'Informe_Compiladores.docx'),
    [string]$Pdf = (Join-Path $PSScriptRoot 'Informe_Compiladores.pdf')
)

$ErrorActionPreference = 'Stop'
$docxPath = (Resolve-Path -LiteralPath $Docx).Path
$pdfPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Pdf)
$word = New-Object -ComObject Word.Application
$document = $null
try {
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($docxPath, $false, $false, $false)
    $document.Repaginate()
    $document.ExportAsFixedFormat($pdfPath, 17)
    [pscustomobject]@{
        Word = $word.Version
        Build = $word.Build
        Paginas = $document.ComputeStatistics(2)
        SoloLectura = $document.ReadOnly
        Proteccion = $document.ProtectionType
        Tablas = $document.Tables.Count
        Figuras = $document.InlineShapes.Count
    } | ConvertTo-Json -Compress
} finally {
    if ($null -ne $document) {
        $document.Close(0)
    }
    $word.Quit(0)
}
