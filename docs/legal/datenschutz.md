# Datenschutzerklärung / Privacy policy

Stand: 21. September 2026

*English summary: ErklaerBaer publishes short science videos for children on YouTube. The
project runs no website, no accounts, no tracking and no analytics, and it does not collect
personal data about viewers. Its only Google access is to the owner's own YouTube channel,
to upload videos. The details below list every tool that touches the project's content.*

## 1. Wer ist verantwortlich?

ErklaerBaer ist ein privates, nicht kommerzielles Projekt von **Andreas Doepfert** (Schweiz).
Kontakt: über die [GitHub-Issues des Projekts](https://github.com/Mapgax/ErklaerBaer/issues).
Es gilt das Schweizer Datenschutzgesetz (DSG); soweit anwendbar, die DSGVO.

## 2. Was ErklaerBaer ist und was es nicht tut

ErklaerBaer stellt kurze Erklärvideos zu Naturwissenschaften für Kinder von etwa fünf bis
neun Jahren auf Deutsch und Niederländisch her. Die Videos erscheinen auf einem
YouTube-Kanal und sind als «für Kinder gemacht» gekennzeichnet.

Das Projekt

- betreibt **keine eigene Website, keine Benutzerkonten, keine Kommentar- oder
  Anmeldefunktion** und setzt **keine Cookies**;
- verwendet **keine Werbung, kein Tracking und keine Analysewerkzeuge**;
- **erhebt, speichert und verkauft keine personenbezogenen Daten** von Zuschauerinnen und
  Zuschauern und gibt keine solchen Daten weiter;
- richtet sich mit seinen Videos an Kinder, sammelt aber keinerlei Angaben von Kindern.

## 3. YouTube

Die Videos werden über YouTube (Google LLC / Google Ireland Limited) ausgeliefert. Beim
Ansehen verarbeitet YouTube Daten nach der
[Datenschutzerklärung von Google](https://policies.google.com/privacy). Darauf hat das
Projekt keinen Einfluss. Das Projekt erhält von YouTube nur die üblichen, zusammengefassten
Kanalstatistiken (zum Beispiel Aufrufe), die YouTube dem Kanalbetreiber anzeigt. Die
Videos sind für Kinder gekennzeichnet; YouTube schränkt dafür personalisierte Werbung und
Kommentare selbst ein.

Für das Hochladen nutzt das Projekt die **YouTube Data API** mit einer OAuth-Anmeldung des
Kanalbetreibers. Diese Anwendung greift **ausschliesslich auf den eigenen Kanal des
Betreibers** zu: Videos, Untertitel, Vorschaubilder und Wiedergabelisten hochladen und
verwalten. Sie liest oder speichert keine Daten anderer Nutzerinnen und Nutzer. Das
Zugriffstoken liegt nur lokal auf dem Rechner des Betreibers und wird nicht weitergegeben.
Die Nutzung von Informationen aus Google-APIs folgt der
[Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy),
einschliesslich der Anforderungen zur eingeschränkten Nutzung.

## 4. Werkzeuge und Dienste, die Inhalte des Projekts verarbeiten

Die Videos werden mit Hilfe von KI-Diensten hergestellt. An diese Dienste gehen
**ausschliesslich Texte und Bildaufträge über Wissenschaftsthemen**, keine personenbezogenen
Daten. Jeder Dienst hat eigene Bedingungen.

| Dienst | Wofür | Was wird gesendet |
|---|---|---|
| **Anthropic (Claude)** | Prüfung der Erklärtexte auf wissenschaftliche Richtigkeit; Unterstützung beim Schreiben der Programme und Skripte | Themenfelder (Titel, Kategorie, Fakt, beobachtetes Ergebnis, Erklärung), Videotext und Quellenangaben |
| **Google Cloud Text-to-Speech / Gemini** | Erzeugung der Sprecherstimme (synthetische Stimme, «Chirp 3 HD» und Gemini-Sprachmodelle) | Der Sprechtext der Videos |
| **Black Forest Labs (FLUX)** | Erzeugung von Bildmaterial und kurzen Bewegungsclips für den Bären und einzelne Gegenstände | Bildbeschreibungen und Referenzbilder des Projekts |
| **Rive** | Lokale Animation der Bärenfigur (Werkzeug auf dem Rechner des Betreibers) | keine Übermittlung von Zuschauerdaten |
| **YouTube Data API (Google)** | Hochladen und Verwalten der Videos auf dem eigenen Kanal | Videodatei, Titel, Beschreibung, Untertitel, Vorschaubild |
| **GitHub** | Öffentliche Ablage des Quellcodes und dieser Texte | Quellcode und Dokumentation; GitHub verarbeitet Zugriffe nach [seiner Datenschutzerklärung](https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement) |
| **MINT-Bot (eigene Themensammlung)** | Quelle der Themenvorschläge und Versuchsbeschreibungen | wird nur gelesen |

Die Bilder und die Stimme in den Videos sind KI-erzeugt; das steht in jeder
Videobeschreibung. Es werden **keine echten Personen, Stimmen oder Ereignisse** abgebildet
oder nachgeahmt.

## 5. Quellen der Inhalte

Die Erklärungen stützen sich auf frei zugängliche Fachquellen, zum Beispiel OpenStax
(Lehrbücher, CC BY), das US Geological Survey (USGS), Fachlexika und Museumsseiten. Die
verwendeten Quellen eines Videos sind im Ordner
[`docs/evidence`](https://github.com/Mapgax/ErklaerBaer/tree/main/docs/evidence) des Projekts
aufgeführt. Schrift auf dem Bildschirm: *Berner Basisschrift 1* mit ihrem beiliegenden
Lizenzhinweis.

## 6. Kinder

Die Videos sind für Kinder gemacht. Das Projekt spricht Kinder nicht direkt an, um Daten
zu erhalten, und bietet ihnen keine Möglichkeit, Daten zu übermitteln. Eltern und
Lehrpersonen sollten Kinder beim Ansehen von YouTube begleiten.

## 7. Ihre Rechte

Da das Projekt keine personenbezogenen Daten über Zuschauende führt, gibt es nichts, worüber
Auskunft erteilt oder was berichtigt oder gelöscht werden könnte. Für Fragen oder wenn Sie Daten in einem
Beitrag des Projekts entdecken, die dort nicht hingehören, schreiben Sie bitte an die
GitHub-Issues (siehe oben). Rechte gegenüber YouTube, Google und GitHub machen Sie bei
diesen Diensten geltend.

## 8. Änderungen

Diese Erklärung wird angepasst, wenn sich Werkzeuge oder Dienste ändern. Die jeweils
gültige Fassung steht immer auf dieser Seite; die Änderungen sind in der Git-Historie des
Projekts nachvollziehbar.
