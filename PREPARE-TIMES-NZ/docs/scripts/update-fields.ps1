param(
  [Parameter(Mandatory=$true)]
  [string]$DocPath
)

$ErrorActionPreference = "Stop"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
  # Open (ReadOnly=false so we can save)
  $doc = $word.Documents.Open($DocPath, $false, $false)

  # Update main story fields (TOC, refs, etc.)
  $doc.Fields.Update() | Out-Null

  # Update headers/footers too (document title fields often live here)
  foreach ($section in $doc.Sections) {
    foreach ($h in $section.Headers) { $h.Range.Fields.Update() | Out-Null }
    foreach ($f in $section.Footers) { $f.Range.Fields.Update() | Out-Null }
  }

  # If you have a TOC, explicitly refresh it as well
  if ($doc.TablesOfContents.Count -gt 0) {
    for ($i=1; $i -le $doc.TablesOfContents.Count; $i++) {
      $doc.TablesOfContents.Item($i).Update() | Out-Null
    }
  }

  $doc.Save()
  $doc.Close()
}
finally {
  $word.Quit()
}
