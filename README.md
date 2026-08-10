# Immich Album Manager

Der **Immich Album Manager** verwaltet Immich-Alben anhand einer konfigurierbaren Ordnerstruktur.

Das Programm durchsucht definierte Verzeichnisse, erkennt daraus Alben und synchronisiert diese mit einem Immich-Server.

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
- Synchronisationsberichte als HTML und TXT
- Anzeige der letzten Synchronisationsberichte
- Manuelles Löschen älterer Berichte
- Weboberflaeche zur Konfiguration und Kontrolle

## Voraussetzungen

- Docker
- Immich mit aktivierter API
- Immich API Key
- Zugriff des Containers auf die zu scannenden Foto- und Videoverzeichnisse

## Konfiguration

Die Konfiguration wird innerhalb des Containers unter

    /config

gespeichert.

Dort befinden sich unter anderem:

    /config/config.json
    /config/album_rules.json
    /config/asset_cache.json
    /config/reports/

## Ordnerregeln

Es koennen mehrere Album-Wurzeln definiert werden.

Beispiel:

    Fotos/Reisen

mit dem Modus:

    children

Dabei koennen die Unterordner als Alben verwendet werden.

Alternativ koennen Jahresstrukturen verwendet werden:

    Fotos
    +-- 2022
    +-- 2023
    +-- 2024
    +-- 2025

## Album-Regeln

Fuer einzelne Alben kann festgelegt werden, ob neue Assets automatisch ergaenzt werden.

Standardmaessig gilt:

    {
      "auto_add": true,
      "allow_delete": false,
      "allow_rename": true
    }

Die Regeln werden in

    /config/album_rules.json

gespeichert.

### Auto Add

Wenn `auto_add` auf `true` gesetzt ist, werden neue Assets, die beim Scan im zugehoerigen Ordner gefunden werden, bei der Synchronisation automatisch zum Album hinzugefuegt.

Wenn `auto_add` auf `false` gesetzt ist, wird das Album weiterhin erkannt und angezeigt, aber neue Assets werden bei der Synchronisation nicht automatisch hinzugefuegt.

Dies ist besonders nuetzlich fuer Alben, deren Inhalt bewusst manuell kontrolliert werden soll.

## Asset-Cache

Der Asset-Cache enthaelt die Zuordnung zwischen Dateipfad und Immich Asset-ID.

Dadurch muss beim Scannen nicht jedes Asset erneut ueber die Immich API gesucht werden.

Der Cache kann ueber die Weboberflaeche manuell neu aufgebaut werden.

Beim normalen Synchronisationsvorgang wird der Cache ebenfalls aktualisiert.

## Synchronisation

Der normale Ablauf ist:

1. Konfiguration pruefen
2. Asset-Cache aktualisieren
3. Ordner scannen
4. Alben mit Immich vergleichen
5. Fehlende Alben anlegen
6. Fehlende Assets ergaenzen
7. Synchronisationsbericht erzeugen

Beim Hinzufuegen von Assets werden nur bestehende Immich-Assets referenziert.

Die Dateien selbst werden nicht erneut importiert.

## Synchronisationsberichte

Nach jeder Synchronisation werden HTML- und TXT-Berichte erzeugt.

Die Berichte befinden sich unter:

    /config/reports/

Der jeweils letzte Bericht wird zusaetzlich als

    last_sync_report.html
    last_sync_report.txt

bereitgestellt.

Die Weboberflaeche bietet Zugriff auf:

- den letzten Synchronisationsbericht
- die letzten gespeicherten Berichte
- die manuelle Bereinigung alter Berichte

Alte Berichte werden nicht automatisch geloescht.

Das Loeschen kann bewusst ueber die Weboberflaeche ausgeloest werden.

## Weboberflaeche

Die Anwendung laeuft standardmaessig auf Port:

    5050

Nach dem Start ist die Weboberflaeche beispielsweise erreichbar unter:

    http://<server-ip>:5050

Die Weboberflaeche bietet unter anderem:

- Konfiguration des Immich-Servers
- Verwaltung der Album-Wurzeln
- Auswahl der Ordnerstruktur
- Scan der Ordner
- Anzeige der erkannten Alben
- Verwaltung der Album-Regeln
- Aufbau des Asset-Caches
- Synchronisation
- Anzeige der Synchronisationsberichte
- Informationen zur Anwendung

## Sicherheit

Der Immich API Key wird fuer die Kommunikation mit dem Immich Server benoetigt.

Die Konfigurationsdateien sollten daher nicht oeffentlich zugaenglich gemacht werden.

Insbesondere sollte die Datei

    /config/config.json

nicht in ein oeffentliches Git-Repository uebernommen werden, wenn sie einen echten Immich API Key enthaelt.

## Datenintegritaet

Der Immich Album Manager veraendert keine Originaldateien.

Beim Hinzufuegen von Assets zu einem Album werden ausschliesslich Referenzen innerhalb von Immich verwendet.

Die Originaldateien werden weder kopiert noch erneut importiert.

## System- und Ausschlussordner

Bestimmte Systemordner werden beim Scan automatisch ignoriert.

Dazu gehoeren unter anderem:

    .@__thumb
    @Recycle
    #recycle
    .Trash
    .Trashes
    .DS_Store
    Thumbs.db
    iPod Photo Cache
    lost+found

Darueber hinaus werden standardmaessig bestimmte Ordner ausgeschlossen:

    Import
    Other
    Scan
    Unknown Year Taken

## Projektstruktur

Die wichtigsten Komponenten des Projekts sind:

    app.py
        Flask-Webanwendung und HTTP-Routen

    scanner.py
        Durchsuchen der konfigurierten Ordner

    immich_api.py
        Kommunikation mit der Immich API

    album_sync.py
        Vergleich und Synchronisation der Alben

    album_rules.py
        Verwaltung der Album-Regeln

    asset_cache.py
        Verwaltung des Asset-Caches

    sync_report.py
        Erzeugung der Synchronisationsberichte

    rules.py
        Erkennung von System-, Jahres- und Tagesordnern

    templates/
        HTML-Vorlagen der Weboberflaeche

    static/
        CSS und statische Dateien

## Installation

Die Anwendung ist fuer den Betrieb innerhalb eines Docker-Containers vorgesehen.

Das Repository kann beispielsweise mit Git geklont werden:

    git clone https://github.com/gkutyi/immich-album-manager.git

Danach kann das Projekt entsprechend der vorhandenen Docker-Konfiguration gestartet werden.

Die konkrete Container-Konfiguration haengt von der jeweiligen Umgebung und der verwendeten Ordnerstruktur ab.

## Version

Aktuelle Version:

**1.0.0**

Version 1.0.0 ist die erste stabile Version des Immich Album Managers.

## Ausblick

Die Version 1.0.0 bildet die stabile Grundlage fuer die weitere Entwicklung.

Fuer eine zukuenftige Version 2.x ist insbesondere eine Erweiterung des Regelwerks vorgesehen.

Geplant sind unter anderem differenziertere Regeln fuer die automatische Synchronisation und eine flexiblere Definition der Albumstruktur.

## Lizenz

Dieses Projekt wird derzeit ohne ausdrueckliche Open-Source-Lizenz veroeffentlicht.

Eine geeignete Lizenz kann zu einem spaeteren Zeitpunkt festgelegt werden.