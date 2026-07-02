#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "img2pdf>=0.5",
#     "Pillow>=10.0",
# ]
# ///

# kleines skript das png-bilder aus einem ordner in pdf umwandelt
# und die seiten am ende zu einer einzigen pdf zusammenkleben kann.
# wichtig: img2pdf steckt die pngs verlustfrei rein, pillow braucht man
# nur um durchsichtige stellen (transparenz) mit weiss zu fuellen,
# weil pdf keine transparenz kann.

import re      # brauche ich fuer die zahlen-sortierung (regex)
import sys     # damit ich das programm mit einer meldung beenden kann
from io import BytesIO   # damit ich ein bild im speicher halten kann statt als datei
from pathlib import Path  # macht das arbeiten mit datei-pfaden einfacher

import img2pdf          # macht aus bildern eine pdf
from PIL import Image   # pillow, zum bilder oeffnen und bearbeiten


# stellt eine frage und gibt die antwort zurueck.
# wenn man einfach enter drueckt kommt der standard-wert (default) raus.
def ask(prompt, default=None):
    # wenn es einen default gibt, zeige ihn in eckigen klammern an
    suffix = f" [{default}]" if default else ""
    antwort = input(f"{prompt}{suffix}: ").strip()  # .strip() schneidet leerzeichen weg
    # wenn die antwort leer ist nehme ich den default (oder leeren text)
    return antwort or (default or "")


# stellt eine ja/nein frage und gibt True oder False zurueck.
def ask_yes_no(prompt, default=True):
    # der grossgeschriebene buchstabe zeigt an was passiert wenn man nur enter drueckt
    hint = "J/n" if default else "j/N"
    antwort = input(f"{prompt} ({hint}): ").strip().lower()
    if not antwort:          # nichts eingegeben -> nimm den default
        return default
    # wenn der erste buchstabe ein j oder y ist zaehle ich das als ja
    return antwort[0] in ("j", "y")


# hilfs-funktion damit "Seite2" vor "Seite10" kommt.
# normales sortieren wuerde "Seite10" vor "Seite2" packen weil es die
# zeichen einzeln vergleicht ("1" ist kleiner als "2").
def natural_key(path):
    # re.split(r"(\d+)", ...) zerlegt den namen in text- und zahl-stuecke,
    # z.b. "Seite10" wird zu ["Seite", "10", ""]
    teile = re.split(r"(\d+)", path.name)
    # jedes zahl-stueck mache ich zu einer echten zahl (int),
    # den rest schreibe ich klein damit gross/klein egal ist
    return [int(t) if t.isdigit() else t.lower() for t in teile]


# zeigt die gefundenen dateien an und fragt ob die reihenfolge passt.
def choose_order(files):
    print("\ngefundene png-dateien:")
    # enumerate(files, 1) gibt mir eine nummer (ab 1) und die datei dazu
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.name}")

    # wenn die reihenfolge passt gebe ich die liste einfach so zurueck
    if ask_yes_no("\nreihenfolge wie angezeigt uebernehmen?", default=True):
        return files

    # sonst darf der nutzer die nummern selbst angeben, z.b. "2,1"
    raw = ask("reihenfolge als nummern angeben (z. b. 2,1)")
    try:
        # jede zahl aus der eingabe in ein int umwandeln
        picks = [int(x) for x in raw.split(",")]
        # pruefen ob eine zahl ausserhalb liegt (kleiner 1 oder groesser als anzahl)
        if any(n < 1 or n > len(files) for n in picks):
            raise ValueError   # dann werfe ich absichtlich einen fehler
    except ValueError:
        # bei bloedsinniger eingabe bleibe ich einfach bei der alten reihenfolge
        print("ungueltige eingabe - behalte die angezeigte reihenfolge.")
        return files
    # nutzer zaehlt ab 1, die liste ab 0, deshalb n - 1
    return [files[n - 1] for n in picks]


# macht aus einem png etwas das img2pdf verarbeiten kann.
# ohne transparenz gebe ich einfach den datei-pfad weiter (schnell und verlustfrei).
# nur wenn transparenz da ist muss ich das bild vorher "flach" machen.
def pdf_source(png):
    with Image.open(png) as img:
        # hat das bild einen transparenz-kanal?
        # RGBA / LA haben einen alpha-kanal, manche pngs speichern transparenz in info
        if img.mode not in ("RGBA", "LA") and "transparency" not in img.info:
            return str(png)   # keine transparenz -> pfad reicht

        # jetzt das transparente bild auf weissen hintergrund legen:
        rgba = img.convert("RGBA")               # sicherstellen dass ein alpha-kanal da ist
        flat = Image.new("RGB", rgba.size, "white")   # ein neues weisses bild in gleicher groesse
        # paste mit mask klebt das bild drauf und nutzt die transparenz als schablone
        flat.paste(rgba, mask=rgba.split()[-1])

    # das fertige bild lege ich in den speicher (nicht auf die festplatte)
    buf = BytesIO()
    flat.save(buf, format="PNG")
    return buf.getvalue()   # die rohen bytes gebe ich zurueck


