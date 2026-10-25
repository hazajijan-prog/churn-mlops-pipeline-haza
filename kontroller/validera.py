import pandas as pd
import pandera.pandas as pa

from kontroller.schema import SCHEMA


def main(fil: str) -> int:
    df = pd.read_csv(fil)

    try:
        SCHEMA.validate(df, lazy=True)

    except pa.errors.SchemaErrors as e:
        print(f"STOPP: {fil} klarar inte schemat")
        ovantade = [namn for namn in df.columns if namn not in SCHEMA.columns]
        saknade = [
            namn for namn, kolumn in SCHEMA.columns.items()
            if kolumn.required and namn not in df.columns
        ]
        if ovantade:
            print(f"Oväntade kolumner: {', '.join(ovantade)}.")
            print("Åtgärd: Ta bort oväntade kolumner eller stäm av schemaändringen.")
        if saknade:
            print(f"Obligatoriska kolumner saknas: {', '.join(saknade)}.")
            print("Åtgärd: Återställ kolumnerna med rätt namn och innehåll.")
        print(e.failure_cases)
        return 1

    print(f"OK: {fil} ({len(df)} rader)")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv[1]))
