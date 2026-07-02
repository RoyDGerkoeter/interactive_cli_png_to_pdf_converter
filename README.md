interactive cli png -> pdf converter

ein kleines, interaktives kommandozeilen-tool das png-bilder aus einem ordner
verlustfrei in pdf-dateien umwandelt und sie auf wunsch zu einer einzigen pdf
zusammenfuegt. es fragt jeden schritt einzeln nach, man muss sich also keine
kryptischen optionen merken.

die bilddaten werden mit img2pdf unveraendert eingebettet. viele andere
bibliotheken kodieren die bilder beim pdf-export verlustbehaftet als jpeg neu,
dadurch leidet die qualitaet von dokumentenscans an text und kanten. hier
bleibt die qualitaet erhalten.


installation und ausfuehrung

voraussetzung: python 3.10 oder neuer.

variante a - mit uv (empfohlen, kein setup noetig):

  uv run png_to_pdf.py

uv liest die im skript hinterlegten abhaengigkeiten (pep 723) und installiert
sie automatisch in einer isolierten umgebung. mehr zu uv:
https://docs.astral.sh/uv/

variante b - mit pip:

  pip install -r requirements.txt
  python png_to_pdf.py

bei bedarf vorher eine virtuelle umgebung anlegen:

  python -m venv .venv
  source .venv/bin/activate        (windows: .venv\Scripts\activate)
  pip install -r requirements.txt
  python png_to_pdf.py


ablauf

das skript fragt nacheinander:

  1. ordner mit den png-dateien (standard: ordner des skripts)
  2. reihenfolge der seiten - standardmaessig "natuerlich" sortiert
     (seite2 vor seite10), auf wunsch manuell per nummern anpassbar
  3. aufloesung in dpi - bestimmt die physische seitengroesse (standard: 150)
  4. ob bestehende dateien ueberschrieben werden sollen (sonst automatisch
     ein freier name)
  5. ob die einzelseiten zu einer pdf zusammengefuegt werden sollen
  6. unter welchem namen die zusammengefuegte pdf gespeichert wird
  7. ob die einzelnen pdf-dateien danach geloescht werden sollen

jede png-datei wird zunaechst als gleichnamige pdf gespeichert
(seite1.png wird zu seite1.pdf). pngs mit transparenz werden dabei automatisch
auf weissem hintergrund zusammengefuehrt, weil pdf keine transparenz kennt.

mit strg+c laesst sich das tool jederzeit sauber abbrechen.


lizenz

mit - siehe die datei LICENSE
