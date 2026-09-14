# Immich Album Manager

Der **Immich Album Manager** verwaltet Immich-Alben anhand einer konfigurierbaren Ordnerstruktur.

Das Programm durchsucht definierte Verzeichnisse, erkennt daraus Alben und synchronisiert diese mit einem Immich-Server.

Der Album Manager arbeitet dabei mit bereits in Immich vorhandenen Assets. Die Mediendateien selbst werden bei der Albumsynchronisation nicht erneut nach Immich hochgeladen.

## Funktionen

- Verbindung zu einem Immich-Server über die Immich API
- Scannen definierter Ordnerstrukturen
- Unterstützung verschiedener Album-Strukturen
- Erkennen von Jahresordnern
- Erkennen von Qfiling-Tagesordnern
- Ausschluss von System- und bestimmten Ordnern
- Asset-Cache zur schnellen Zuordnung von Dateien zu Immich-Assets
- Erstellen fehlender Alben
- Ergänzen fehlender Assets in bestehenden Alben
- Konfigurierbare Album-Regeln
- Aktivieren oder Deaktivieren der automatischen Ergänzung einzelner Alben
- Erkennung von Live-Photo-Motion-Assets
- Import-Funktion für den angebundenen Family Photo Importer
- Import-Reports
- Import-Logs
- Synchronisationsberichte als HTML und TXT
- Anzeige der letzten Synchronisations- und Importberichte
- Manuelles Löschen älterer Berichte und Logs
- Weboberfläche zur Konfiguration und Kontrolle

## Voraussetzungen

- Docker
- Immich mit aktivierter API
- Immich API Key
- Zugriff des Containers auf die zu scannenden Foto- und Videoverzeichnisse
- Für die Import-Funktion: vorhandener Family Photo Importer

## Konfiguration

Die Konfiguration wird innerhalb des Containers unter

    /config

gespeichert.

Die wichtigsten Dateien und Verzeichnisse sind:

    /config/settings.json
    /config/album_rules.json
    /config/asset_index.json
    /config/reports/
    /config/import_reports/

### settings.json

Die Datei `settings.json` enthält unter anderem:

- Immich-Server-URL
- Immich API Key
- Album-Wurzeln
- Scan-Modus
- Cache-Einstellungen

Diese Datei enthält sensible Zugangsdaten und darf nicht in ein öffentliches Git-Repository übernommen werden.

Eine lokale Konfigurationsdatei wird deshalb durch `.gitignore` vom Repository ausgeschlossen.

## Ordnerregeln

Es können mehrere Album-Wurzeln definiert werden.

Beispiel:

    Fotos/Reisen

mit dem Modus:

    children

Dabei können die Unterordner als Alben verwendet werden.

Alternativ können Jahresstrukturen verwendet werden:

    Fotos
    +-- 2022
    +-- 2023
    +-- 2024
    +-- 2025

Der Scanner unterstützt außerdem erkannte Qfiling-Tagesordner.

## Album-Regeln

Für einzelne Alben kann festgelegt werden, ob neue Assets automatisch ergänzt werden.

Der Standard ist bewusst konservativ:

    {
      "auto_add": false,
      "allow_delete": false,
      "allow_rename": true
    }

Die Regeln werden in

    /config/album_rules.json

gespeichert.

### Auto Add

Wenn `auto_add` auf `true` gesetzt ist, werden neue Assets, die beim Scan im zugehörigen Ordner gefunden werden, bei der Synchronisation automatisch zum bestehenden Album hinzugefügt.

Wenn `auto_add` auf `false` gesetzt ist, wird das Album weiterhin erkannt und angezeigt. Neue Assets werden jedoch nicht automatisch zum Album hinzugefügt.

Die Einstellung kann für jedes Album über die Weboberfläche geändert werden.

Der Standardwert `false` verhindert, dass neue Dateien automatisch in bestehende Alben übernommen werden.

### Weitere Album-Regeln

Die Eigenschaften

    allow_delete
    allow_rename

sind im Regelmodell bereits vorgesehen.

Sie werden in der aktuellen Version jedoch noch nicht aktiv für die Synchronisation verwendet und dienen als Vorbereitung für zukünftige Funktionen.

## Asset-Cache

Der Asset-Cache enthält die Zuordnung zwischen Dateipfad und Immich Asset-ID.

Die Cache-Datei lautet:

    /config/asset_index.json

Dadurch muss beim Scannen nicht jedes Asset erneut über die Immich API gesucht werden.

Der Cache kann über die Weboberfläche manuell neu aufgebaut werden.

Beim normalen Synchronisationsvorgang wird der Cache entsprechend der Anwendung aktualisiert.

## Live Photos

Immich verwaltet bei Live Photos das Foto und den zugehörigen Motion-Anteil als separate Assets.

Der Motion-Anteil kann in Immich als verstecktes (`hidden`) Video-Asset geführt werden.

Bei der Ermittlung fehlender Assets berücksichtigt der Album Manager diese versteckten Live-Photo-Motion-Assets.