# baut den ziel-pfad fuer eine neue datei.
# wenn die datei schon existiert frage ich ob ich sie ueberschreiben darf,
# sonst suche ich einen freien namen mit _1, _2, ...
def resolve_target(path):
    # datei gibt es noch nicht ODER ich darf ueberschreiben -> pfad passt
    if not path.exists() or ask_yes_no(f"'{path.name}' ueberschreiben?", default=False):
        return path
    # ansonsten haenge ich eine zahl an bis der name frei ist
    counter = 1
    while True:
        candidate = path.with_stem(f"{path.stem}_{counter}")  # z.b. Seite1_1.pdf
        if not candidate.exists():
            return candidate
        counter += 1   # name war belegt, naechste zahl probieren


# das ist das eigentliche programm, hier laeuft alles der reihe nach ab.
def main():
    # der ordner in dem dieses skript liegt, den biete ich als standard an
    here = Path(__file__).resolve().parent
    eingabe = ask("ordner mit den png-dateien", str(here))
    # expanduser macht aus ~ den home-ordner, resolve macht einen vollen pfad draus
    folder = Path(eingabe).expanduser().resolve()
    if not folder.is_dir():          # gibt es den ordner ueberhaupt?
        sys.exit(f"fehler: '{folder}' ist kein ordner.")

    # alle .png dateien im ordner suchen und "natuerlich" sortieren
    pngs = sorted(folder.glob("*.png"), key=natural_key)
    if not pngs:                     # liste leer -> nichts zu tun
        sys.exit(f"keine png-dateien in '{folder}' gefunden.")

    pngs = choose_order(pngs)        # nutzer die reihenfolge bestaetigen lassen

    # dpi bestimmt wie gross die pdf-seite physisch wird (nicht die qualitaet)
    dpi = ask("aufloesung (dpi) fuer die seitengroesse", "150")
    try:
        # get_fixed_dpi_layout_fun sorgt dafuer dass alle seiten die gleiche dpi haben
        layout = img2pdf.get_fixed_dpi_layout_fun((int(dpi), int(dpi)))
    except ValueError:
        # wenn jemand keinen sinnvollen zahlenwert eingibt nehme ich 150
        print("ungueltige dpi - verwende 150.")
        layout = img2pdf.get_fixed_dpi_layout_fun((150, 150))

    print("\nwandle pngs verlustfrei um ...")
    # fuer jedes png die quelle vorbereiten (pfad oder bytes)
    sources = [pdf_source(p) for p in pngs]

    single_pdfs = []   # hier merke ich mir die erzeugten einzel-pdfs
    # zip() laeuft ueber beide listen gleichzeitig (bild + passende quelle)
    for png, src in zip(pngs, sources):
        target = resolve_target(png.with_suffix(".pdf"))  # aus Seite1.png wird Seite1.pdf
        target.write_bytes(img2pdf.convert(src, layout_fun=layout))  # pdf schreiben
        single_pdfs.append(target)
        print(f"  {png.name} -> {target.name}")

    # jetzt die frage ob alles in eine einzige pdf soll
    if not ask_yes_no("\nseiten zu einer pdf zusammenfuegen?", default=True):
        print("\nfertig.")
        return   # wenn nein sind wir hier schon fertig

    name = ask("name der zusammengefuegten pdf", "zusammengefuegt.pdf")
    # falls der nutzer die endung vergisst, haenge ich .pdf selbst an
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    merged = resolve_target(folder / name)
    # img2pdf.convert mit der ganzen liste macht aus allen bildern eine pdf
    merged.write_bytes(img2pdf.convert(sources, layout_fun=layout))
    print(f"\ngespeichert: {merged}")

    # aufraeumen: auf wunsch die einzelnen pdfs wieder loeschen
    if ask_yes_no("die einzelnen pdfs jetzt loeschen?", default=False):
        for p in single_pdfs:
            p.unlink()   # unlink() loescht die datei
        print("einzel-pdfs geloescht.")

    print("\nfertig.")


# dieser block startet das programm nur wenn die datei direkt ausgefuehrt wird.
if __name__ == "__main__":
    try:
        main()
    # strg+c oder eingabe-ende (strg+d) sollen sauber beenden statt einen
    # haesslichen fehler-block (traceback) auszuspucken
    except (KeyboardInterrupt, EOFError):
        sys.exit("\nabgebrochen.")
