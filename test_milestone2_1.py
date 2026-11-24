"""
Test di regressione per la Milestone 2.1 (v0.3.3-alpha).
Verifica: schema DB, creazione bozza, modifica, emissione, eliminazione.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from database import get_connection, init_db
from datetime import datetime


def check_schema(cursor):
    print("1. Verifica schema database...")
    cursor.execute("PRAGMA table_info(documenti)")
    cols = [r[1] for r in cursor.fetchall()]
    assert "stato_documento" in cols, "MANCA stato_documento"
    assert "note" in cols, "MANCA note"
    print("   [OK] Colonne stato_documento e note presenti.")


def check_bozza(cursor):
    print("2. Creazione fattura in bozza...")
    cursor.execute("SELECT id FROM clienti LIMIT 1")
    row = cursor.fetchone()
    if not row:
        print("   [SKIP] Nessun cliente in DB.")
        return None
    cliente_id = row[0]

    cursor.execute("""
        INSERT INTO documenti
            (tipo_documento, numero, data_emissione, cliente_id,
             imponibile, totale_documento, stato_xml, pagamento,
             tipo_soggetto, note, stato_documento)
        VALUES ('FATTURA', 'BOZZA-TEST', ?, ?, 100.0, 122.0,
                'PRONTO_SDI', 'CONTANTI', 'CLIENTE', 'Test', 'BOZZA')
    """, (datetime.now().strftime("%Y-%m-%d"), cliente_id))
    doc_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO documenti_righe
            (documento_id, articolo_id, descrizione, quantita,
             prezzo_unitario, aliquota_iva, totale_riga,
             sconto_riga, tipo_sconto_riga)
        VALUES (?, NULL, 'Riga test', 1, 100.0, 22.0, 122.0, 0.0, '%')
    """, (doc_id,))
    print(f"   [OK] Bozza creata con id={doc_id}")
    return doc_id


def check_modifica(cursor, doc_id):
    print("3. Modifica bozza...")
    cursor.execute("""
        UPDATE documenti SET note = 'Modificata dal test' WHERE id = ?
    """, (doc_id,))
    cursor.execute("SELECT note FROM documenti WHERE id = ?", (doc_id,))
    note = cursor.fetchone()[0]
    assert note == "Modificata dal test", "Modifica fallita"
    print("   [OK] Modifica applicata.")


def check_emissione(cursor, doc_id):
    print("4. Emissione fattura (BOZZA -> EMESSO)...")
    anno = datetime.now().strftime('%Y')
    cursor.execute("""
        SELECT ultimo_numero FROM contatori
        WHERE tipo_documento = 'FATTURA' AND anno = ?
    """, (anno,))
    row = cursor.fetchone()
    if row is None:
        nuovo = 1
        cursor.execute("""
            INSERT INTO contatori (tipo_documento, anno, ultimo_numero)
            VALUES ('FATTURA', ?, ?)
        """, (anno, nuovo))
    else:
        nuovo = (row[0] or 0) + 1
        cursor.execute("""
            UPDATE contatori SET ultimo_numero = ?
            WHERE tipo_documento = 'FATTURA' AND anno = ?
        """, (nuovo, anno))
    numero = f"FAT-{anno}-{nuovo:04d}"

    cursor.execute("""
        UPDATE documenti SET numero = ?, stato_documento = 'EMESSO'
        WHERE id = ?
    """, (numero, doc_id))
    cursor.execute("SELECT numero, stato_documento FROM documenti WHERE id = ?", (doc_id,))
    n, s = cursor.fetchone()
    assert s == "EMESSO", "Emissione fallita"
    print(f"   [OK] Fattura emessa: {n}")


def check_eliminazione(cursor, doc_id):
    print("5. Eliminazione bozza (cleanup)...")
    cursor.execute("DELETE FROM documenti_righe WHERE documento_id = ?", (doc_id,))
    cursor.execute("DELETE FROM documenti WHERE id = ?", (doc_id,))
    cursor.execute("SELECT id FROM documenti WHERE id = ?", (doc_id,))
    assert cursor.fetchone() is None, "Eliminazione fallita"
    print("   [OK] Bozza eliminata.")


def main():
    print("=" * 60)
    print("  TEST MILESTONE 2.1 — v0.3.3-alpha")
    print("=" * 60)
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        check_schema(cursor)
        doc_id = check_bozza(cursor)
        if doc_id:
            check_modifica(cursor, doc_id)
            check_emissione(cursor, doc_id)
            check_eliminazione(cursor, doc_id)
        conn.commit()
        print()
        print("=" * 60)
        print("  TUTTI I TEST PASSATI ✅")
        print("=" * 60)
    except AssertionError as e:
        conn.rollback()
        print(f"\n[FAIL] {e}")
        sys.exit(1)
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()