Dadurch werden Motion-Video-Assets eines bereits vorhandenen Live Photos nicht fälschlicherweise bei jeder Synchronisation als fehlende Assets gemeldet.

Die Live-Photo-Motion-Assets werden beim Erstellen eines neuen Albums weiterhin zusammen mit den vorhandenen Asset-IDs an Immich übergeben.

## Synchronisation

Der normale Ablauf ist:

1. Konfiguration prüfen
2. Asset-Cache verwenden bzw. aktualisieren
3. Ordner scannen
4. Alben mit Immich vergleichen
5. Fehlende Alben erkennen
6. Fehlende Alben bei entsprechender Regel anlegen
7. Fehlende Assets bestehender Alben ermitteln
8. Live-Photo-Motion-Assets bei der Differenzprüfung berücksichtigen
9. Fehlende Assets entsprechend der `auto_add`-Regel ergänzen
10. Synchronisationsbericht erzeugen

Beim Hinzufügen von Assets werden nur bestehende Immich-Assets referenziert.

Die Dateien selbst werden dabei nicht erneut importiert.

## Import

Der Album Manager kann den angebundenen Family Photo Importer über die Weboberfläche ausführen.

Die Import-Funktion kann:

- einen Import starten
- den Importstatus anzeigen
- Import-Reports anzeigen
- frühere Import-Reports anzeigen
- Import-Logs anzeigen
- ältere Import-Reports und Logs bereinigen

Die Importdaten werden getrennt von den Synchronisationsberichten gespeichert.

Import-Reports befinden sich unter:

    /config/import_reports/

## Synchronisationsberichte

Nach einer Synchronisation werden HTML- und TXT-Berichte erzeugt.

Die Berichte befinden sich unter:

    /config/reports/

Der jeweils letzte Bericht wird zusätzlich als

    last_sync_report.html
    last_sync_report.txt

bereitgestellt.

Die Weboberfläche bietet Zugriff auf:

- den letzten Synchronisationsbericht
- die letzten gespeicherten Berichte
- die manuelle Bereinigung alter Berichte

Alte Berichte werden nicht automatisch gelöscht.

Das Löschen kann bewusst über die Weboberfläche ausgelöst werden.

## Import-Berichte und Logs

Import-Berichte werden unter

    /config/import_reports/

gespeichert.

Zusätzlich können Import-Logs über die Weboberfläche angezeigt und bereinigt werden.

Import- und Synchronisationsberichte werden getrennt voneinander verwaltet.

## Weboberfläche

Die Anwendung läuft im Container standardmäßig auf Port:

    5050

Nach dem Start ist die Weboberfläche beispielsweise erreichbar unter:

    http://<server-ip>:5050

Die Weboberfläche bietet unter anderem:

- Konfiguration des Immich-Servers
- Verwaltung der Album-Wurzeln
- Auswahl der Ordnerstruktur
- Scan der Ordner
- Anzeige der erkannten Alben
- Verwaltung der Album-Regeln
- Aktivieren und Deaktivieren von `auto_add`
- Aufbau des Asset-Caches
- Synchronisation
- Anzeige der Synchronisationsberichte
- Start des Family Photo Importers
- Anzeige von Import-Reports
- Anzeige von Import-Logs
- Bereinigung älterer Reports und Logs
- Informationen zur Anwendung

## Docker

Die Anwendung ist für den Betrieb innerhalb eines Docker-Containers vorgesehen.

Das Repository kann beispielsweise mit Git geklont werden:

    git clone https://github.com/gkutyi/immich-album-manager.git

Anschließend kann die Anwendung entsprechend der vorhandenen Docker-Konfiguration gestartet werden.

Die konkrete Container- und Volume-Konfiguration hängt von der jeweiligen Umgebung und Ordnerstruktur ab.

## Sicherheit

Der Immich API Key wird für die Kommunikation mit dem Immich Server benötigt.

Konfigurationsdateien mit Zugangsdaten dürfen nicht öffentlich zugänglich gemacht werden.

Insbesondere sollte

    /config/settings.json

nicht in ein öffentliches Git-Repository übernommen werden.

Auch Runtime-Daten wie

    /config/album_rules.json
    /config/asset_index.json
    /config/reports/
    /config/import_reports/
    /logs/

werden nicht versioniert.

## Version

Aktuelle Version:

**1.2.0**

### Version 1.2.0

Die Version 1.2.0 erweitert den Immich Album Manager unter anderem um:

- Import-Funktion und Import-Reports
- Import-Logs
- verbesserte Weboberfläche
- Live-Photo-Motion-Erkennung
- korrigierte Behandlung versteckter Live-Photo-Video-Assets
- `auto_add` mit dem sicheren Standardwert `false`
- überarbeitete Docker-Konfiguration
- Bereinigung von Runtime- und Konfigurationsdateien aus dem Git-Repository

## Lizenz

Dieses Projekt wird derzeit ohne ausdrückliche Open-Source-Lizenz veröffentlicht.

Eine geeignete Lizenz kann zu einem späteren Zeitpunkt festgelegt werden.
